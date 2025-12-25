import os

from packaging.version import parse as parse_version

from jetbase.constants import (
    RUNS_ALWAYS_FILE_PREFIX,
    RUNS_ON_CHANGE_FILE_PREFIX,
    VERSION_FILE_PREFIX,
)
from jetbase.core.file_parser import is_filename_format_valid, is_filename_length_valid
from jetbase.exceptions import (
    DuplicateMigrationVersionError,
    InvalidMigrationFilenameError,
    MigrationFilenameTooLongError,
)


def _get_version_key_from_filename(filename: str) -> str:
    """
    Extract and normalize version key from a filename.

    The function extracts the version part from a filename that follows the format:
    'V{version}__{description}.sql' where version can be like '1', '1_1', or '1.1'.

    Args:
        filename (str): The filename to extract version from.
            Must follow pattern like 'V1__description.sql' or 'V1_1__description.sql'

    Returns:
        str: Normalized version string where underscores are replaced with periods.

    Raises:
        ValueError: If the filename doesn't follow the expected format.

    Examples:
        >>> _get_version_key_from_filename("V1__my_description.sql")
        '1'
        >>> _get_version_key_from_filename("V1_1__my_description.sql")
        '1.1'
        >>> _get_version_key_from_filename("V1.1__my_description.sql")
        '1.1'
    """
    try:
        version = filename.split("__")[0][1:]
    except Exception:
        raise (
            ValueError(
                "Filename must be in the following format: V1__my_description.sql, V1_1__my_description.sql, V1.1__my_description.sql"
            )
        )
    return version.replace("_", ".")


def get_migration_filepaths_by_version(
    directory: str,
    version_to_start_from: str | None = None,
    end_version: str | None = None,
) -> dict[str, str]:
    """
    Retrieve migration file paths organized by version number.

    Walks through the specified directory to find SQL migration files and creates
    a dictionary mapping version strings to their file paths. Files are validated
    for proper naming format and length. Results can be filtered by version range.

    Args:
        directory (str): The directory path to search for SQL migration files.
        version_to_start_from (str | None): Optional minimum version (inclusive).
            Only files with versions >= this value are included. Defaults to None.
        end_version (str | None): Optional maximum version (exclusive).
            Only files with versions < this value are included. Defaults to None.

    Returns:
        dict[str, str]: Dictionary mapping version strings to file paths,
            sorted in ascending order by version number.

    Raises:
        InvalidMigrationFilenameError: If a filename doesn't match the required format.
        MigrationFilenameTooLongError: If a filename exceeds the maximum length of 512 characters.
        DuplicateMigrationVersionError: If duplicate migration versions are detected.

    Example:
        >>> get_migration_filepaths_by_version('/path/to/migrations')
        {'1.0.0': '/path/to/migrations/V1_0_0__init.sql',
         '1.2.0': '/path/to/migrations/V1_2_0__add_users.sql'}
        >>> get_migration_filepaths_by_version('/path/to/migrations', version_to_start_from='1.1.0')
        {'1.2.0': '/path/to/migrations/V1_2_0__add_users.sql'}
    """
    version_to_filepath_dict: dict[str, str] = {}
    seen_versions: set[str] = set()

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".sql") and not is_filename_format_valid(
                filename=filename
            ):
                raise InvalidMigrationFilenameError(
                    f"Invalid migration filename format: {filename}.\n"
                    "Filenames must start with 'V', followed by the version number, "
                    "two underscores '__', a description, and end with '.sql'.\n"
                    "V<version_number>__<my_description>.sql. "
                    "Examples: 'V1_2_0__add_new_table.sql' or 'V1.2.0__add_new_table.sql'\n"
                )

            if filename.endswith(".sql") and not is_filename_length_valid(
                filename=filename
            ):
                raise MigrationFilenameTooLongError(
                    f"Migration filename too long: {filename}.\n"
                    f"Filename is currently {len(filename)} characters.\n"
                    "Filenames must not exceed 512 characters."
                )

            if is_filename_format_valid(filename=filename):
                if filename.startswith(VERSION_FILE_PREFIX):
                    file_path: str = os.path.join(root, filename)
                    file_version: str = _get_version_key_from_filename(
                        filename=filename
                    )

                    if file_version in seen_versions:
                        raise DuplicateMigrationVersionError(
                            f"Duplicate migration version detected: {file_version}.\n"
                            "Each file must have a unique version.\n"
                            "Please rename the file to have a unique version."
                        )
                    seen_versions.add(file_version)

                    if end_version:
                        if parse_version(file_version) > parse_version(end_version):
                            continue

                    if version_to_start_from:
                        if parse_version(file_version) >= parse_version(
                            version_to_start_from
                        ):
                            version_to_filepath_dict[file_version] = file_path

                    else:
                        version_to_filepath_dict[file_version] = file_path

    ordered_version_to_filepath_dict: dict[str, str] = dict(
        sorted(
            version_to_filepath_dict.items(),
            key=lambda item: parse_version(item[0]),
        )
    )

    return ordered_version_to_filepath_dict


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
