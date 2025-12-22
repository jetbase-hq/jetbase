import os

from jetbase.config import get_config
from jetbase.core.checksum import (
    validate_current_migration_files_match_checksums,
    validate_migrated_repeatable_versions_in_migration_files,
    validate_migrated_versions_in_current_migration_files,
    validate_no_duplicate_migration_file_versions,
    validate_no_new_migration_files_with_lower_version_than_latest_migration,
)
from jetbase.core.dry_run import process_dry_run
from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.core.lock import create_lock_table_if_not_exists, migration_lock
from jetbase.core.repository import (
    create_migrations_table_if_not_exists,
    get_checksums_by_version,
    get_existing_on_change_filenames_to_checksums,
    get_existing_repeatable_always_migration_filenames,
    get_last_updated_version,
    get_migrated_repeatable_filenames,
    get_migrated_versions,
    get_repeatable_always_filepaths,
    get_repeatable_on_change_filepaths,
    run_migration,
    run_update_repeatable_migration,
)
from jetbase.core.version import (
    get_migration_filepaths_by_version,
    get_repeatable_filenames,
)
from jetbase.enums import MigrationDirectionType, MigrationType


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

    latest_migrated_version: str | None = get_last_updated_version()

    if latest_migrated_version:
        run_upgrade_validations(
            latest_migrated_version=latest_migrated_version,
            skip_validation=skip_validation,
            skip_checksum_validation=skip_checksum_validation,
            skip_file_validation=skip_file_validation,
        )

    all_versions: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migrated_version,
    )

    if latest_migrated_version:
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
        directory=os.path.join(os.getcwd(), "migrations")
    )
    existing_repeatable_always_filenames: set[str] = (
        get_existing_repeatable_always_migration_filenames()
    )

    repeatable_on_change_filepaths: list[str] = get_repeatable_on_change_filepaths(
        directory=os.path.join(os.getcwd(), "migrations"),
        changed_only=True,
    )

    existing_repeatable_on_change_filenames: list[str] = list(
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
                            migration_type=MigrationType.REPEATABLE_ALWAYS,
                        )
                        print(f"Migration applied successfully: {filename}")
                    else:
                        run_migration(
                            sql_statements=sql_statements,
                            version=None,
                            migration_operation=MigrationDirectionType.UPGRADE,
                            filename=filename,
                            migration_type=MigrationType.REPEATABLE_ALWAYS,
                        )
                        print(f"Migration applied successfully: {filename}")

            if repeatable_on_change_filepaths:
                for filepath in repeatable_on_change_filepaths:
                    sql_statements: list[str] = parse_upgrade_statements(
                        file_path=filepath
                    )
                    filename: str = os.path.basename(filepath)

                    if filename in existing_repeatable_on_change_filenames:
                        # update migration
                        run_update_repeatable_migration(
                            sql_statements=sql_statements,
                            filename=filename,
                            migration_type=MigrationType.REPEATABLE_ON_CHANGE,
                        )
                        print(f"Migration applied successfully: {filename}")
                    else:
                        run_migration(
                            sql_statements=sql_statements,
                            version=None,
                            migration_operation=MigrationDirectionType.UPGRADE,
                            filename=filename,
                            migration_type=MigrationType.REPEATABLE_ON_CHANGE,
                        )
                        print(f"Migration applied successfully: {filename}")
    else:
        process_dry_run(
            version_to_filepath=all_versions,
            migration_operation=MigrationDirectionType.UPGRADE,
            repeatable_always_filepaths=repeatable_always_filepaths,
            repeatable_on_change_filepaths=repeatable_on_change_filepaths,
        )


def run_upgrade_validations(
    latest_migrated_version: str,
    skip_validation: bool = False,
    skip_checksum_validation: bool = False,
    skip_file_validation: bool = False,
) -> None:
    """
    Run validations on migration files before performing upgrade.
    """

    skip_validation_config: bool = get_config().skip_validation
    skip_checksum_validation_config: bool = get_config().skip_checksum_validation
    skip_file_validation_config: bool = get_config().skip_file_validation

    migrations_directory: str = os.path.join(os.getcwd(), "migrations")

    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=migrations_directory
    )
    validate_no_duplicate_migration_file_versions(
        current_migration_filepaths_by_version=migration_filepaths_by_version
    )

    if not skip_validation and not skip_validation_config:
        if not skip_file_validation and not skip_file_validation_config:
            migrated_versions: list[str] = get_migrated_versions()

            validate_no_new_migration_files_with_lower_version_than_latest_migration(
                current_migration_filepaths_by_version=migration_filepaths_by_version,
                migrated_versions=migrated_versions,
                latest_migrated_version=latest_migrated_version,
            )

            validate_migrated_versions_in_current_migration_files(
                migrated_versions=migrated_versions,
                current_migration_filepaths_by_version=migration_filepaths_by_version,
            )

            validate_migrated_repeatable_versions_in_migration_files(
                migrated_repeatable_filenames=get_migrated_repeatable_filenames(),
                all_repeatable_filenames=get_repeatable_filenames(),
            )

        migrated_filepaths_by_version: dict[str, str] = (
            get_migration_filepaths_by_version(
                directory=migrations_directory, end_version=latest_migrated_version
            )
        )

        if not skip_checksum_validation and not skip_checksum_validation_config:
            validate_current_migration_files_match_checksums(
                migrated_filepaths_by_version=migrated_filepaths_by_version,
                migrated_versions_and_checksums=get_checksums_by_version(),
            )
