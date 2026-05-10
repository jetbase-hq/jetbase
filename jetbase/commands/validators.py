from pathlib import Path

from jetbase.constants import BASE_DIR, MIGRATIONS_DIR
from jetbase.exceptions import DirectoryNotFoundError


def get_jetbase_directory() -> Path:
    """
    Get the path to the jetbase directory.

    Find the root project directory by looking for the 'jetbase' folder.

    Returns:
        Path: The path to the jetbase directory.

    Raises:
        DirectoryNotFoundError: If the jetbase directory cannot be found in the current path or
            any parent directories.
    """
    current_dir = Path.cwd()

    if current_dir.name == BASE_DIR:
        return current_dir

    if (current_dir / BASE_DIR).is_dir():
        return current_dir / BASE_DIR

    for parent in current_dir.parents:
        if (parent / BASE_DIR).is_dir():
            return parent / BASE_DIR

    raise DirectoryNotFoundError(
        f"'{BASE_DIR}' directory not found. Run 'jetbase init' to create a Jetbase project."
    )


def get_migrations_directory() -> Path:
    """
    Get the path to the migrations directory.

    Returns:
        Path: The path to the migrations directory.

    Raises:
        DirectoryNotFoundError: If the migrations directory does not exist in the jetbase directory.
    """
    jetbase_dir = get_jetbase_directory()
    migrations_dir = jetbase_dir / MIGRATIONS_DIR
    if not migrations_dir.exists() or not migrations_dir.is_dir():
        raise DirectoryNotFoundError(
            f"'{MIGRATIONS_DIR}' directory not found in {jetbase_dir}.\n"
            "Add a migrations directory inside the 'jetbase' directory to proceed.\n"
            "You can also run 'jetbase init' to create a Jetbase project."
        )
    return migrations_dir


def validate_jetbase_directory() -> None:
    """
    Ensure a jetbase directory exists in the current directory or parent directories.

    Validates that a 'jetbase' directory exists in the current working directory
    or any of its parent directories, and that it contains a 'migrations' subdirectory.
    This validation is required before running most Jetbase CLI commands.

    Returns:
        None: Returns silently if validation passes.

    Raises:
        DirectoryNotFoundError: If the jetbase directory or migrations subdirectory does not exist.
    """
    get_migrations_directory()
