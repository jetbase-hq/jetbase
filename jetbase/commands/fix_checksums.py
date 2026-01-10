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
    Fix or audit checksums for applied migrations.

    Compares the checksums stored in the database against the current checksums
    of migration files on disk. Detects drift where files have been modified
    after being applied to the database.

    Args:
        audit_only (bool): If True, only reports checksum mismatches without
            making any changes to the database. If False, updates the stored
            checksums to match the current file contents. Defaults to False.

    Returns:
        None: Prints audit report or repair status to stdout.

    Raises:
        MigrationVersionMismatchError: If there is a mismatch between expected
            and actual migration versions during processing.
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

    versions_and_checksums_to_repair: list[tuple[str, str]] = _find_checksum_mismatches(
        migrated_versions_and_checksums=migrated_versions_and_checksums,
        latest_migrated_version=latest_migrated_version,
    )

    if not versions_and_checksums_to_repair:
        print(
            "All migration checksums are valid - no altered upgrade statments detected."
        )
        return

    if audit_only:
        _print_audit_report(
            versions_and_checksums_to_repair=versions_and_checksums_to_repair
        )
        return

    _repair_checksums(versions_and_checksums_to_repair=versions_and_checksums_to_repair)


def _print_audit_report(
    versions_and_checksums_to_repair: list[tuple[str, str]],
) -> None:
    """
    Print a formatted report of migrations with checksum drift.

    Outputs a list of migration versions whose file contents have changed
    since they were originally applied to the database.

    Args:
        versions_and_checksums_to_repair (list[tuple[str, str]]): List of tuples
            containing (version, new_checksum) for migrations with detected drift.

    Returns:
        None: Prints the audit report to stdout.
    """
    print("\nJETBASE - Checksum Audit Report")
    print("----------------------------------------")
    print("Changes detected in the following files:")
    for file_version, _ in versions_and_checksums_to_repair:
        print(f" → {file_version}")


def _repair_checksums(versions_and_checksums_to_repair: list[tuple[str, str]]) -> None:
    """
    Update checksums in the database for migrations with detected drift.

    Acquires a migration lock and updates the stored checksums in the
    jetbase_migrations table to match the current file contents.

    Args:
        versions_and_checksums_to_repair (list[tuple[str, str]]): List of tuples
            containing (version, new_checksum) for migrations to update.

    Returns:
        None: Prints repair status for each version to stdout.
    """
    with migration_lock():
        update_migration_checksums(
            versions_and_checksums=versions_and_checksums_to_repair
        )
        for version, _ in versions_and_checksums_to_repair:
            print(f"Repaired checksum for version: {version}")

    print("Successfully repaired checksums")


def _find_checksum_mismatches(
    migrated_versions_and_checksums: list[tuple[str, str]], latest_migrated_version: str
) -> list[tuple[str, str]]:
    """
    Find migrations where the file checksum differs from the stored checksum.

    Compares the current checksum of each migration file against the checksum
    stored in the database when the migration was originally applied.

    Args:
        migrated_versions_and_checksums (list[tuple[str, str]]): List of tuples
            containing (version, stored_checksum) from the database.
        latest_migrated_version (str): The most recent version that has been
            migrated, used to limit the scope of files checked.

    Returns:
        list[tuple[str, str]]: List of (version, new_checksum) tuples for
            migrations where the file has changed since being applied.

    Raises:
        MigrationVersionMismatchError: If the file versions do not match the
            expected sequence of migrated versions.

    Example:
        >>> _find_checksum_mismatches([("1.0", "abc123")], "1.0")
        [("1.0", "def456")]  # If file changed
    """
    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), MIGRATIONS_DIR),
        end_version=latest_migrated_version,
    )

    db_checksums_by_version: dict[str, str] = dict(migrated_versions_and_checksums)

    versions_and_checksums_to_repair: list[tuple[str, str]] = []

    for file_version, filepath in migration_filepaths_by_version.items():
        # this should never be hit because of the validation check above
        if file_version not in db_checksums_by_version:
            raise MigrationVersionMismatchError(
                f"Version {file_version} found in files but not in database."
            )

        sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
        checksum: str = calculate_checksum(sql_statements=sql_statements)

        if checksum != db_checksums_by_version[file_version]:
            versions_and_checksums_to_repair.append(
                (
                    file_version,
                    checksum,
                )
            )

    return versions_and_checksums_to_repair
