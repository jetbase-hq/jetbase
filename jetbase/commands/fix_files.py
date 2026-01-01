import os

from jetbase.engine.lock import migration_lock
from jetbase.engine.repeatable import get_repeatable_filenames
from jetbase.engine.version import (
    get_migration_filepaths_by_version,
)
from jetbase.models import MigrationRecord
from jetbase.repositories.lock_repo import create_lock_table_if_not_exists
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    delete_missing_repeatables,
    delete_missing_versions,
    fetch_repeatable_migrations,
    get_migrated_versions,
)


def fix_files_cmd(audit_only: bool = False) -> None:
    """
    Fix migration tracking by removing database records for missing migration files.

    This function reconciles the migration state between the database and the filesystem
    by identifying and optionally removing records of migrations whose corresponding
    files no longer exist. It handles both versioned and repeatable migrations.
    Args:
        audit_only (bool, optional): If True, only reports missing migration files
            without making any changes to the database. If False, removes database
            records for missing migrations. Defaults to False.
    Returns:
        None: This function prints its results to stdout and does not return a value.
    """

    create_lock_table_if_not_exists()
    create_migrations_table_if_not_exists()

    migrated_versions: list[str] = get_migrated_versions()
    current_migration_filepaths_by_version: dict[str, str] = (
        get_migration_filepaths_by_version(
            directory=os.path.join(os.getcwd(), "migrations")
        )
    )
    repeatable_migrations: list[MigrationRecord] = fetch_repeatable_migrations()
    all_repeatable_filenames: list[str] = get_repeatable_filenames()

    missing_versions: list[str] = []
    missing_repeatables: list[str] = []

    for migrated_version in migrated_versions:
        if migrated_version not in current_migration_filepaths_by_version:
            missing_versions.append(migrated_version)

    for r_migration in repeatable_migrations:
        if r_migration.filename not in all_repeatable_filenames:
            missing_repeatables.append(r_migration.filename)

    if audit_only:
        if missing_versions or missing_repeatables:
            print("The following migrations are missing their corresponding files:")
            for version in missing_versions:
                print(f"→ {version}")
            for r_file in missing_repeatables:
                print(f"→ {r_file}")

        else:
            print("All migrations have corresponding files.")
        return

    if not audit_only:
        if missing_versions or missing_repeatables:
            with migration_lock():
                if missing_versions:
                    delete_missing_versions(versions=missing_versions)
                    print("Stopped tracking the following missing versions:")
                    for version in missing_versions:
                        print(f"→ {version}")

                if missing_repeatables:
                    delete_missing_repeatables(repeatable_filenames=missing_repeatables)
                    print(
                        "Removed the following missing repeatable migrations from the database:"
                    )
                    for r_file in missing_repeatables:
                        print(f"→ {r_file}")
        else:
            print("No missing migration files.")
