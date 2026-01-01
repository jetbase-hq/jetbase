import os

from jetbase.constants import MIGRATIONS_DIR
from jetbase.engine.checksum import calculate_checksum
from jetbase.engine.file_parser import parse_upgrade_statements
from jetbase.engine.lock import migration_lock
from jetbase.engine.validation import run_migration_validations
from jetbase.engine.version import get_migration_filepaths_by_version
from jetbase.exceptions import (
    MigrationVersionMismatchError,
)
from jetbase.repositories.migrations_repo import (
    get_checksums_by_version,
    update_migration_checksums,
)


def fix_checksums_cmd(audit_only: bool = False) -> None:
    """
    Fix or audit checksums for applied database migrations.
    This function validates and optionally repairs checksums for all migrations that have
    been applied to the database up to the latest migrated version. It detects drift between
    the current migration files and their recorded checksums in the migration history table.
    Args:
        audit_only (bool, optional): If True, only reports checksum mismatches without
            making any repairs. If False, updates the database with corrected checksums.
            Defaults to False.
    Returns:
        None
    Raises:
        MigrationVersionMismatchError: If there's a mismatch between expected and actual
            migration versions during processing.
    Notes:
        - If no migrations have been applied, the function exits early with a message.
        - The function acquires a migration lock before updating checksums to prevent
          concurrent modifications.
        - Checksum validation is skipped during the initial upgrade validation to allow
          the repair process to proceed.
        - In audit mode, the function prints a report of files with checksum drift
          without modifying the database.
    Example:
        >>> fix_checksums_cmd(audit_only=True)  # Check for drift only
        >>> fix_checksums_cmd()  # Repair detected drift
    """

    migrated_versions_and_checksums: list[tuple[str, str]] = get_checksums_by_version()
    if not migrated_versions_and_checksums:
        print("No migrations have been applied; nothing to repair.")
        return

    latest_migrated_version: str = migrated_versions_and_checksums[-1][0]

    run_migration_validations(
        latest_migrated_version=latest_migrated_version,
        skip_checksum_validation=True,
    )

    versions_and_checksums_to_repair: list[tuple[str, str]] = []

    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        end_version=latest_migrated_version,
    )

    for index, (file_version, filepath) in enumerate(
        migration_filepaths_by_version.items()
    ):
        sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
        checksum: str = calculate_checksum(sql_statements=sql_statements)

        # this should never be hit because of the validation check above
        if file_version != migrated_versions_and_checksums[index][0]:
            raise MigrationVersionMismatchError(
                f"Version mismatch123: expected {migrated_versions_and_checksums[index][0]}, found {file_version}."
            )

        if checksum != migrated_versions_and_checksums[index][1]:
            versions_and_checksums_to_repair.append(
                (
                    file_version,
                    checksum,
                )
            )

    if not versions_and_checksums_to_repair:
        print("All migration checksums are already valid - no drift detected.")
        return

    if audit_only:
        print("\nJETBASE - Checksum Audit Report")
        print("----------------------------------------")
        print("Changes detected in the following files:")
        for file_version, _ in versions_and_checksums_to_repair:
            print(f" → {file_version}")

    with migration_lock():
        update_migration_checksums(
            versions_and_checksums=versions_and_checksums_to_repair
        )
        for version, _ in versions_and_checksums_to_repair:
            print(f"Repaired checksum for version: {version}")
            print("Successfully repaired checksums")
