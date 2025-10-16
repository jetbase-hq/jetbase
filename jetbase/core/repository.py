from sqlalchemy import Engine, Result, create_engine, text

from jetbase.config import get_sqlalchemy_url
from jetbase.queries import (
    CREATE_MIGRATIONS_TABLE_STMT,
    INSERT_VERSION_STMT,
    LATEST_VERSION_QUERY,
)


def get_last_updated_version() -> str | None:
    """
    Retrieves the latest version from the database.
    This function connects to the database, executes a query to get the most recent version,
    and returns that version as a string.
    Returns:
        str | None: The latest version string if available, None if no version was found.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result: Result[tuple[str]] = connection.execute(LATEST_VERSION_QUERY)
        latest_version: str | None = result.scalar()
    if not latest_version:
        return None
    return latest_version


def create_migrations_table() -> None:
    """
    Creates the migrations table in the database
    if it does not already exist.
    Returns:
        None
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())
    with engine.begin() as connection:
        connection.execute(statement=CREATE_MIGRATIONS_TABLE_STMT)


def run_migration(sql_statements: list[str], version: str) -> None:
    """
    Execute a database migration by running SQL statements and recording the migration version.
    Args:
        sql_statements (list[str]): List of SQL statements to execute as part of the migration
        version (str): Version identifier to record after successful migration
    Returns:
        None
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())
    with engine.begin() as connection:
        for statement in sql_statements:
            connection.execute(text(statement))
        connection.execute(
            statement=INSERT_VERSION_STMT, parameters={"version": version}
        )
