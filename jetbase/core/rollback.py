import os

from jetbase.core.dry_run import process_dry_run
from jetbase.core.file_parser import parse_rollback_statements
from jetbase.core.lock import (
    create_lock_table_if_not_exists,
    migration_lock,
)
from jetbase.core.repository import (
    create_migrations_table_if_not_exists,
    get_latest_versions,
    get_latest_versions_by_starting_version,
    run_migration,
)
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationOperationType


def rollback_cmd(
    count: int | None = None, to_version: str | None = None, dry_run: bool = False
) -> None:
    create_migrations_table_if_not_exists()
    create_lock_table_if_not_exists()

    if count is not None and to_version is not None:
        raise ValueError(
            "Cannot specify both 'count' and 'to_version' for rollback. "
            "Select only one, or do not specify either to rollback the last migration."
        )
    if count is None and to_version is None:
        count = 1

    latest_migration_versions: list[str] = []
    if count:
        latest_migration_versions = get_latest_versions(limit=count)
    elif to_version:
        latest_migration_versions = get_latest_versions_by_starting_version(
            starting_version=to_version
        )

    if not latest_migration_versions:
        print("No migrations have been applied; nothing to rollback.")
        return

    versions_to_rollback: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migration_versions[-1],
        end_version=latest_migration_versions[0],
    )

    versions_to_rollback: dict[str, str] = dict(reversed(versions_to_rollback.items()))

    if not dry_run:
        with migration_lock():
            for version, file_path in versions_to_rollback.items():
                sql_statements: list[str] = parse_rollback_statements(
                    file_path=file_path
                )
                run_migration(
                    sql_statements=sql_statements,
                    version=version,
                    migration_operation=MigrationOperationType.ROLLBACK,
                )
                filename: str = os.path.basename(file_path)

                print(f"Rollback applied successfully: {filename}")

    else:
        process_dry_run(
            version_to_filepath=versions_to_rollback,
            migration_operation=MigrationOperationType.ROLLBACK,
        )
