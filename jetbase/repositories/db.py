from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Connection, Engine, create_engine, text

from jetbase.config import get_config
from jetbase.enums import DatabaseType
from jetbase.queries.base import detect_db


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
    engine: Engine = create_engine(url=sqlalchemy_url)
    db_type: DatabaseType = detect_db(sqlalchemy_url=sqlalchemy_url)

    with engine.begin() as connection:
        if db_type == DatabaseType.POSTGRESQL:
            postgres_schema: str | None = get_config().postgres_schema
            if postgres_schema:
                connection.execute(
                    text("SET search_path TO :postgres_schema"),
                    parameters={"postgres_schema": postgres_schema},
                )
        yield connection
