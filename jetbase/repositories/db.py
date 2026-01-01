from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Connection, Engine, create_engine, text

from jetbase.config import get_config
from jetbase.enums import DatabaseType
from jetbase.queries.base import detect_db


@contextmanager
def get_db_connection() -> Generator[Connection, None, None]:
    """
    Context manager that yields a database connection for use in database operations.

    This function retrieves the current SQLAlchemy database URL from configuration,
    creates an engine, and yields a connection with a transaction opened. For PostgreSQL,
    if a schema is specified in the config, it sets the search_path accordingly.

    Yields:
        Connection: A SQLAlchemy Connection object.

    Usage:
        with get_db_connection() as conn:
            # Use conn to interact with the database
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
