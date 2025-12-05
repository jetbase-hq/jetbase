import os

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


def convert_version_tuple_to_version(version_tuple: tuple[str, ...]) -> str:
    """
    Convert a version tuple to a string representation.

    Args:
        version_tuple (tuple[str, ...]): A tuple containing version components as strings.

    Returns:
        str: A string representation of the version, with components joined by periods.

    Example:
        >>> _convert_version_tuple_to_str(('1', '2', '3'))
        '1.2.3'
    """
    return ".".join(version_tuple)


def convert_version_to_tuple(version: str) -> tuple[str, ...]:
    """
    Convert a version string to a tuple of version components.

    Args:
        version_str (str): A version string with components separated by periods.

    Returns:
        tuple[str, ...]: A tuple containing the version components as strings.

    Example:
        >>> convert_version_to_tuple("1.2.3")
        ('1', '2', '3')
    """
    return tuple(version.split("."))


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
    seen_versions: set[tuple[str, ...]] = set()

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
                file_path: str = os.path.join(root, filename)
                version: str = _get_version_key_from_filename(filename=filename)
                version_tuple: tuple[str, ...] = convert_version_to_tuple(
                    version=version
                )

                if version_tuple in seen_versions:
                    raise DuplicateMigrationVersionError(
                        f"Duplicate migration version detected: {convert_version_tuple_to_version(version_tuple)}.\n"
                        "Each file must have a unique version.\n"
                        "Please rename the file to have a unique version."
                    )
                seen_versions.add(version_tuple)

                if end_version:
                    if version_tuple > convert_version_to_tuple(version=end_version):
                        continue

                if version_to_start_from:
                    if version_tuple >= convert_version_to_tuple(
                        version=version_to_start_from
                    ):
                        version_to_filepath_dict[
                            convert_version_tuple_to_version(
                                version_tuple=version_tuple
                            )
                        ] = file_path

                else:
                    version_to_filepath_dict[
                        convert_version_tuple_to_version(version_tuple=version_tuple)
                    ] = file_path

    ordered_version_to_filepath_dict: dict[str, str] = {
        version: version_to_filepath_dict[version]
        for version in sorted(version_to_filepath_dict.keys())
    }

    return ordered_version_to_filepath_dict
