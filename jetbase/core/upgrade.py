import os

from jetbase.core.checksum import (
    validate_current_migration_files_match_checksums,
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
    get_last_updated_version,
    get_migrated_versions,
    run_migration,
)
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationOperationType


def upgrade_cmd(
    count: int | None = None,
    to_version: str | None = None,
    dry_run: bool = False,
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

    create_migrations_table_if_not_exists()
    create_lock_table_if_not_exists()

    latest_migrated_version: str | None = get_last_updated_version()

    if latest_migrated_version:
        run_upgrade_validations(
            latest_migrated_version=latest_migrated_version,
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
            raise ValueError(
                f"The specified to_version '{to_version}' does not exist among pending migrations."
            )
        all_versions_list = []
        for file_version, file_path in all_versions.items():
            all_versions_list.append((file_version, file_path))
            if file_version == to_version:
                break
        all_versions = dict(all_versions_list)

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
                    migration_operation=MigrationOperationType.UPGRADE,
                    filename=filename,
                )

                print(f"Migration applied successfully: {filename}")

    else:
        process_dry_run(
            version_to_filepath=all_versions,
            migration_operation=MigrationOperationType.UPGRADE,
        )


def run_upgrade_validations(
    latest_migrated_version: str,
    skip_checksum_validation: bool = False,
    skip_file_validation: bool = False,
) -> None:
    """
    Run validations on migration files before performing upgrade.
    """

    migrations_directory: str = os.path.join(os.getcwd(), "migrations")

    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=migrations_directory
    )
    validate_no_duplicate_migration_file_versions(
        current_migration_filepaths_by_version=migration_filepaths_by_version
    )

    if not skip_file_validation:
        migrated_versions: list[str] = get_migrated_versions()

        validate_migrated_versions_in_current_migration_files(
            migrated_versions=migrated_versions,
            current_migration_filepaths_by_version=migration_filepaths_by_version,
        )

        validate_no_new_migration_files_with_lower_version_than_latest_migration(
            current_migration_filepaths_by_version=migration_filepaths_by_version,
            migrated_versions=migrated_versions,
            latest_migrated_version=latest_migrated_version,
        )

        migrated_filepaths_by_version: dict[str, str] = (
            get_migration_filepaths_by_version(
                directory=migrations_directory, end_version=latest_migrated_version
            )
        )

        if not skip_checksum_validation:
            validate_current_migration_files_match_checksums(
                migrated_filepaths_by_version=migrated_filepaths_by_version,
                migrated_versions_and_checksums=get_checksums_by_version(),
            )
