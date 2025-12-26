from sqlalchemy import Result, Row, text

from jetbase.core.checksum import calculate_checksum
from jetbase.core.file_parser import (
    get_description_from_filename,
)
from jetbase.core.models import MigrationRecord
from jetbase.enums import MigrationDirectionType, MigrationType
from jetbase.exceptions import VersionNotFoundError
from jetbase.queries.base import QueryMethod
from jetbase.queries.query_loader import get_query
from jetbase.repositories.db import get_db_connection


def run_migration(
    sql_statements: list[str],
    version: str | None,
    migration_operation: MigrationDirectionType,
    filename: str,
    migration_type: MigrationType = MigrationType.VERSIONED,
) -> None:
    """
    Execute a database migration by running SQL statements and recording the migration version.
    Args:
        sql_statements (list[str]): List of SQL statements to execute as part of the migration
        version (str): Version identifier to record after successful migration
    Returns:
        None
    """

    if migration_operation == MigrationDirectionType.UPGRADE and filename is None:
        raise ValueError("Filename must be provided for upgrade migrations.")

    with get_db_connection() as connection:
        for statement in sql_statements:
            connection.execute(text(statement))

        if migration_operation == MigrationDirectionType.UPGRADE:
            assert filename is not None

            description: str = get_description_from_filename(filename=filename)
            checksum: str = calculate_checksum(sql_statements=sql_statements)

            connection.execute(
                statement=get_query(QueryMethod.INSERT_VERSION_STMT),
                parameters={
                    "version": version,
                    "description": description,
                    "filename": filename,
                    "migration_type": migration_type.value,
                    "checksum": checksum,
                },
            )

        elif migration_operation == MigrationDirectionType.ROLLBACK:
            connection.execute(
                statement=get_query(QueryMethod.DELETE_VERSION_STMT),
                parameters={"version": version},
            )


def run_update_repeatable_migration(
    sql_statements: list[str],
    filename: str,
    migration_type: MigrationType,
) -> None:
    checksum: str = calculate_checksum(sql_statements=sql_statements)

    with get_db_connection() as connection:
        for statement in sql_statements:
            connection.execute(text(statement))

        connection.execute(
            statement=get_query(QueryMethod.UPDATE_REPEATABLE_MIGRATION_STMT),
            parameters={
                "checksum": checksum,
                "filename": filename,
                "migration_type": migration_type.value,
            },
        )


def fetch_latest_versioned_migration() -> MigrationRecord | None:
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

    with get_db_connection() as connection:
        result: Result[tuple[str]] = connection.execute(
            get_query(
                QueryMethod.MIGRATION_RECORDS_QUERY,
                ascending=False,
                migration_type=MigrationType.VERSIONED,
            )
        )
        latest_migration: Row | None = result.first()
    if not latest_migration:
        return None
    return MigrationRecord(*latest_migration)


def create_migrations_table_if_not_exists() -> None:
    """
    Creates the migrations table in the database
    if it does not already exist.
    Returns:
        None
    """

    with get_db_connection() as connection:
        connection.execute(
            statement=get_query(QueryMethod.CREATE_MIGRATIONS_TABLE_STMT)
        )


