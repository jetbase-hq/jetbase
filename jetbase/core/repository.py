from sqlalchemy import Engine, Result, create_engine, text

from jetbase.config import get_sqlalchemy_url
from jetbase.enums import MigrationOperationType
from jetbase.queries import (
    CHECK_IF_VERSION_EXISTS_QUERY,
    CREATE_MIGRATIONS_TABLE_STMT,
    DELETE_VERSION_STMT,
    INSERT_VERSION_STMT,
    LATEST_VERSION_QUERY,
    LATEST_VERSIONS_BY_STARTING_VERSION_QUERY,
    LATEST_VERSIONS_QUERY,
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


def run_migration(
    sql_statements: list[str], version: str, migration_operation: MigrationOperationType
) -> None:
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

        if migration_operation == MigrationOperationType.UPGRADE:
            connection.execute(
                statement=INSERT_VERSION_STMT, parameters={"version": version}
            )
        elif migration_operation == MigrationOperationType.ROLLBACK:
            connection.execute(
                statement=DELETE_VERSION_STMT, parameters={"version": version}
            )


def get_latest_versions(limit: int) -> list[str]:
    """
    Retrieve the latest N migration versions from the database.
    Args:
        limit (int): The number of latest versions to retrieve
    Returns:
        list[str]: A list of the latest migration version strings
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())
    latest_versions: list[str] = []

    with engine.begin() as connection:
        result: Result[tuple[str]] = connection.execute(
            statement=LATEST_VERSIONS_QUERY,
            parameters={"limit": limit},
        )
        latest_versions: list[str] = [row[0] for row in result.fetchall()]

    return latest_versions


def get_latest_versions_by_starting_version(
    starting_version: str,
) -> list[str]:
    """
    Retrieve the latest N migration versions from the database,
    starting from a specific version.
    Args:
        starting_version (str): The version to start retrieving from
        limit (int): The number of latest versions to retrieve
    Returns:
        list[str]: A list of the latest migration version strings
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())
    latest_versions: list[str] = []
    starting_version = starting_version[1:]

    with engine.begin() as connection:
        version_exists_result: Result[tuple[int]] = connection.execute(
            statement=CHECK_IF_VERSION_EXISTS_QUERY,
            parameters={"version": starting_version},
        )
        version_exists: int = version_exists_result.scalar_one()

        if version_exists == 0:
            raise ValueError(
                f"'{starting_version}' has not been applied yet or does not exist."
            )

        latest_versions_result: Result[tuple[str]] = connection.execute(
            statement=LATEST_VERSIONS_BY_STARTING_VERSION_QUERY,
            parameters={"starting_version": starting_version},
        )
        latest_versions: list[str] = [
            row[0] for row in latest_versions_result.fetchall()
        ]

    return latest_versions
