import os

from packaging.version import parse as parse_version

from jetbase.constants import (
    VERSION_FILE_PREFIX,
)
from jetbase.engine.file_parser import (
    is_filename_format_valid,
    is_filename_length_valid,
)
from jetbase.exceptions import (
    DuplicateMigrationVersionError,
    InvalidMigrationFilenameError,
    MigrationFilenameTooLongError,
)


def _get_version_key_from_filename(filename: str) -> str:
    """
    Extract and normalize the version key from a migration filename.

    Parses the version portion between 'V' and '__', then normalizes
    underscores to periods for consistent version comparison.

    Args:
        filename (str): The migration filename to parse.

    Returns:
        str: Normalized version string with periods as separators.

    Raises:
        ValueError: If the filename doesn't follow the expected format.

    Example:
        >>> _get_version_key_from_filename("V1_2__desc.sql")
        '1.2'
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
    Get versioned migration file paths sorted by version number.

    Scans the directory for SQL migration files, validates their format,
    and returns a dictionary mapping version strings to file paths.
    Results can be filtered by version range.

    Args:
        directory (str): Path to the migrations directory to scan.
        version_to_start_from (str | None): Minimum version to include
            (inclusive). If provided, only files with versions >= this
            are returned. Defaults to None.
        end_version (str | None): Maximum version to include (inclusive).
            If provided, only files with versions <= this are returned.
            Defaults to None.

    Returns:
        dict[str, str]: Dictionary mapping normalized version strings
            to their absolute file paths, sorted by version number.

    Raises:
        InvalidMigrationFilenameError: If a file has an invalid format.
        MigrationFilenameTooLongError: If a filename exceeds 512 characters.
        DuplicateMigrationVersionError: If duplicate versions are detected.

    Example:
        >>> get_migration_filepaths_by_version('/migrations')
        {'1.0': '/migrations/V1__init.sql', '1.1': '/migrations/V1_1__add.sql'}
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
