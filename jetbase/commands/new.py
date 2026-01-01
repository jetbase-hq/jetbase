import datetime as dt
import os

from jetbase.constants import MIGRATIONS_DIR, NEW_MIGRATION_FILE_CONTENT
from jetbase.exceptions import DirectoryNotFoundError


def generate_new_migration_file_cmd(description: str) -> None:
    """
    Generate a new migration file with a timestamped filename.

    Creates a new SQL migration file in the migrations directory with a
    filename format of V{timestamp}__{description}.sql. The file contains
    template sections for upgrade and rollback SQL statements.

    Args:
        description (str): A human-readable description for the migration.
            Spaces will be replaced with underscores in the filename.

    Returns:
        None: Prints the created filename to stdout.

    Raises:
        DirectoryNotFoundError: If the migrations directory does not exist.

    Example:
        >>> generate_new_migration_file_cmd("create users table")
        Created migration file: V20251201.120000__create_users_table.sql
    """

    migrations_dir_path: str = os.path.join(os.getcwd(), MIGRATIONS_DIR)

    if not os.path.exists(migrations_dir_path):
        raise DirectoryNotFoundError(
            "Migrations directory not found. Run 'jetbase initialize' to set up jetbase.\n"
            "If you have already done so, run this command from the jetbase directory."
        )

    filename: str = _generate_new_filename(description=description)
    filepath: str = os.path.join(migrations_dir_path, filename)

    with open(filepath, "w") as f:  # noqa: F841
        f.write(NEW_MIGRATION_FILE_CONTENT)
    print(f"Created migration file: {filename}")


def _generate_new_filename(description: str) -> str:
    """
    Generate a timestamped filename for a migration.

    Creates a filename using the current timestamp in YYYYMMDD.HHMMSS format
    followed by the description with spaces converted to underscores.

    Args:
        description (str): A human-readable description for the migration.

    Returns:
        str: Formatted filename like "V20251201.120000__description.sql".

    Example:
        >>> _generate_new_filename("add users")
        'V20251201.120000__add_users.sql'
    """
    timestamp = dt.datetime.now().strftime("%Y%m%d.%H%M%S")
    return f"V{timestamp}__{description.replace(' ', '_')}.sql"
