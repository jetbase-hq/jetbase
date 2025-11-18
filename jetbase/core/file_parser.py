import re

from jetbase.enums import MigrationOperationType


def parse_upgrade_statements(file_path: str) -> list[str]:
    statements = []
    current_statement = []

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if (
                line.startswith("--")
                and line[2:].strip().lower() == MigrationOperationType.ROLLBACK.value
            ):
                break

            if not line or line.startswith("--"):
                continue
            current_statement.append(line)

            if line.endswith(";"):
                statement = " ".join(current_statement)
                statement = statement.rstrip(";").strip()
                if statement:
                    statements.append(statement)
                current_statement = []

    return statements


def parse_rollback_statements(file_path: str) -> list[str]:
    statements = []
    current_statement = []
    in_rollback_section = False

    with open(file_path, "r") as file:
        for line in file:
            line = line.strip()

            if not in_rollback_section:
                if (
                    line.startswith("--")
                    and line[2:].strip().lower()
                    == MigrationOperationType.ROLLBACK.value
                ):
                    in_rollback_section = True
                else:
                    continue

            if in_rollback_section:
                if not line or line.startswith("--"):
                    continue
                current_statement.append(line)

                if line.endswith(";"):
                    statement = " ".join(current_statement)
                    statement = statement.rstrip(";").strip()
                    if statement:
                        statements.append(statement)
                    current_statement = []

    return statements


def is_valid_filename(filename: str) -> bool:
    """
    Validates if a filename follows the expected migration file naming convention.
    A valid filename must:
    - Start with "V"
    - Have a valid version number following "V"
    - Contain "__" (double underscore)
    - End with ".sql"
    - Have a valid version number extractable from the filename
    Args:
        filename (str): The filename to validate.
    Returns:
        bool: True if the filename meets all validation criteria, False otherwise.
    Example:
        >>> is_valid_filename("V1__initial_migration.sql")
        True
        >>> is_valid_filename("migration.sql")
        False
    """
    if not filename.endswith(".sql"):
        return False
    if not filename.startswith("V"):
        return False
    if "__" not in filename:
        return False
    description: str = _get_description_from_filename(filename=filename)
    if len(description.strip()) == 0:
        return False
    raw_version: str = _get_version_from_filename(filename=filename)
    if not _is_valid_version(version=raw_version):
        return False
    return True


def _get_version_from_filename(filename: str) -> str:
    """
    Extract the version string from a migration filename.

    Args:
        filename: The migration filename (e.g., "V1_2_0__add_feature.sql")

    Returns:
        str: The extracted version string (e.g., "1_2_0")
    """

    version: str = filename[1 : filename.index("__")]
    return version


def _get_description_from_filename(filename: str) -> str:
    """
    Extract the description string from a migration filename.

    Args:
        filename: The migration filename (e.g., "V1_2_0__add_feature.sql")

    Returns:
        str: The extracted description string (e.g., "add_feature")
    """

    description: str = filename[
        filename.index("__") + 2 : filename.index(".sql")
    ].strip()
    return description


def _is_valid_version(version: str) -> bool:
    """
    Validate that a version string follows the correct format.

    Rules:
    - Must start and end with a number
    - Can be any length (1 or greater)
    - Can contain periods (.) or underscores (_) between numbers

    Valid examples: "1", "1.2", "1_2", "1.2.3", "1_2_3", "10.20.30"
    Invalid examples: ".1", "1.", "_1", "1_", "1..2", "1__2", "abc", ""

    Args:
        version: The version string to validate

    Returns:
        bool: True if version is valid, False otherwise
    """
    if not version:
        return False

    # Pattern: starts with digit, ends with digit, can have periods/underscores between digits
    pattern = r"^\d+([._]\d+)*$"
    return bool(re.match(pattern, version))
