from enum import Enum

from sqlalchemy import Engine, TextClause, create_engine

from jetbase.config import get_config
from jetbase.queries.base import BaseQueries, QueryMethod
from jetbase.queries.postgres import PostgresQueries
from jetbase.queries.sqlite import SQLiteQueries


class DatabaseType(Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"


def get_database_type() -> DatabaseType:
    """
    Infer the database type from the SQLAlchemy URL.

    Returns:
        DatabaseType: The detected database type

    Raises:
        ValueError: If the database type is not supported
    """
    sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    engine: Engine = create_engine(url=sqlalchemy_url)
    dialect_name: str = engine.dialect.name.lower()

    if dialect_name.startswith("postgres"):
        return DatabaseType.POSTGRESQL
    elif dialect_name == "sqlite":
        return DatabaseType.SQLITE
    else:
        raise ValueError(f"Unsupported database type: {dialect_name}")


def get_queries() -> type[BaseQueries]:
    """
    Get the appropriate query class based on the database type.

    Returns:
        type[BaseQueries]: The query class for the detected database
    """
    db_type = get_database_type()

    if db_type == DatabaseType.POSTGRESQL:
        return PostgresQueries
    elif db_type == DatabaseType.SQLITE:
        return SQLiteQueries
    else:
        raise ValueError(f"Unsupported database type: {db_type}")


# Convenience function to get specific queries
def get_query(query_name: QueryMethod) -> TextClause:
    """
    Get a specific query for the current database type.

    Args:
        query_name: Name of the query method (e.g., 'latest_version_query')

    Returns:
        TextClause: The database-specific query
    """
    queries = get_queries()
    method = getattr(queries, query_name.value)
    return method()
