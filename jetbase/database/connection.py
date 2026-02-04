import logging
import os
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache
from typing import AsyncGenerator, Generator

from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from jetbase.config import get_config
from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType


@lru_cache(maxsize=1)
def _get_engine(url: str) -> Engine:
    return create_engine(url=url)


def is_async_enabled() -> bool:
    """
    Check if async mode is enabled.

    Only checks the ASYNC environment variable:
    - "true", "1", "yes" -> async mode
    - "false", "0", "no", or not set -> sync mode

    Returns:
        bool: True if async mode is enabled, False otherwise.
    """
    async_env = os.getenv("ASYNC", "").lower()
    return async_env in ("true", "1", "yes")


def _make_sync_url(url: str) -> str:
    """Convert an async URL to sync by removing async driver suffixes."""
    url = url.replace("+asyncpg", "")
    url = url.replace("+async", "")
    url = url.replace("+aiosqlite", "")
    return url


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager that yields a database connection with a transaction.

    Always works in sync mode. If ASYNC=true, strips the async driver suffix
    from the URL to allow sync connections.

    Example:
        >>> with get_db_connection() as conn:
        ...     conn.execute(query)
    """
    config = get_config(required={"sqlalchemy_url"})
    url = config.sqlalchemy_url

    if is_async_enabled():
        url = _make_sync_url(url)

    engine: Engine = create_engine(url=url)
    db_type = detect_db(sqlalchemy_url=str(engine.url))

    if db_type == DatabaseType.DATABRICKS:
        with _suppress_databricks_warnings():
            with engine.begin() as connection:
                yield connection
    else:
        with engine.begin() as connection:
            if db_type == DatabaseType.POSTGRESQL:
                postgres_schema = config.postgres_schema
                if postgres_schema:
                    connection.execute(
                        text("SET search_path TO :postgres_schema"),
                        parameters={"postgres_schema": postgres_schema},
                    )
            yield connection


@asynccontextmanager
async def get_async_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Context manager that yields an async database connection with a transaction.

    Only works when ASYNC=true. Raises RuntimeError otherwise.

    Example:
        >>> async with get_async_db_connection() as conn:
        ...     await conn.execute(query)
    """
    if not is_async_enabled():
        raise RuntimeError(
            "ASYNC=false but using get_async_db_connection(). "
            "Set ASYNC=true to use async mode, or use get_db_connection() for sync mode."
        )

    config = get_config(required={"sqlalchemy_url"})
    async_engine: AsyncEngine = create_async_engine(url=config.sqlalchemy_url)

    async with async_engine.begin() as connection:
        db_type = detect_db(sqlalchemy_url=str(async_engine.url))
        if db_type == DatabaseType.POSTGRESQL:
            postgres_schema = config.postgres_schema
            if postgres_schema:
                await connection.execute(
                    text("SET search_path TO :postgres_schema"),
                    parameters={"postgres_schema": postgres_schema},
                )
        yield connection


class _ConnectionWrapper:
    """
    Context manager wrapper that provides both sync and async protocols.

    Usage:
        ASYNC=true:   async with get_connection() as conn:
        ASYNC=false:  with get_connection() as conn:
    """

    def __enter__(self):
        self._sync_cm = get_db_connection()
        return self._sync_cm.__enter__()

    def __exit__(self, *args):
        return self._sync_cm.__exit__(*args)

    async def __aenter__(self):
        self._async_cm = get_async_db_connection()
        return await self._async_cm.__aenter__()

    async def __aexit__(self, *args):
        return await self._async_cm.__aexit__(*args)


def get_connection() -> "_ConnectionWrapper":
    """
    Context manager that works with both sync and async based on ASYNC env var.

    Usage:
        ASYNC=true:   async with get_connection() as conn:
        ASYNC=false:  with get_connection() as conn:

    Returns:
        _ConnectionWrapper: A wrapper that supports both sync and async context managers.
    """
    return _ConnectionWrapper()


@contextmanager
def _suppress_databricks_warnings():
    logger = logging.getLogger("databricks")
    original_level = logger.level
    logger.setLevel(logging.ERROR)

    try:
        yield
    finally:
        logger.setLevel(original_level)
