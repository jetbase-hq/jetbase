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
    Apply pending migrations to the database in order.

    Args:
        count (int | None): Maximum number of migrations to apply.
        to_version (str | None): Apply migrations up to this version.
        dry_run (bool): Preview SQL without executing.
        skip_validation (bool): Skip all validations.
        skip_checksum_validation (bool): Skip checksum validation only.
        skip_file_validation (bool): Skip file validation only.

    Raises:
        ValueError: If both count and to_version are specified.
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

    filepaths_by_version: dict[str, str] = _get_filepaths_by_version(
        latest_migration=latest_migration,
        count=count,
        to_version=to_version,
    )

    repeatable_always_filepaths: list[str] = get_repeatable_always_filepaths(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR)
    )

    runs_on_change_filepaths: list[str] = get_runs_on_change_filepaths(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        changed_only=True,
    )

    if not dry_run:
        if (
            not filepaths_by_version
            and not repeatable_always_filepaths
            and not runs_on_change_filepaths
        ):
            print("Migrations are up to date.")
            return

        with migration_lock():
            print("Starting migrations...")

            _run_versioned_migrations(filepaths_by_version=filepaths_by_version)

            _run_repeatable_always_migrations(
                repeatable_always_filepaths=repeatable_always_filepaths
            )

            _run_repeatable_on_change_migrations(
                runs_on_change_filepaths=runs_on_change_filepaths
            )

            print("Migrations completed successfully.")
    else:
        process_dry_run(
            version_to_filepath=filepaths_by_version,
            migration_operation=MigrationDirectionType.UPGRADE,
            repeatable_always_filepaths=repeatable_always_filepaths,
            runs_on_change_filepaths=runs_on_change_filepaths,
        )


def _get_filepaths_by_version(
    latest_migration: MigrationRecord | None,
    count: int | None = None,
    to_version: str | None = None,
) -> dict[str, str]:
    """
    Get pending migration file paths filtered by count or target version.

    Args:
        latest_migration (MigrationRecord | None): The most recently
            applied migration, or None if no migrations applied.
        count (int | None): Limit to this many migrations. Defaults to None.
        to_version (str | None): Include migrations up to this version.
            Defaults to None.

    Returns:
        dict[str, str]: Mapping of version to file path for pending migrations.

    Raises:
        FileNotFoundError: If to_version is not found in pending migrations.
    """
    filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        version_to_start_from=latest_migration.version if latest_migration else None,
    )

    if latest_migration:
        filepaths_by_version = dict(list(filepaths_by_version.items())[1:])

    if count:
        filepaths_by_version = dict(list(filepaths_by_version.items())[:count])
    elif to_version:
        if filepaths_by_version.get(to_version) is None:
            raise FileNotFoundError(
                f"The specified to_version '{to_version}' does not exist among pending migrations."
            )
        seen_versions: dict[str, str] = {}
        for file_version, file_path in filepaths_by_version.items():
            seen_versions[file_version] = file_path
            if file_version == to_version:
                break
        filepaths_by_version = seen_versions

    return filepaths_by_version


def _run_versioned_migrations(filepaths_by_version: dict[str, str]) -> None:
    """
    Execute versioned (V__) migrations.

    Args:
        filepaths_by_version (dict[str, str]): Mapping of version to file path.
    """
    for version, file_path in filepaths_by_version.items():
        sql_statements: list[str] = parse_upgrade_statements(file_path=file_path)
        filename: str = os.path.basename(file_path)

        run_migration(
            sql_statements=sql_statements,
            version=version,
            migration_operation=MigrationDirectionType.UPGRADE,
            filename=filename,
        )

        print(f"Migration applied successfully: {filename}")


def _run_repeatable_always_migrations(
    repeatable_always_filepaths: list[str],
) -> None:
    """
    Execute runs-always (RA__) migrations.

    Args:
        repeatable_always_filepaths (list[str]): List of RA__ file paths.
    """
    if repeatable_always_filepaths:
        for filepath in repeatable_always_filepaths:
            sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
            filename: str = os.path.basename(filepath)

            if filename in get_existing_repeatable_always_migration_filenames():
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


def _run_repeatable_on_change_migrations(runs_on_change_filepaths: list[str]) -> None:
    """
    Execute runs-on-change (ROC__) migrations.

    Args:
        runs_on_change_filepaths (list[str]): List of ROC__ file paths.
    """
    if runs_on_change_filepaths:
        for filepath in runs_on_change_filepaths:
            sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
            filename: str = os.path.basename(filepath)

            if filename in list(get_existing_on_change_filenames_to_checksums().keys()):
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
