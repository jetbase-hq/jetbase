import os

from jetbase.constants import MIGRATIONS_DIR
from jetbase.engine.dry_run import process_dry_run
from jetbase.engine.file_parser import parse_upgrade_statements
from jetbase.engine.lock import migration_lock
from jetbase.engine.repeatable import (
    get_repeatable_always_filepaths,
    get_runs_on_change_filepaths,
)
from jetbase.engine.validation import run_migration_validations
from jetbase.engine.version import (
    get_migration_filepaths_by_version,
)
from jetbase.enums import MigrationDirectionType, MigrationType
from jetbase.models import MigrationRecord
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
    Apply pending migrations to the database.

    Executes all pending versioned migrations in order, followed by any
    repeatable migrations (runs-always and runs-on-change). Validates
    migration files and checksums before execution unless validation
    is explicitly skipped.

    Args:
        count (int | None): Maximum number of versioned migrations to apply.
            Cannot be used with to_version. Defaults to None (apply all).
        to_version (str | None): Apply migrations up to and including this
            version. Cannot be used with count. Defaults to None.
        dry_run (bool): If True, shows a preview of the SQL that would be
            executed without actually running it. Defaults to False.
        skip_validation (bool): If True, skips both checksum and file
            validation. Defaults to False.
        skip_checksum_validation (bool): If True, skips validation that
            checks if migration files have been modified. Defaults to False.
        skip_file_validation (bool): If True, skips validation that checks
            for missing or out-of-order files. Defaults to False.

    Returns:
        None: Prints migration status for each applied migration to stdout.

    Raises:
        ValueError: If both count and to_version are specified, or if count
            is not a positive integer.
        FileNotFoundError: If to_version is specified but not found in
            pending migrations.
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
        if (
            not all_versions
            and not repeatable_always_filepaths
            and not runs_on_change_filepaths
        ):
            print("Migrations are up to date.")
            return

        with migration_lock():
            print("Starting migrations...")
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
            print("Migrations completed successfully.")
    else:
        process_dry_run(
            version_to_filepath=all_versions,
            migration_operation=MigrationDirectionType.UPGRADE,
            repeatable_always_filepaths=repeatable_always_filepaths,
            runs_on_change_filepaths=runs_on_change_filepaths,
        )
