import re

from jetbase.constants import (
    DEFAULT_DELIMITER,
    RUNS_ALWAYS_FILE_PREFIX,
    RUNS_ON_CHANGE_FILE_PREFIX,
    VERSION_FILE_PREFIX,
)
from jetbase.enums import MigrationDirectionType
from jetbase.exceptions import (
    InvalidMigrationFilenameError,
    MigrationFilenameTooLongError,
)


def parse_upgrade_statements(file_path: str, dry_run: bool = False) -> list[str]:
    """
    Parse SQL statements from the upgrade section of a migration file.

    Reads the migration file and extracts all SQL statements that appear
    before the '-- rollback' marker. Statements are split on semicolons.

    Args:
        file_path (str): Path to the migration SQL file.
        dry_run (bool): If True, preserves formatting for display.
            If False, joins lines for execution. Defaults to False.

    Returns:
        list[str]: List of SQL statements.
    """
    delimiter: str = _extract_delimiter_from_file(file_path=file_path)

    statements = []
    current_statement = []

    with open(file_path, "r") as file:
        for line in file:
            if not dry_run:
                line = line.strip()
            else:
                line = line.rstrip()

            if (
                line.strip().startswith("--")
                and line[2:].strip().lower() == MigrationDirectionType.ROLLBACK.value
            ):
                break

            if not line or line.strip().startswith("--"):
                continue
            current_statement.append(line)

            if line.strip().endswith(delimiter):
                if not dry_run:
                    statement = " ".join(current_statement)
                else:
                    statement = "\n".join(current_statement)
                statement = statement.rstrip(delimiter).strip()
                if statement:
                    statements.append(statement)
                current_statement = []

    return statements


def parse_rollback_statements(file_path: str, dry_run: bool = False) -> list[str]:
    """
    Parse SQL statements from the rollback section of a migration file.

    Reads the migration file and extracts all SQL statements that appear
    after the '-- rollback' marker. Statements are split on semicolons.

    Args:
        file_path (str): Path to the migration SQL file.
        dry_run (bool): If True, preserves formatting for display.
            If False, joins lines for execution. Defaults to False.

    Returns:
        list[str]: List of SQL statements (without trailing semicolons).
    """
    delimiter: str = _extract_delimiter_from_file(file_path=file_path)
    statements = []
    current_statement = []
    in_rollback_section = False

    with open(file_path, "r") as file:
        for line in file:
            if not dry_run:
                line = line.strip()
            else:
                line = line.rstrip()

            if not in_rollback_section:
                if (
                    line.strip().startswith("--")
                    and line[2:].strip().lower()
                    == MigrationDirectionType.ROLLBACK.value
                ):
                    in_rollback_section = True
                else:
                    continue

            if in_rollback_section:
                if not line or line.strip().startswith("--"):
                    continue
                current_statement.append(line)

                if line.strip().endswith(delimiter):
                    if not dry_run:
                        statement = " ".join(current_statement)
                    else:
                        statement = "\n".join(current_statement)
                    statement = statement.rstrip(delimiter).strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []

    return statements


def _extract_delimiter_from_file(file_path: str) -> str:
    """
    Extract custom delimiter from a migration file if specified.

    Looks for a comment line in the format:
    -- jetbase: delimiter=<char>

    Args:
        file_path (str): Path to the migration SQL file.

    Returns:
        str: The custom delimiter if found, otherwise the default semicolon.
    """
    import re

    delimiter_pattern: re.Pattern[str] = re.compile(
        r"^--\s*jetbase:\s*delimiter=(.+)$", re.IGNORECASE
    )

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()
            match: re.Match[str] | None = delimiter_pattern.match(line)
            if match:
                return match.group(1).strip()
            # Stop looking after first non-comment, non-empty line
            if line and not line.startswith("--"):
                break

    return DEFAULT_DELIMITER


def is_filename_format_valid(filename: str) -> bool:
    """
    Check if filename follows the migration naming convention.

    Valid filenames must start with 'V', 'RA__', or 'ROC__', contain '__',
    end with '.sql', and have a non-empty description.

    Args:
        filename (str): The filename to validate.

    Returns:
        bool: True if the filename matches the convention, False otherwise.

    Example:
        >>> is_filename_format_valid("V1__init.sql")
        True
        >>> is_filename_format_valid("invalid.sql")
        False
    """
    if not filename.endswith(".sql"):
        return False
    if not filename.startswith(
        (VERSION_FILE_PREFIX, RUNS_ON_CHANGE_FILE_PREFIX, RUNS_ALWAYS_FILE_PREFIX)
    ):
        return False
    if "__" not in filename:
        return False
    description: str = _get_raw_description_from_filename(filename=filename)
    if len(description.strip()) == 0:
        return False
    if filename.startswith((RUNS_ON_CHANGE_FILE_PREFIX, RUNS_ALWAYS_FILE_PREFIX)):
        return True
    raw_version: str = _get_version_from_filename(filename=filename)
    if not is_valid_version(version=raw_version):
        return False
    return True


