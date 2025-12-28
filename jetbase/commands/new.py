import datetime as dt
import os

from jetbase.constants import MIGRATIONS_DIR, NEW_MIGRATION_FILE_CONTENT
from jetbase.exceptions import DirectoryNotFoundError


def generate_new_migration_file_cmd(description: str) -> None:
    """
    Generate a new migration file with a timestamped filename.
    This function creates a new SQL migration file in the migrations directory with
    a filename format of V{timestamp}__{description}.sql. The timestamp is in the
    format YYYYMMDD.HHMMSS.
    Args:
        description (str): A description for the migration file.
            Spaces in the description will be replaced with underscores in the
            filename.
    Raises:
        DirectoryNotFoundError: If the migrations directory is not found.
    Returns:
        None
    Examples:
        >>> generate_new_migration_file_cmd("create users table")
        Created migration file: jetbase/migrations/V20251201.120000__create_users_table.sql
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
    Generate a new filename for a migration file.
    Args:
        description (str): A description for the migration file.
    Returns:
        str: A new filename for the migration file.
    """
    timestamp = dt.datetime.now().strftime("%Y%m%d.%H%M%S")
    return f"V{timestamp}__{description.replace(' ', '_')}.sql"
