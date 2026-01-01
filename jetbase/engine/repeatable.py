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
    Retrieve all Repeatable Always (RA) migration filenames from the migrations directory.

    This function scans the 'migrations' directory in the current working directory
    for files that follow the Repeatable Always naming convention (starting with 'RA__').
    It returns a list of these filenames.

    Returns:
        list[str]: A list of Repeatable Always migration filenames.
    """
    ra_filenames: list[str] = []
    for root, _, files in os.walk(os.path.join(os.getcwd(), "migrations")):
        for filename in files:
            if filename.startswith(RUNS_ALWAYS_FILE_PREFIX):
                ra_filenames.append(filename)
    return ra_filenames


def get_repeatable_filenames() -> list[str]:
    """
    Retrieve all Repeatable migration filenames from the migrations directory.

    This function scans the 'migrations' directory in the current working directory
    for files that follow the Repeatable naming convention (starting with 'RA__' or 'RC__').
    It returns a list of these filenames.

    Returns:
        list[str]: A list of Repeatable migration filenames.
    """
    repeatable_filenames: list[str] = []
    for root, _, files in os.walk(os.path.join(os.getcwd(), "migrations")):
        for filename in files:
            if filename.startswith(RUNS_ALWAYS_FILE_PREFIX) or filename.startswith(
                RUNS_ON_CHANGE_FILE_PREFIX
            ):
                repeatable_filenames.append(filename)
    return repeatable_filenames
