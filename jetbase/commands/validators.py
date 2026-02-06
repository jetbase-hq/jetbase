from pathlib import Path

from jetbase.engine.jetbase_locator import find_jetbase_directory
from jetbase.exceptions import DirectoryNotFoundError


def validate_jetbase_directory() -> None:
    """
    Ensure command is run from jetbase directory or a parent project directory.

    Validates that:
    1. The current directory is named 'jetbase' and contains a 'migrations' folder, OR
    2. A 'jetbase' directory with 'migrations' folder exists in the current or parent directory

    Returns:
        None: Returns silently if validation passes.

    Raises:
        DirectoryNotFoundError: If no valid jetbase directory is found.
    """
    current_dir = Path.cwd()

    if current_dir.name == "jetbase":
        migrations_dir = current_dir / "migrations"
        if migrations_dir.exists() and migrations_dir.is_dir():
            return

    jetbase_dir = find_jetbase_directory()
    if jetbase_dir:
        return

    raise DirectoryNotFoundError(
        "Jetbase directory not found. Please ensure you are either:\n"
        "  - In a directory named 'jetbase' with a 'migrations' subdirectory, OR\n"
        "  - In a project directory that contains a 'jetbase/' subdirectory with migrations\n"
        "You can run 'jetbase init' to create a Jetbase project."
    )
