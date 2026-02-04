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


def is_async_url(sqlalchemy_url: str) -> bool:
    """
    Check if the SQLAlchemy URL uses an async driver.
    """
    return (
        "+asyncpg" in sqlalchemy_url
        or "+aiosqlite" in sqlalchemy_url
        or "+async" in sqlalchemy_url
    )


def is_async_enabled() -> bool:
    """
    Check if async mode is enabled via ASYNC environment variable.
    """
    return os.getenv("ASYNC", "").lower() in ("true", "1", "yes")


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager that yields a database connection with a transaction.

    For async databases, use get_async_db_connection() instead.

    Raises:
        RuntimeError: If ASYNC=true.

    Example:
        >>> with get_db_connection() as conn:
        ...     conn.execute(query)
    """
    if is_async_enabled():
        raise RuntimeError(
            "ASYNC=true but using get_db_connection(). "
            "Use 'async with get_async_db_connection()' for async mode."
        )

    config = get_config(required={"sqlalchemy_url"})
    url = config.sqlalchemy_url

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


def _make_sync_url(url: str) -> str:
    """
    Convert an async URL to sync by removing async driver suffixes.
    """
    url = url.replace("+asyncpg", "")
    url = url.replace("+async", "")
    url = url.replace("+aiosqlite", "")
    return url


@asynccontextmanager
async def get_async_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    Context manager that yields an async database connection with a transaction.

    Raises:
        RuntimeError: If ASYNC=false.

    Example:
        >>> async with get_async_db_connection() as conn:
        ...     await conn.execute(query)
    """
    if not is_async_enabled():
        raise RuntimeError(
            "ASYNC=false but using get_async_db_connection(). "
            "Use 'with get_db_connection()' for sync mode, "
            "or set ASYNC=true."
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
    Wrapper that provides both sync and async context manager protocols.

    Usage:
        ASYNC=false:  with get_connection() as conn:
        ASYNC=true:   async with get_connection() as conn:
    """

    def __enter__(self):
        if is_async_enabled():
            raise RuntimeError(
                "ASYNC=true but using 'with' instead of 'async with'.\n"
                "Use 'async with get_connection() as conn:' for async mode."
            )
        cm = get_db_connection()
        self._sync_cm = cm
        return cm.__enter__()

    def __exit__(self, *args):
        return self._sync_cm.__exit__(*args)

    async def __aenter__(self):
        if not is_async_enabled():
            raise RuntimeError(
                "ASYNC=false but using 'async with'.\n"
                "Use 'with get_connection() as conn:' for sync mode."
            )
        cm = get_async_db_connection()
        self._async_cm = cm
        return await cm.__aenter__()

    async def __aexit__(self, *args):
        return await self._async_cm.__aexit__(*args)


def get_connection() -> "_ConnectionWrapper":
    """
    Context manager that works with both sync and async based on ASYNC env var.

    Usage:
        ASYNC=false:  with get_connection() as conn:
        ASYNC=true:   async with get_connection() as conn:

    Returns:
        _ConnectionWrapper: A wrapper that supports both sync and async context manager protocols.
    """
    return _ConnectionWrapper()


@contextmanager
def _suppress_databricks_warnings():
    """
    Temporarily sets the databricks logger to ERROR level to suppress warnings.
    """
    logger = logging.getLogger("databricks")
    original_level = logger.level
    logger.setLevel(logging.ERROR)

    try:
        yield
    finally:
        logger.setLevel(original_level)
