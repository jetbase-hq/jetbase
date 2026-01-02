import os

from jetbase.engine.dry_run import process_dry_run
from jetbase.engine.file_parser import parse_rollback_statements
from jetbase.engine.lock import (
    migration_lock,
)
from jetbase.engine.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationDirectionType
from jetbase.exceptions import VersionNotFoundError
from jetbase.repositories.lock_repo import create_lock_table_if_not_exists
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    get_latest_versions,
    run_migration,
)


def rollback_cmd(
    count: int | None = None, to_version: str | None = None, dry_run: bool = False
) -> None:
    """
    Rollback applied migrations.

    Reverts previously applied migrations by executing their rollback SQL
    statements in reverse order. Can rollback a specific number of migrations
    or all migrations after a specified version.

    Args:
        count (int | None): Number of migrations to rollback. If None and
            to_version is also None, defaults to 1. Defaults to None.
        to_version (str | None): Rollback all migrations applied after this
            version. Cannot be used with count. Defaults to None.
        dry_run (bool): If True, shows a preview of the rollback SQL without
            executing it. Defaults to False.

    Returns:
        None: Prints rollback status for each migration to stdout.

    Raises:
        ValueError: If both count and to_version are specified.
        VersionNotFoundError: If a required migration file is missing.
    """
    create_migrations_table_if_not_exists()
    create_lock_table_if_not_exists()

    if count is not None and to_version is not None:
        raise ValueError(
            "Cannot specify both 'count' and 'to_version' for rollback. "
            "Select only one, or do not specify either to rollback the last migration."
        )
    if count is None and to_version is None:
        count = 1

    latest_migration_versions: list[str] = _get_latest_migration_versions(
        count=count, to_version=to_version
    )

    if not latest_migration_versions:
        print("Nothing to rollback.")
        return

    versions_to_rollback: dict[str, str] = _get_versions_to_rollback(
        latest_migration_versions=latest_migration_versions
    )

    _validate_rollback_files_exist(
        latest_migration_versions=latest_migration_versions,
        versions_to_rollback=versions_to_rollback,
    )

    if not dry_run:
        with migration_lock():
            print("Starting rollback...")
            for version, file_path in versions_to_rollback.items():
                sql_statements: list[str] = parse_rollback_statements(
                    file_path=file_path
                )
                filename: str = os.path.basename(file_path)

                run_migration(
                    sql_statements=sql_statements,
                    version=version,
                    migration_operation=MigrationDirectionType.ROLLBACK,
                    filename=filename,
                )

                print(f"Rollback applied successfully: {filename}")
            print("Rollbacks completed successfully.")

    else:
        process_dry_run(
            version_to_filepath=versions_to_rollback,
            migration_operation=MigrationDirectionType.ROLLBACK,
        )


def _get_latest_migration_versions(
    count: int | None = None, to_version: str | None = None
) -> list[str]:
    """
    Get the latest migration versions from the database.

    Retrieves migration versions either by count or by starting version.
    If neither is specified, returns the single most recent migration.

    Args:
        count (int | None): Number of migrations to retrieve.
            Defaults to None.
        to_version (str | None): Retrieve all migrations applied after
            this version. Defaults to None.

    Returns:
        list[str]: List of version strings in order of application.
    """
    if count:
        return get_latest_versions(limit=count)
    elif to_version:
        return get_latest_versions(starting_version=to_version)
    else:
        return get_latest_versions(limit=1)


def _get_versions_to_rollback(latest_migration_versions: list[str]) -> dict[str, str]:
    """
    Get migration file paths for versions to rollback.

    Maps version strings to their corresponding file paths, ordered
    in reverse (newest first) for rollback execution.

    Args:
        latest_migration_versions (list[str]): List of version strings
            to rollback, ordered oldest to newest.

    Returns:
        dict[str, str]: Mapping of version to file path, reversed so
            newest versions are rolled back first.
    """
    versions_to_rollback: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migration_versions[-1],
        end_version=latest_migration_versions[0],
    )

    return dict(reversed(versions_to_rollback.items()))


def _validate_rollback_files_exist(
    latest_migration_versions: list[str], versions_to_rollback: dict[str, str]
) -> None:
    """
    Validate that all migration files exist for rollback.

    Ensures every version that needs to be rolled back has a corresponding
    migration file in the migrations directory.

    Args:
        latest_migration_versions (list[str]): Version strings that need
            to be rolled back.
        versions_to_rollback (dict[str, str]): Mapping of version to
            file path for available migration files.

    Raises:
        VersionNotFoundError: If any migration file is missing.
    """
    for version in latest_migration_versions:
        if version not in list(versions_to_rollback.keys()):
            raise VersionNotFoundError(
                f"Migration file for version '{version}' not found. Cannot proceed with rollback.\n"
                "Please restore the missing migration file and try again, or run 'jetbase fix' "
                "to synchronize the migrations table with existing files before retrying the rollback."
            )
