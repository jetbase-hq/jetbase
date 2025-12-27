import os

from jetbase.constants import MIGRATIONS_DIR
from jetbase.core.dry_run import process_dry_run
from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.core.lock import migration_lock
from jetbase.core.models import MigrationRecord
from jetbase.core.repeatable import (
    get_repeatable_always_filepaths,
    get_runs_on_change_filepaths,
)
from jetbase.core.validation import run_migration_validations
from jetbase.core.version import (
    get_migration_filepaths_by_version,
)
from jetbase.enums import MigrationDirectionType, MigrationType
from jetbase.repositories.lock_repo import create_lock_table_if_not_exists
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    fetch_latest_versioned_migration,
    get_existing_on_change_filenames_to_checksums,
    get_existing_repeatable_always_migration_filenames,
    run_migration,
    run_update_repeatable_migration,
)


def upgrade_cmd(
    count: int | None = None,
    to_version: str | None = None,
    dry_run: bool = False,
    skip_validation: bool = False,
    skip_checksum_validation: bool = False,
    skip_file_validation: bool = False,
) -> None:
    """
    Run database migrations by applying all pending SQL migration files.
    Executes migration files in order starting from the last migrated version + 1,
    updating the jetbase_migrations table after each successful migration.

    Returns:
        None
    """

    if count is not None and to_version is not None:
        raise ValueError(
            "Cannot specify both 'count' and 'to_version' for upgrade. "
            "Select only one, or do not specify either to run all pending migrations."
        )

    if count:
        if count < 1 or not isinstance(count, int):
            raise ValueError("'count' must be a positive integer.")

    create_migrations_table_if_not_exists()
    create_lock_table_if_not_exists()

    latest_migration: MigrationRecord | None = fetch_latest_versioned_migration()

    if latest_migration:
        run_migration_validations(
            latest_migrated_version=latest_migration.version,
            skip_validation=skip_validation,
            skip_checksum_validation=skip_checksum_validation,
            skip_file_validation=skip_file_validation,
        )

    all_versions: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        version_to_start_from=latest_migration.version if latest_migration else None,
    )

    if latest_migration:
        all_versions = dict(list(all_versions.items())[1:])

    if count:
        all_versions = dict(list(all_versions.items())[:count])
    elif to_version:
        if all_versions.get(to_version) is None:
            raise FileNotFoundError(
                f"The specified to_version '{to_version}' does not exist among pending migrations."
            )
        all_versions_list = []
        for file_version, file_path in all_versions.items():
            all_versions_list.append((file_version, file_path))
            if file_version == to_version:
                break
        all_versions = dict(all_versions_list)

    repeatable_always_filepaths: list[str] = get_repeatable_always_filepaths(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR)
    )
    existing_repeatable_always_filenames: set[str] = (
        get_existing_repeatable_always_migration_filenames()
    )

    runs_on_change_filepaths: list[str] = get_runs_on_change_filepaths(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        changed_only=True,
    )

    existing_runs_on_change_filenames: list[str] = list(
        get_existing_on_change_filenames_to_checksums().keys()
    )

    if not dry_run:
        with migration_lock():
            for version, file_path in all_versions.items():
                sql_statements: list[str] = parse_upgrade_statements(
                    file_path=file_path
                )
                filename: str = os.path.basename(file_path)

                run_migration(
                    sql_statements=sql_statements,
                    version=version,
                    migration_operation=MigrationDirectionType.UPGRADE,
                    filename=filename,
                )

                print(f"Migration applied successfully: {filename}")

            if repeatable_always_filepaths:
                for filepath in repeatable_always_filepaths:
                    sql_statements: list[str] = parse_upgrade_statements(
                        file_path=filepath
                    )
                    filename: str = os.path.basename(filepath)

                    if filename in existing_repeatable_always_filenames:
                        run_update_repeatable_migration(
                            sql_statements=sql_statements,
                            filename=filename,
                            migration_type=MigrationType.RUNS_ALWAYS,
                        )
                        print(f"Migration applied successfully: {filename}")
                    else:
                        run_migration(
                            sql_statements=sql_statements,
                            version=None,
                            migration_operation=MigrationDirectionType.UPGRADE,
                            filename=filename,
                            migration_type=MigrationType.RUNS_ALWAYS,
                        )
                        print(f"Migration applied successfully: {filename}")

            if runs_on_change_filepaths:
                for filepath in runs_on_change_filepaths:
                    sql_statements: list[str] = parse_upgrade_statements(
                        file_path=filepath
                    )
                    filename: str = os.path.basename(filepath)

                    if filename in existing_runs_on_change_filenames:
                        # update migration
                        run_update_repeatable_migration(
                            sql_statements=sql_statements,
                            filename=filename,
                            migration_type=MigrationType.RUNS_ON_CHANGE,
                        )
                        print(f"Migration applied successfully: {filename}")
                    else:
                        run_migration(
                            sql_statements=sql_statements,
                            version=None,
                            migration_operation=MigrationDirectionType.UPGRADE,
                            filename=filename,
                            migration_type=MigrationType.RUNS_ON_CHANGE,
                        )
                        print(f"Migration applied successfully: {filename}")
    else:
        process_dry_run(
            version_to_filepath=all_versions,
            migration_operation=MigrationDirectionType.UPGRADE,
            repeatable_always_filepaths=repeatable_always_filepaths,
            runs_on_change_filepaths=runs_on_change_filepaths,
        )
