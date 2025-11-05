import os


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


def _convert_version_tuple_to_str(version_tuple: tuple[str, ...]) -> str:
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


def get_versions(
    directory: str,
    version_to_start_from: str | None = None,
    end_version: str | None = None,
) -> dict[str, str]:
    """
    Retrieves SQL files from the specified directory and organizes them by version.
    This function walks through the directory tree, collects all SQL files, and creates a dictionary
    mapping version strings to file paths. Files can be filtered to only include versions greater
    than a specified starting version.
    Args:
        directory: The directory path to search for SQL files
        version_to_start_from: Optional version string to filter results, only returning
                              versions greater than this value
        end_version: Optional version string to filter results, only returning
                     versions less than this value
    Returns:
        A dictionary mapping version strings to file paths, sorted by version number
    Example:
        >>> get_versions('/path/to/sql/files')
        {'1.0.0': '/path/to/sql/files/v1_0_0__description.sql', '1.2.0': '/path/to/sql/files/v1_2_0__description.sql'}
    """
    version_to_filepath_dict: dict[str, str] = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".sql"):
                file_path: str = os.path.join(root, file)
                version: str = _get_version_key_from_filename(filename=file)
                version_tuple: tuple[str, ...] = convert_version_to_tuple(
                    version=version
                )
                if end_version:
                    if version_tuple > convert_version_to_tuple(version=end_version):
                        continue
                if version_to_start_from:
                    if version_tuple >= convert_version_to_tuple(
                        version=version_to_start_from
                    ):
                        version_to_filepath_dict[
                            _convert_version_tuple_to_str(version_tuple=version_tuple)
                        ] = file_path
                else:
                    version_to_filepath_dict[
                        _convert_version_tuple_to_str(version_tuple=version_tuple)
                    ] = file_path
    ordered_version_to_filepath_dict: dict[str, str] = {
        version: version_to_filepath_dict[version]
        for version in sorted(version_to_filepath_dict.keys())
    }

    return ordered_version_to_filepath_dict
