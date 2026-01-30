import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Any, Generator

from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import URL, make_url

from jetbase.config import get_config
from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager that yields a database connection with a transaction.

    Creates a database connection using the configured SQLAlchemy URL,
    opens a transaction, and yields the connection. For PostgreSQL,
    sets the search_path if a schema is configured.

    Yields:
        Connection: A SQLAlchemy Connection object within an active
            transaction.

    Example:
        >>> with get_db_connection() as conn:
        ...     conn.execute(query)
    """

    engine: Engine = _get_engine()
    db_type: DatabaseType = detect_db(sqlalchemy_url=str(engine.url))

    if db_type == DatabaseType.DATABRICKS:
        # Suppress databricks warnings during connection
        with _suppress_databricks_warnings():
            with engine.begin() as connection:
                yield connection
    else:
        with engine.begin() as connection:
            if db_type == DatabaseType.POSTGRESQL:
                postgres_schema: str | None = get_config().postgres_schema
                if postgres_schema:
                    connection.execute(
                        text("SET search_path TO :postgres_schema"),
                        parameters={"postgres_schema": postgres_schema},
                    )
            yield connection


@lru_cache(maxsize=1)
def _get_engine() -> Engine:
    """
    Get or create the singleton SQLAlchemy Engine.

    Creates the engine on first call and caches it for subsequent calls.
    The engine manages its own connection pool internally.

    Returns:
        Engine: A SQLAlchemy Engine instance.
    """
    sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    db_type: DatabaseType = detect_db(sqlalchemy_url=sqlalchemy_url)

    connect_args: dict[str, Any] = {}

    if db_type == DatabaseType.SNOWFLAKE:
        snowflake_url: URL = make_url(sqlalchemy_url)

        if not snowflake_url.password:
            connect_args["private_key"] = _get_snowflake_private_key_der()

    return create_engine(url=sqlalchemy_url, connect_args=connect_args)


def _get_snowflake_private_key_der() -> bytes:
    """
    Retrieves the Snowflake private key in DER format for key pair authentication.

    Loads the private key from configuration (PEM format), optionally decrypts it with a password,
    and returns the key encoded as DER bytes, suitable for use with Snowflake's SQLAlchemy driver.

    Returns:
        bytes | None: The DER-encoded private key bytes, or None if not set.

    Raises:
        ValueError: If neither Snowflake private key nor password are set in configuration.
    """
    # Lazy import - only needed for Snowflake key pair auth
    from cryptography.hazmat.backends import (
        default_backend,  # type: ignore[missing-import]
    )
    from cryptography.hazmat.primitives import (
        serialization,  # type: ignore[missing-import]
    )
    from cryptography.hazmat.primitives.asymmetric.types import (
        PrivateKeyTypes,  # type: ignore[missing-import]
    )

    snowflake_private_key: str | None = get_config().snowflake_private_key

    if not snowflake_private_key:
        raise ValueError(
            "Snowflake private key is not set. "
            "You can set it as 'JETBASE_SNOWFLAKE_PRIVATE_KEY' in an environment variable. "
            "Alternatively, you can add the password to the SQLAlchemy URL."
        )

    password_str: str | None = get_config().snowflake_private_key_password
    password: bytes | None = password_str.encode("utf-8") if password_str else None

    private_key: PrivateKeyTypes = serialization.load_pem_private_key(
        snowflake_private_key.encode("utf-8"),
        password=password,
        backend=default_backend(),
    )

    private_key_bytes: bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return private_key_bytes


@contextmanager
def _suppress_databricks_warnings():
    """
    Temporarily sets the databricks logger to ERROR level to suppress
    the deprecated _user_agent_entry warning coming from the databricks-sqlalchemy dependency.

    Databricks-sqlalchemy is a dependency of databricks-sql-connector (which is triggering the warning), so we need to suppress the warning here until databricks-sqlalchemy is updated to fix the warning.
    """
    logger = logging.getLogger("databricks")
    original_level = logger.level
    logger.setLevel(logging.ERROR)

    try:
        yield
    finally:
        logger.setLevel(original_level)