def get_description_from_filename(filename: str) -> str:
    """
    Extract and format the description from a migration filename.

    Extracts the portion after '__' and before '.sql', then replaces
    underscores with spaces for human-readable display.

    Args:
        filename (str): The migration filename to parse.

    Returns:
        str: Human-readable description with spaces.

    Example:
        >>> get_description_from_filename("V1__add_users.sql")
        'add users'
    """

    raw_description: str = _get_raw_description_from_filename(filename=filename)
    formatted_description: str = raw_description.replace("_", " ")
    return formatted_description


def is_filename_length_valid(filename: str, max_length: int = 512) -> bool:
    """
    Check if the filename length is within the allowed maximum.

    Args:
        filename (str): The filename to check.
        max_length (int): Maximum allowed character length. Defaults to 512.

    Returns:
        bool: True if the filename length is <= max_length.
    """
    return len(filename) <= max_length


def _get_version_from_filename(filename: str) -> str:
    """
    Extract the version string from a migration filename.

    Parses the portion between 'V' and '__' to get the raw version.

    Args:
        filename (str): The migration filename to parse.

    Returns:
        str: Raw version string (e.g., "1_2_0" from "V1_2_0__desc.sql").
    """

    version: str = filename[1 : filename.index("__")]
    return version


def _get_raw_description_from_filename(filename: str) -> str:
    """
    Extract the raw description from a migration filename.

    Returns the portion between '__' and '.sql' without any formatting.

    Args:
        filename (str): The migration filename to parse.

    Returns:
        str: Raw description with underscores preserved.
    """

    description: str = filename[
        filename.index("__") + 2 : filename.index(".sql")
    ].strip()
    return description


def is_valid_version(version: str) -> bool:
    """
    Validate that a version string follows the correct format.

    Valid versions contain digits separated by periods or underscores.
    Must start and end with a digit.

    Args:
        version (str): The version string to validate.

    Returns:
        bool: True if the version format is valid.

    Example:
        >>> is_valid_version("1.2.3")
        True
        >>> is_valid_version("1__2")
        False
    """
    if not version:
        return False

    # Pattern: starts with digit, ends with digit, can have periods/underscores between digits
    pattern = r"^\d+([._]\d+)*$"
    return bool(re.match(pattern, version))


def validate_filename_format(filename: str) -> None:
    """
    Validate filename format, raising an exception if invalid.

    Checks that the filename follows the migration naming convention
    and does not exceed the maximum length.

    Args:
        filename (str): The filename to validate.

    Returns:
        None: Returns silently if validation passes.

    Raises:
        InvalidMigrationFilenameError: If the filename doesn't match
            the required naming convention.
        MigrationFilenameTooLongError: If the filename exceeds 512 characters.
    """
    is_valid_filename: bool = True
    if not filename.endswith(".sql"):
        is_valid_filename = False
    if not filename.startswith(
        (VERSION_FILE_PREFIX, RUNS_ON_CHANGE_FILE_PREFIX, RUNS_ALWAYS_FILE_PREFIX)
    ):
        is_valid_filename = False
    if "__" not in filename:
        is_valid_filename = False
    description: str = _get_raw_description_from_filename(filename=filename)
    if len(description.strip()) == 0:
        is_valid_filename = False
    if filename.startswith(VERSION_FILE_PREFIX):
        raw_version: str = _get_version_from_filename(filename=filename)
        if not is_valid_version(version=raw_version):
            is_valid_filename = False

    if not is_valid_filename:
        raise InvalidMigrationFilenameError(
            f"Invalid migration filename format: {filename}.\n"
            "Filenames must start with 'V', followed by the version number, "
            "two underscores '__', a description, and end with '.sql'.\n"
            "V<version_number>__<my_description>.sql. "
            "Examples: 'V1_2_0__add_new_table.sql' or 'V1.2.0__add_new_table.sql'\n\n"
            "For repeatable migrations, filenames must start with 'RC' or 'RA', "
            "followed by two underscores '__', a description, and end with '.sql'.\n"
            "RC__<my_description>.sql or RA__<my_description>.sql."
        )

    _validate_filename_length(filename=filename)


def _validate_filename_length(filename: str, max_length: int = 512) -> None:
    """
    Validate that the filename does not exceed the maximum length.

    Args:
        filename (str): The filename to validate.
        max_length (int): Maximum allowed character length. Defaults to 512.

    Returns:
        None: Returns silently if validation passes.

    Raises:
        MigrationFilenameTooLongError: If the filename exceeds max_length.
    """
    if len(filename) > max_length:
        raise MigrationFilenameTooLongError(
            f"Migration filename too long: {filename}.\n"
            f"Filename is currently {len(filename)} characters.\n"
            "Filenames must not exceed 512 characters."
        )
