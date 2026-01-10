from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.engine import make_url, URL

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
    sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    db_type: DatabaseType = detect_db(sqlalchemy_url=sqlalchemy_url)

    connect_args: dict[str, Any] = {}

    if db_type == DatabaseType.SNOWFLAKE:
        snowflake_url: URL = make_url(sqlalchemy_url)

        if not snowflake_url.password:
            connect_args["private_key"] = _get_snowflake_private_key_der()

    engine: Engine = create_engine(url=sqlalchemy_url, connect_args=connect_args)

    with engine.begin() as connection:
        if db_type == DatabaseType.POSTGRESQL:
            postgres_schema: str | None = get_config().postgres_schema
            if postgres_schema:
                connection.execute(
                    text("SET search_path TO :postgres_schema"),
                    parameters={"postgres_schema": postgres_schema},
                )
        yield connection


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
    from cryptography.hazmat.primitives import serialization  # type: ignore[missing-import]
    from cryptography.hazmat.backends import default_backend  # type: ignore[missing-import]
    from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes  # type: ignore[missing-import]

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
