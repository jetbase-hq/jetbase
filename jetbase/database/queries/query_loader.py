from enum import Enum

from sqlalchemy import Engine, TextClause, create_engine

from jetbase.config import get_config
from jetbase.database.queries.base import BaseQueries, QueryMethod
from jetbase.database.queries.postgres import PostgresQueries
from jetbase.database.queries.sqlite import SQLiteQueries
from jetbase.database.queries.snowflake import SnowflakeQueries


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SNOWFLAKE = "snowflake"


def get_database_type() -> DatabaseType:
    """
    Detect the database type from the configured SQLAlchemy URL.

    Reads the sqlalchemy_url from configuration and determines the
    database backend type.

    Returns:
        DatabaseType: The detected database type (postgresql or sqlite).

    Raises:
        ValueError: If the database type is not supported.
    """
    sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    engine: Engine = create_engine(url=sqlalchemy_url)
    dialect_name: str = engine.dialect.name.lower()

    if dialect_name.startswith("postgres"):
        return DatabaseType.POSTGRESQL
    elif dialect_name == "sqlite":
        return DatabaseType.SQLITE
    elif dialect_name == "snowflake":
        return DatabaseType.SNOWFLAKE
    else:
        raise ValueError(f"Unsupported database type: {dialect_name}")


def get_queries() -> type[BaseQueries]:
    """
    Get the appropriate query class for the current database type.

    Returns the PostgresQueries or SQLiteQueries class based on the
    detected database type.

    Returns:
        type[BaseQueries]: The database-specific query class.

    Raises:
        ValueError: If the database type is not supported.
    """
    db_type = get_database_type()

    if db_type == DatabaseType.POSTGRESQL:
        return PostgresQueries
    elif db_type == DatabaseType.SQLITE:
        return SQLiteQueries
    elif db_type == DatabaseType.SNOWFLAKE:
        return SnowflakeQueries
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Convenience function to get specific queries
def get_query(query_name: QueryMethod, **kwargs) -> TextClause:
    """
    Get a specific query for the current database type.

    Retrieves the appropriate database-specific query by looking up the
    query method on the correct query class for the current database.

    Args:
        query_name (QueryMethod): The enum value identifying which query
            to retrieve.
        **kwargs: Additional arguments to pass to the query method.

    Returns:
        TextClause: The database-specific SQLAlchemy TextClause query.

    Example:
        >>> get_query(QueryMethod.LATEST_VERSION_QUERY)
        <sqlalchemy.sql.elements.TextClause>
    """
    queries = get_queries()
    method = getattr(queries, query_name.value)
    return method(**kwargs)
