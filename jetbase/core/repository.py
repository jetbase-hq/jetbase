from sqlalchemy import Engine, Result, create_engine, text

from jetbase.config import get_sqlalchemy_url
from jetbase.core.checksum import calculate_checksum
from jetbase.core.file_parser import get_description_from_filename
from jetbase.core.models import MigrationRecord
from jetbase.enums import MigrationOperationType
from jetbase.queries import (
    CHECK_IF_LOCK_TABLE_EXISTS_QUERY,
    CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY,
    CHECK_IF_VERSION_EXISTS_QUERY,
    CREATE_MIGRATIONS_TABLE_STMT,
    DELETE_VERSION_STMT,
    GET_VERSION_CHECKSUMS_QUERY,
    INSERT_VERSION_STMT,
    LATEST_VERSION_QUERY,
    LATEST_VERSIONS_BY_STARTING_VERSION_QUERY,
    LATEST_VERSIONS_QUERY,
    MIGRATION_RECORDS_QUERY,
    REPAIR_MIGRATION_CHECKSUM_STMT,
)


def get_last_updated_version() -> str | None:
    """
    Retrieves the latest version from the database.
    This function connects to the database, executes a query to get the most recent version,
    and returns that version as a string.
    Returns:
        str | None: The latest version string if available, None if no version was found.
    """

    table_exists: bool = migrations_table_exists()
    if not table_exists:
        return None

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result: Result[tuple[str]] = connection.execute(LATEST_VERSION_QUERY)
        latest_version: str | None = result.scalar()
    if not latest_version:
        return None
    return latest_version


def create_migrations_table_if_not_exists() -> None:
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
    sql_statements: list[str],
    version: str,
    migration_operation: MigrationOperationType,
    filename: str | None = None,
) -> None:
    """
    Execute a database migration by running SQL statements and recording the migration version.
    Args:
        sql_statements (list[str]): List of SQL statements to execute as part of the migration
        version (str): Version identifier to record after successful migration
    Returns:
        None
    """

    if migration_operation == MigrationOperationType.UPGRADE and filename is None:
        raise ValueError("Filename must be provided for upgrade migrations.")

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        for statement in sql_statements:
            connection.execute(text(statement))

        if migration_operation == MigrationOperationType.UPGRADE:
            assert filename is not None

            description: str = get_description_from_filename(filename=filename)
            checksum: str = calculate_checksum(sql_statements=sql_statements)

            connection.execute(
                statement=INSERT_VERSION_STMT,
                parameters={
                    "version": version,
                    "description": description,
                    "filename": filename,
                    "checksum": checksum,
                },
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
    starting_version = starting_version

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


def migrations_table_exists() -> bool:
    """
    Check if the jetbase_migrations table exists in the database.
    Returns:
        bool: True if the jetbase_migrations table exists, False otherwise.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result: Result[tuple[bool]] = connection.execute(
            statement=CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY
        )
        table_exists: bool = result.scalar_one()

    return table_exists


def get_migration_records() -> list[MigrationRecord]:
    """
    Retrieve the full migration history from the database.
    Returns:
        list[MigrationRecord]: A list of MigrationRecord containing migration details.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        results: Result[tuple[str, int, str]] = connection.execute(
            statement=MIGRATION_RECORDS_QUERY
        )
        migration_records: list[MigrationRecord] = [
            MigrationRecord(
                version=row.version,
                order_executed=row.order_executed,
                description=row.description,
            )
            for row in results.fetchall()
        ]

    return migration_records


def lock_table_exists() -> bool:
    """
    Check if the jetbase_lock table exists in the database.
    Returns:
        bool: True if the jetbase_lock table exists, False otherwise.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result: Result[tuple[bool]] = connection.execute(
            statement=CHECK_IF_LOCK_TABLE_EXISTS_QUERY
        )
        table_exists: bool = result.scalar_one()

    return table_exists


def get_checksums_by_version() -> list[tuple[str, str]]:
    """
    Retrieve all migration versions along with their corresponding checksums from the database.
    Returns:
        tuple[str, str]: A tuple containing migration version and its checksum.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        results: Result[tuple[str, str]] = connection.execute(
            statement=GET_VERSION_CHECKSUMS_QUERY
        )
        versions_and_checksums: list[tuple[str, str]] = [
            (row.version, row.checksum) for row in results.fetchall()
        ]

    return versions_and_checksums


def get_migrated_versions() -> list[str]:
    """
    Retrieve all migrated versions from the database.
    Returns:
        list[str]: A list of migrated version strings.
    """

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=GET_VERSION_CHECKSUMS_QUERY
        )
        migrated_versions: list[str] = [row.version for row in results.fetchall()]

    return migrated_versions


def update_migration_checksums(versions_and_checksums: list[tuple[str, str]]) -> None:
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        for version, checksum in versions_and_checksums:
            connection.execute(
                statement=REPAIR_MIGRATION_CHECKSUM_STMT,
                parameters={"version": version, "checksum": checksum},
            )
