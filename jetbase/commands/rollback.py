import os

from jetbase.core.dry_run import process_dry_run
from jetbase.core.file_parser import parse_rollback_statements
from jetbase.core.lock import (
    create_lock_table_if_not_exists,
    migration_lock,
)
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationDirectionType
from jetbase.exceptions import VersionNotFoundError
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    get_latest_versions,
    run_migration,
)


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
        latest_migration_versions = get_latest_versions(starting_version=to_version)

    if not latest_migration_versions:
        print("Nothing to rollback.")
        return

    versions_to_rollback: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migration_versions[-1],
        end_version=latest_migration_versions[0],
    )

    for version in latest_migration_versions:
        if version not in list(versions_to_rollback.keys()):
            raise VersionNotFoundError(
                f"Migration file for version '{version}' not found. Cannot proceed with rollback.\n"
                "Please restore the missing migration file and try again, or run 'jetbase fix' "
                "to synchronize the migrations table with existing files before retrying the rollback."
            )

    versions_to_rollback: dict[str, str] = dict(reversed(versions_to_rollback.items()))
    print(f"Versions to rollback: {versions_to_rollback}")

    if not dry_run:
        with migration_lock():
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
                filename: str = os.path.basename(file_path)

                print(f"Rollback applied successfully: {filename}")

    else:
        process_dry_run(
            version_to_filepath=versions_to_rollback,
            migration_operation=MigrationDirectionType.ROLLBACK,
        )
