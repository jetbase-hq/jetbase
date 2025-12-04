import hashlib
import os

from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.exceptions import (
    DuplicateMigrationVersionError,
    MigrationChecksumMismatchError,
    MigrationVersionMismatchError,
    OutOfOrderMigrationError,
)


def calculate_checksum(sql_statements: list[str]) -> str:
    """
    Calculate a checksum for a list of SQL statements.

    Args:
        sql_statements (list[str]): The list of SQL statements to calculate the checksum for

    Returns:
        str: The hexadecimal checksum string

    Example:
        >>> calculate_checksum(["SELECT * FROM users", "INSERT INTO logs VALUES (1)"])
        'a1b2c3d4e5f6...'
    """
    formatted_sql_statements: str = "\n".join(sql_statements)

    checksum: str = hashlib.sha256(formatted_sql_statements.encode("utf-8")).hexdigest()

    return checksum


def validate_current_migration_files_match_checksums(
    migrated_filepaths_by_version: dict[str, str],
    migrated_versions_and_checksums: list[tuple[str, str]],
) -> None:
    """
    Validates that current migration files match their stored checksums.

    Args:
        migrated_filepaths_by_version: Dictionary mapping version strings to file paths
        migrated_versions_and_checksums: List of tuples containing version and checksum pairs

    Raises:
        MigrationVersionMismatchError: If version mismatch is detected
        MigrationChecksumMismatchError: If checksum doesn't match
    """
    for index, (file_version, filepath) in enumerate(
        migrated_filepaths_by_version.items()
    ):
        sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
        checksum: str = calculate_checksum(sql_statements=sql_statements)

        if file_version != migrated_versions_and_checksums[index][0]:
            raise MigrationVersionMismatchError(
                f"Version mismatch: expected {migrated_versions_and_checksums[index][0]}, found {file_version}."
            )

        if checksum != migrated_versions_and_checksums[index][1]:
            raise MigrationChecksumMismatchError(
                f"Checksum mismatch for version {file_version}: file has been changed since migration."
            )


def validate_migrated_versions_in_current_migration_files(
    migrated_versions: list[str],
    current_migration_filepaths_by_version: dict[str, str],
) -> None:
    """
    Validates that all migrated versions have corresponding migration files.

    This function checks that every version that has been previously migrated
    still has a corresponding migration file present in the current migration
    files directory.

    Args:
        migrated_versions: A list of version strings that have been previously
            migrated to the database.
        current_migration_filepaths_by_version: A dictionary mapping version
            strings to their corresponding migration file paths.

    Raises:
        FileNotFoundError: If a migrated version is not found in the current
            migration files, indicating that a migration file has been removed
            or is missing.
    """
    for migrated_version in migrated_versions:
        if migrated_version not in current_migration_filepaths_by_version:
            raise FileNotFoundError(
                f"Version {migrated_version} has been migrated but is missing from the current migration files."
            )


def validate_no_new_migration_files_with_lower_version_than_latest_migration(
    current_migration_filepaths_by_version: dict[str, str],
    migrated_versions: list[str],
    latest_migrated_version: str,
) -> None:
    """
    Validates that no new migration files have been added with a version lower than the latest migrated version.
    Args:
        current_migration_filepaths_by_version: Dictionary mapping version strings to file paths
        migrated_versions: List of versions that have already been migrated
        latest_migrated_version: The most recent version that has been migrated
    Raises:
        ValueError: If a new migration file has a version lower than the latest migrated version
    """
    for file_version, filepath in current_migration_filepaths_by_version.items():
        if (
            file_version < latest_migrated_version
            and file_version not in migrated_versions
        ):
            filename: str = os.path.basename(filepath)
            raise OutOfOrderMigrationError(
                f"{filename} has version {file_version} which is lower than the latest migrated version {latest_migrated_version}.\n"
                "New migration files cannot have versions lower than the latest migrated version.\n"
                f"Please rename the file to have a version higher than {latest_migrated_version}.\n"
            )


def validate_no_duplicate_migration_file_versions(
    current_migration_filepaths_by_version: dict[str, str],
) -> None:
    """
    Validates that there are no duplicate migration file versions in the provided dictionary.

    Args:
        current_migration_filepaths_by_version (dict[str, str]): A dictionary mapping migration
            file versions (as strings) to their corresponding file paths.

    Raises:
        DuplicateMigrationVersionError: If a duplicate migration file version is detected. The error message includes
            the duplicate version number converted to a readable format.
    """
    seen_versions: set[str] = set()
    for file_version in current_migration_filepaths_by_version.keys():
        if file_version in seen_versions:
            raise DuplicateMigrationVersionError(
                f"Duplicate migration version detected: {file_version}.\n"
                "Each file must have a unique version.\n"
                "Please rename the file to have a unique version."
            )
        seen_versions.add(file_version)
