from sqlalchemy import Result, Row, text

from jetbase.database.connection import get_db_connection
from jetbase.database.queries.base import QueryMethod
from jetbase.database.queries.query_loader import get_query
from jetbase.engine.checksum import calculate_checksum
from jetbase.engine.file_parser import (
    get_description_from_filename,
)
from jetbase.enums import MigrationDirectionType, MigrationType
from jetbase.exceptions import VersionNotFoundError
from jetbase.models import MigrationRecord


def run_migration(
    sql_statements: list[str],
    version: str | None,
    migration_operation: MigrationDirectionType,
    filename: str,
    migration_type: MigrationType = MigrationType.VERSIONED,
) -> None:
    """
    Execute SQL statements and record the migration in the database.

    Runs all SQL statements within a transaction, then either inserts
    (for upgrade) or deletes (for rollback) the migration record.

    Args:
        sql_statements (list[str]): List of SQL statements to execute.
        version (str | None): Version string for the migration. Required
            for versioned migrations, can be None for repeatables.
        migration_operation (MigrationDirectionType): Whether this is an
            UPGRADE or ROLLBACK operation.
        filename (str): The migration filename, used to extract description.
        migration_type (MigrationType): Type of migration (VERSIONED,
            RUNS_ALWAYS, or RUNS_ON_CHANGE). Defaults to VERSIONED.

    Returns:
        None: Migration is executed and recorded as a side effect.

    Raises:
        ValueError: If filename is None for an upgrade operation.
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
    """
    Execute and update an existing repeatable migration record.

    Runs the SQL statements and updates the existing migration record
    with a new checksum and applied_at timestamp.

    Args:
        sql_statements (list[str]): List of SQL statements to execute.
        filename (str): The migration filename to update.
        migration_type (MigrationType): Type of repeatable migration
            (RUNS_ALWAYS or RUNS_ON_CHANGE).

    Returns:
        None: Migration is executed and record is updated as a side effect.
    """
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
    Get the most recently applied versioned migration from the database.

    Queries the jetbase_migrations table for the versioned migration
    with the most recent applied_at timestamp.

    Returns:
        MigrationRecord | None: The most recent migration record if any
            migrations have been applied, otherwise None.
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
    Create the jetbase_migrations table if it doesn't already exist.

    Creates the table used to track applied migrations, including
    columns for version, description, filename, checksum, and timestamps.

    Returns:
        None: Table is created as a side effect.
    """

    with get_db_connection() as connection:
        connection.execute(
            statement=get_query(QueryMethod.CREATE_MIGRATIONS_TABLE_STMT)
        )


def get_latest_versions(
    limit: int | None = None, starting_version: str | None = None
) -> list[str]:
    """
    Get recent migration versions from the database.

    Retrieves either the N most recent versions or all versions applied
    after a specified starting version.

    Args:
        limit (int | None): Maximum number of versions to return.
            Cannot be used with starting_version. Defaults to None.
        starting_version (str | None): Return all versions applied after
            this version. Cannot be used with limit. Defaults to None.

    Returns:
        list[str]: List of version strings in descending order by
            application time.

    Raises:
        ValueError: If both limit and starting_version are specified,
            or if neither is specified.
        VersionNotFoundError: If starting_version has not been applied.
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

    Queries the database metadata to determine if the migrations
    tracking table has been created.

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
    Get all migration records from the database.

    Retrieves the complete migration history including versioned
    and repeatable migrations, ordered by application time.

    Returns:
        list[MigrationRecord]: List of all migration records in
            chronological order.
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
    Get version and checksum pairs for all versioned migrations.

    Retrieves the checksum stored for each version when it was
    originally applied, ordered by execution order.

    Returns:
        list[tuple[str, str]]: List of (version, checksum) tuples
            in order of application.
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
    Get all applied versioned migration versions from the database.

    Returns the version string for each versioned migration that
    has been applied, in order of application.

    Returns:
        list[str]: List of version strings in order of application.
    """
    with get_db_connection() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=get_query(QueryMethod.GET_VERSION_CHECKSUMS_QUERY)
        )
        migrated_versions: list[str] = [row.version for row in results.fetchall()]

    return migrated_versions


def update_migration_checksums(versions_and_checksums: list[tuple[str, str]]) -> None:
    """
    Update stored checksums for specified migration versions.

    Updates the checksum values in the database for migrations
    whose files have been modified since they were applied.

    Args:
        versions_and_checksums (list[tuple[str, str]]): List of
            (version, new_checksum) tuples to update.

    Returns:
        None: Checksums are updated as a side effect.
    """
    with get_db_connection() as connection:
        for version, checksum in versions_and_checksums:
            connection.execute(
                statement=get_query(QueryMethod.REPAIR_MIGRATION_CHECKSUM_STMT),
                parameters={"version": version, "checksum": checksum},
            )


def get_existing_on_change_filenames_to_checksums() -> dict[str, str]:
    """
    Get filename to checksum mapping for runs-on-change migrations.

    Retrieves the checksums stored for each runs-on-change migration
    when it was last applied.

    Returns:
        dict[str, str]: Dictionary mapping filenames to their stored
            checksum values.
    """
    with get_db_connection() as connection:
        results: Result[tuple[str, str]] = connection.execute(
            statement=get_query(QueryMethod.GET_RUNS_ON_CHANGE_MIGRATIONS_QUERY),
        )
        migration_filenames_to_checksums: dict[str, str] = {
            row.filename: row.checksum for row in results.fetchall()
        }

    return migration_filenames_to_checksums


def get_existing_repeatable_always_migration_filenames() -> set[str]:
    """
    Get filenames of all runs-always migrations in the database.

    Retrieves the filenames of all runs-always migrations that have
    been applied at least once.

    Returns:
        set[str]: Set of runs-always migration filenames.
    """
    with get_db_connection() as connection:
        results: Result[tuple[str]] = connection.execute(
            statement=get_query(QueryMethod.GET_RUNS_ALWAYS_MIGRATIONS_QUERY),
        )
        migration_filenames: set[str] = {row.filename for row in results.fetchall()}

    return migration_filenames


def delete_missing_versions(versions: list[str]) -> None:
    """
    Delete migration records for specified versions.

    Removes records from the jetbase_migrations table for versioned
    migrations whose files no longer exist.

    Args:
        versions (list[str]): List of version strings to delete.

    Returns:
        None: Records are deleted as a side effect.
    """
    with get_db_connection() as connection:
        for version in versions:
            connection.execute(
                statement=get_query(QueryMethod.DELETE_MISSING_VERSION_STMT),
                parameters={"version": version},
            )


def delete_missing_repeatables(repeatable_filenames: list[str]) -> None:
    """
    Delete migration records for specified repeatable filenames.

    Removes records from the jetbase_migrations table for repeatable
    migrations whose files no longer exist.

    Args:
        repeatable_filenames (list[str]): List of filenames to delete.

    Returns:
        None: Records are deleted as a side effect.
    """
    with get_db_connection() as connection:
        for r_file in repeatable_filenames:
            connection.execute(
                statement=get_query(QueryMethod.DELETE_MISSING_REPEATABLE_STMT),
                parameters={"filename": r_file},
            )


def fetch_repeatable_migrations() -> list[MigrationRecord]:
    """
    Get all repeatable migration records from the database.

    Retrieves all runs-always and runs-on-change migrations that
    have been applied.

    Returns:
        list[MigrationRecord]: List of all repeatable migration records.
    """
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
