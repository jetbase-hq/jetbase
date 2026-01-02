import os

from packaging.version import parse as parse_version

from jetbase.config import get_config
from jetbase.constants import MIGRATIONS_DIR
from jetbase.engine.checksum import calculate_checksum
from jetbase.engine.file_parser import parse_upgrade_statements
from jetbase.engine.repeatable import get_repeatable_filenames
from jetbase.engine.version import (
    get_migration_filepaths_by_version,
)
from jetbase.exceptions import (
    ChecksumMismatchError,
    OutOfOrderMigrationError,
)
from jetbase.repositories.migrations_repo import (
    fetch_repeatable_migrations,
    get_checksums_by_version,
    get_migrated_versions,
)


def validate_current_migration_files_match_checksums(
    migrated_filepaths_by_version: dict[str, str],
    migrated_versions_and_checksums: list[tuple[str, str]],
) -> None:
    """
    Validate that migration files have not been modified since being applied.

    Compares the current checksum of each migration file against the
    checksum stored in the database when the migration was applied.

    Args:
        migrated_filepaths_by_version (dict[str, str]): Mapping of version
            strings to file paths for migrations to check.
        migrated_versions_and_checksums (list[tuple[str, str]]): List of
            (version, checksum) tuples from the database.

    Returns:
        None: Returns silently if all checksums match.

    Raises:
        ChecksumMismatchError: If any migration file's current checksum
            differs from its stored checksum.
    """
    versions_changed: list[str] = []
    for index, (file_version, filepath) in enumerate(
        migrated_filepaths_by_version.items()
    ):
        sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
        checksum: str = calculate_checksum(sql_statements=sql_statements)

        for migrated_version, migrated_checksum in migrated_versions_and_checksums:
            if file_version == migrated_version:
                if checksum != migrated_checksum:
                    versions_changed.append(file_version)

        if versions_changed:
            raise ChecksumMismatchError(
                f"Checksum mismatch for versions: {', '.join(versions_changed)}. Files have been changed since migration."
            )


def validate_migrated_versions_in_current_migration_files(
    migrated_versions: list[str],
    current_migration_filepaths_by_version: dict[str, str],
) -> None:
    """
    Ensure all migrated versions have corresponding migration files.

    Verifies that every version recorded in the database still has
    its migration file present in the migrations directory.

    Args:
        migrated_versions (list[str]): List of version strings that have
            been applied to the database.
        current_migration_filepaths_by_version (dict[str, str]): Mapping
            of version strings to file paths for existing files.

    Returns:
        None: Returns silently if all files are present.

    Raises:
        FileNotFoundError: If any migrated version is missing its file.
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
    Ensure no new migration files have versions lower than the latest applied.

    Prevents out-of-order migrations by checking that all new migration
    files have version numbers higher than the most recently applied version.

    Args:
        current_migration_filepaths_by_version (dict[str, str]): Mapping
            of version strings to file paths for all migration files.
        migrated_versions (list[str]): List of versions already applied.
        latest_migrated_version (str): The most recently applied version.

    Returns:
        None: Returns silently if validation passes.

    Raises:
        OutOfOrderMigrationError: If a new migration file has a version
            lower than the latest migrated version.
    """
    for file_version, filepath in current_migration_filepaths_by_version.items():
        if (
            parse_version(file_version) < parse_version(latest_migrated_version)
            and file_version not in migrated_versions
        ):
            filename: str = os.path.basename(filepath)
            raise OutOfOrderMigrationError(
                f"{filename} has version {file_version} which is lower than the latest migrated version {latest_migrated_version}.\n"
                "New migration files cannot have versions lower than the latest migrated version.\n"
                f"Please rename the file to have a version higher than {latest_migrated_version}.\n"
            )


def validate_migrated_repeatable_versions_in_migration_files(
    migrated_repeatable_filenames: list[str],
    all_repeatable_filenames: list[str],
) -> None:
    """
    Ensure all migrated repeatable migrations have corresponding files.

    Verifies that every repeatable migration recorded in the database
    still has its file present in the migrations directory.

    Args:
        migrated_repeatable_filenames (list[str]): List of repeatable
            migration filenames from the database.
        all_repeatable_filenames (list[str]): List of all repeatable
            migration filenames currently in the migrations directory.

    Returns:
        None: Returns silently if all files are present.

    Raises:
        FileNotFoundError: If any migrated repeatable file is missing.
    """
    missing_filenames: list[str] = []
    for r_file in migrated_repeatable_filenames:
        if r_file not in all_repeatable_filenames:
            missing_filenames.append(r_file)
    if missing_filenames:
        raise FileNotFoundError(
            f"The following migrated repeatable files are missing: {', '.join(missing_filenames)}"
        )


def run_migration_validations(
    latest_migrated_version: str,
    skip_validation: bool = False,
    skip_checksum_validation: bool = False,
    skip_file_validation: bool = False,
) -> None:
    """
    Run all migration validations before performing an upgrade.

    Executes validation checks including duplicate version detection,
    file presence verification, out-of-order detection, and checksum
    validation. Validations can be skipped via parameters or config.

    Args:
        latest_migrated_version (str): The most recently applied version,
            used to check for out-of-order migrations.
        skip_validation (bool): If True, skips all validations except
            duplicate version check. Defaults to False.
        skip_checksum_validation (bool): If True, skips checksum validation.
            Defaults to False.
        skip_file_validation (bool): If True, skips file presence and
            out-of-order validations. Defaults to False.

    Returns:
        None: Returns silently if all validations pass.

    Raises:
        DuplicateMigrationVersionError: If duplicate versions are found.
        FileNotFoundError: If migration files are missing.
        OutOfOrderMigrationError: If out-of-order migrations are detected.
        ChecksumMismatchError: If file checksums don't match stored values.
    """

    skip_validation_config: bool = get_config().skip_validation
    skip_checksum_validation_config: bool = get_config().skip_checksum_validation
    skip_file_validation_config: bool = get_config().skip_file_validation

    migrations_directory_path: str = os.path.join(os.getcwd(), MIGRATIONS_DIR)

    migration_filepaths_by_version: dict[str, str] = get_migration_filepaths_by_version(
        directory=migrations_directory_path
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
                migrated_repeatable_filenames=[
                    r.filename for r in fetch_repeatable_migrations()
                ],
                all_repeatable_filenames=get_repeatable_filenames(),
            )

        migrated_filepaths_by_version: dict[str, str] = (
            get_migration_filepaths_by_version(
                directory=migrations_directory_path, end_version=latest_migrated_version
            )
        )

        if not skip_checksum_validation and not skip_checksum_validation_config:
            validate_current_migration_files_match_checksums(
                migrated_filepaths_by_version=migrated_filepaths_by_version,
                migrated_versions_and_checksums=get_checksums_by_version(),
            )
