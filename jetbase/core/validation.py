import os

from jetbase.core.repository import delete_missing_versions, get_migrated_versions
from jetbase.core.version import get_migration_filepaths_by_version


def fix_files(audit_only: bool = False) -> None:
    """Fix file version validation issues."""

    migrated_versions: list[str] = get_migrated_versions()
    current_migration_filepaths_by_version: dict[str, str] = (
        get_migration_filepaths_by_version(
            directory=os.path.join(os.getcwd(), "migrations")
        )
    )

    missing_versions: list[str] = []

    for migrated_version in migrated_versions:
        if migrated_version not in current_migration_filepaths_by_version:
            missing_versions.append(migrated_version)

    if audit_only:
        if missing_versions:
            print("The following migrated versions are missing migration files:")
            for version in missing_versions:
                print(f"→ {version}")

        else:
            print("All migrated versions have corresponding migration files.")
        return

    if not audit_only:
        if missing_versions:
            delete_missing_versions(versions=missing_versions)
            print("Removed the following missing migrated versions from the database:")
            for version in missing_versions:
                print(f"→ {version}")
        else:
            print("No missing migrated versions to fix.")
