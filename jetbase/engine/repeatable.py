import os

from jetbase.constants import RUNS_ALWAYS_FILE_PREFIX, RUNS_ON_CHANGE_FILE_PREFIX
from jetbase.engine.checksum import calculate_checksum
from jetbase.engine.file_parser import (
    parse_upgrade_statements,
    validate_filename_format,
)
from jetbase.repositories.migrations_repo import (
    get_existing_on_change_filenames_to_checksums,
)


def get_repeatable_always_filepaths(directory: str) -> list[str]:
    """
    Get file paths for all runs-always (RA__) migrations in a directory.

    Scans the directory for migration files starting with the RA__ prefix
    and validates their filename format.

    Args:
        directory (str): Path to the migrations directory to scan.

    Returns:
        list[str]: Sorted list of absolute file paths for RA__ migrations.

    Raises:
        InvalidMigrationFilenameError: If any file has an invalid format.
        MigrationFilenameTooLongError: If any filename exceeds 512 characters.
    """
    repeatable_always_filepaths: list[str] = []
    for root, _, files in os.walk(directory):
        for filename in files:
            validate_filename_format(filename=filename)
            if filename.startswith(RUNS_ALWAYS_FILE_PREFIX):
                filepath: str = os.path.join(root, filename)
                repeatable_always_filepaths.append(filepath)

    repeatable_always_filepaths.sort()
    return repeatable_always_filepaths


def get_runs_on_change_filepaths(
    directory: str, changed_only: bool = False
) -> list[str]:
    """
    Get file paths for runs-on-change (ROC__) migrations in a directory.

    Scans the directory for migration files starting with the ROC__ prefix.
    Optionally filters to only include files whose checksums have changed
    since they were last applied.

    Args:
        directory (str): Path to the migrations directory to scan.
        changed_only (bool): If True, only returns files that have been
            modified since last migration. Defaults to False.

    Returns:
        list[str]: Sorted list of absolute file paths for ROC__ migrations.

    Raises:
        InvalidMigrationFilenameError: If any file has an invalid format.
        MigrationFilenameTooLongError: If any filename exceeds 512 characters.
    """
    runs_on_change_filepaths: list[str] = []
    for root, _, files in os.walk(directory):
        for filename in files:
            validate_filename_format(filename=filename)
            if filename.startswith(RUNS_ON_CHANGE_FILE_PREFIX):
                filepath: str = os.path.join(root, filename)
                runs_on_change_filepaths.append(filepath)

    if runs_on_change_filepaths and changed_only:
        existing_on_change_migrations: dict[str, str] = (
            get_existing_on_change_filenames_to_checksums()
        )

        for filepath in runs_on_change_filepaths.copy():
            filename: str = os.path.basename(filepath)
            sql_statements: list[str] = parse_upgrade_statements(file_path=filepath)
            checksum: str = calculate_checksum(sql_statements=sql_statements)

            if existing_on_change_migrations.get(filename) == checksum:
                runs_on_change_filepaths.remove(filepath)

    runs_on_change_filepaths.sort()
    return runs_on_change_filepaths


def get_ra_filenames() -> list[str]:
    """
    Get all runs-always (RA__) migration filenames from the migrations directory.

    Scans the 'migrations' subdirectory in the current working directory
    for files starting with the RA__ prefix.

    Returns:
        list[str]: List of RA__ migration filenames (not full paths).
    """
    ra_filenames: list[str] = []
    for root, _, files in os.walk(os.path.join(os.getcwd(), "migrations")):
        for filename in files:
            if filename.startswith(RUNS_ALWAYS_FILE_PREFIX):
                ra_filenames.append(filename)
    return ra_filenames


def get_repeatable_filenames() -> list[str]:
    """
    Get all repeatable migration filenames from the migrations directory.

    Scans the 'migrations' subdirectory in the current working directory
    for files starting with either RA__ or ROC__ prefix.

    Returns:
        list[str]: List of all repeatable migration filenames (not full paths).
    """
    repeatable_filenames: list[str] = []
    for root, _, files in os.walk(os.path.join(os.getcwd(), "migrations")):
        for filename in files:
            if filename.startswith(RUNS_ALWAYS_FILE_PREFIX) or filename.startswith(
                RUNS_ON_CHANGE_FILE_PREFIX
            ):
                repeatable_filenames.append(filename)
    return repeatable_filenames
