import datetime as dt
import os

from jetbase.constants import MIGRATIONS_DIR, NEW_MIGRATION_FILE_CONTENT
from jetbase.exceptions import DirectoryNotFoundError
from jetbase.engine.file_parser import is_valid_version, is_filename_length_valid
from jetbase.exceptions import MigrationFilenameTooLongError, InvalidVersionError


def generate_new_migration_file_cmd(
    description: str, version: str | None = None
) -> None:
    """
    Generate a new migration file with a timestamped filename.

    Creates a new SQL migration file in the migrations directory with a
    filename format of V{timestamp}__{description}.sql. The file contains
    template sections for upgrade and rollback SQL statements.

    Args:
        description (str): A human-readable description for the migration.
            Spaces will be replaced with underscores in the filename.
        version (str | None): The version of the migration.
            If not provided, a timestamp will be used.

    Returns:
        None: Prints the created filename to stdout.

    Raises:
        DirectoryNotFoundError: If the migrations directory does not exist.

    Example:
        >>> generate_new_migration_file_cmd("create users table", version="1")
        Created migration file: V1__create_users_table.sql
        >>> generate_new_migration_file_cmd("create users table")
        Created migration file: V20251201.120000__create_users_table.sql
    """

    migrations_dir_path: str = os.path.join(os.getcwd(), MIGRATIONS_DIR)

    if not os.path.exists(migrations_dir_path):
        raise DirectoryNotFoundError(
            "Migrations directory not found. Run 'jetbase initialize' to set up jetbase.\n"
            "If you have already done so, run this command from the jetbase directory."
        )

    filename: str = _generate_new_filename(description=description, version=version)
    filepath: str = os.path.join(migrations_dir_path, filename)

    with open(filepath, "w") as f:  # noqa: F841
        f.write(NEW_MIGRATION_FILE_CONTENT)
    print(f"Created migration file: {filename}")


def _generate_new_filename(description: str, version: str | None = None) -> str:
    """
    Generate a timestamped filename for a migration.

    Creates a filename using the current timestamp in YYYYMMDD.HHMMSS format
    followed by the description with spaces converted to underscores.

    Args:
        description (str): A human-readable description for the migration.
        version (str | None): The version of the migration.
            If not provided, a timestamp will be used.

    Returns:
        str: Formatted filename like "V1__description.sql" or "V20251201.120000__description.sql".

    Example:
        >>> _generate_new_filename("add users", version="1")
        'V1__add_users.sql'
        >>> _generate_new_filename("add users")
        'V20251201.120000__add_users.sql'
    """
    if version is None:
        version = dt.datetime.now().strftime("%Y%m%d.%H%M%S")
    else:
        if not is_valid_version(version):
            raise InvalidVersionError(
                f"""
            Invalid version: {version}.
            Version must be integer(s) that are separated by periods or underscores.
            Examples: "1", "1.5", "1_5"
            """
            )

    filename: str = f"V{version}__{description.replace(' ', '_')}.sql"
    if not is_filename_length_valid(filename=filename):
        raise MigrationFilenameTooLongError(
            """
            Migration filename too long.
            Filename must not exceed 512 characters.
            """
        )
    return filename