def get_latest_versions(
    limit: int | None = None, starting_version: str | None = None
) -> list[str]:
    """
    Retrieve the latest N migration versions from the database.
    Args:
        limit (int): The number of latest versions to retrieve
    Returns:
        list[str]: A list of the latest migration version strings
    """

    if limit and starting_version:
        raise ValueError(
            "Cannot specify both 'limit' and 'starting_version'. Choose only one."
        )

    if not limit and not starting_version:
        raise ValueError("Either 'limit' or 'starting_version' must be specified.")

    latest_versions: list[str] = []

    if limit:
        with get_db_connection() as connection:
            result: Result[tuple[str]] = connection.execute(
                statement=get_query(QueryMethod.LATEST_VERSIONS_QUERY),
                parameters={"limit": limit},
            )
            latest_versions: list[str] = [row[0] for row in result.fetchall()]

    if starting_version:
        with get_db_connection() as connection:
            version_exists_result: Result[tuple[int]] = connection.execute(
                statement=get_query(QueryMethod.CHECK_IF_VERSION_EXISTS_QUERY),
                parameters={"version": starting_version},
            )
            version_exists: int = version_exists_result.scalar_one()

            if version_exists == 0:
                raise VersionNotFoundError(
                    f"Version '{starting_version}' has not been applied yet or does not exist."
                )

            latest_versions_result: Result[tuple[str]] = connection.execute(
                statement=get_query(
                    QueryMethod.LATEST_VERSIONS_BY_STARTING_VERSION_QUERY
                ),
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
    with get_db_connection() as connection:
        result: Result[tuple[bool]] = connection.execute(
            statement=get_query(QueryMethod.CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY)
        )
        table_exists: bool = result.scalar_one()

    return table_exists


def get_migration_records() -> list[MigrationRecord]:
    """
    Retrieve the full migration history from the database.
    Returns:
        list[MigrationRecord]: A list of MigrationRecord containing migration details.
    """
    with get_db_connection() as connection:
        results: Result[tuple[str, int, str]] = connection.execute(
            statement=get_query(QueryMethod.MIGRATION_RECORDS_QUERY)
        )
        migration_records: list[MigrationRecord] = [
            MigrationRecord(
                order_executed=row.order_executed,
                version=row.version,
                description=row.description,
                filename=row.filename,
                migration_type=row.migration_type,
                applied_at=row.applied_at,
                checksum=row.checksum,
            )
            for row in results.fetchall()
        ]

    return migration_records


def get_checksums_by_version() -> list[tuple[str, str]]:
    """
    Retrieve all migration versions along with their corresponding checksums from the database.
    Returns:
        tuple[str, str]: A tuple containing migration version and its checksum.
    """
    with get_db_connection() as connection:
        results: Result[tuple[str, str]] = connection.execute(
            statement=get_query(QueryMethod.GET_VERSION_CHECKSUMS_QUERY)
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
    with get_db_connection() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=get_query(QueryMethod.GET_VERSION_CHECKSUMS_QUERY)
        )
        migrated_versions: list[str] = [row.version for row in results.fetchall()]

    return migrated_versions


def update_migration_checksums(versions_and_checksums: list[tuple[str, str]]) -> None:
    with get_db_connection() as connection:
        for version, checksum in versions_and_checksums:
            connection.execute(
                statement=get_query(QueryMethod.REPAIR_MIGRATION_CHECKSUM_STMT),
                parameters={"version": version, "checksum": checksum},
            )


def get_existing_on_change_filenames_to_checksums() -> dict[str, str]:
    with get_db_connection() as connection:
        results: Result[tuple[str, str]] = connection.execute(
            statement=get_query(QueryMethod.GET_RUNS_ON_CHANGE_MIGRATIONS_QUERY),
        )
        migration_filenames_to_checksums: dict[str, str] = {
            row.filename: row.checksum for row in results.fetchall()
        }

    return migration_filenames_to_checksums


def get_existing_repeatable_always_migration_filenames() -> set[str]:
    with get_db_connection() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=get_query(QueryMethod.GET_RUNS_ALWAYS_MIGRATIONS_QUERY),
        )
        migration_filenames: set[str] = {row.filename for row in results.fetchall()}

    return migration_filenames


def delete_missing_versions(versions: list[str]) -> None:
    with get_db_connection() as connection:
        for version in versions:
            connection.execute(
                statement=get_query(QueryMethod.DELETE_MISSING_VERSION_STMT),
                parameters={"version": version},
            )


def delete_missing_repeatables(repeatable_filenames: list[str]) -> None:
    with get_db_connection() as connection:
        for r_file in repeatable_filenames:
            connection.execute(
                statement=get_query(QueryMethod.DELETE_MISSING_REPEATABLE_STMT),
                parameters={"filename": r_file},
            )


def fetch_repeatable_migrations() -> list[MigrationRecord]:
    with get_db_connection() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=get_query(
                QueryMethod.MIGRATION_RECORDS_QUERY, all_repeatables=True
            ),
        )
        return [
            MigrationRecord(
                order_executed=row.order_executed,
                version=row.version,
                description=row.description,
                filename=row.filename,
                migration_type=row.migration_type,
                applied_at=row.applied_at,
                checksum=row.checksum,
            )
            for row in results.fetchall()
        ]
