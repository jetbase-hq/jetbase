from pathlib import Path

from jetbase.exceptions import DirectoryNotFoundError


def validate_jetbase_directory() -> None:
    """
    Ensure command is run from jetbase directory with migrations folder.

    Validates that the current working directory is named 'jetbase' and
    contains a 'migrations' subdirectory. This validation is required
    before running most Jetbase CLI commands.

    Returns:
        None: Returns silently if validation passes.

    Raises:
        DirectoryNotFoundError: If the current directory is not named
            'jetbase' or if the 'migrations' subdirectory does not exist.
    """
    current_dir = Path.cwd()

    # Check if current directory is named 'jetbase'
    if current_dir.name != "jetbase":
        raise DirectoryNotFoundError(
            "Command must be run from the 'jetbase' directory.\n"
            "You can run 'jetbase init' to create a Jetbase project."
        )

    # Check if migrations directory exists
    migrations_dir = current_dir / "migrations"
    if not migrations_dir.exists() or not migrations_dir.is_dir():
        raise DirectoryNotFoundError(
            f"'migrations' directory not found in {current_dir}.\n"
            "Add a migrations directory inside the 'jetbase' directory to proceed.\n"
            "You can also run 'jetbase init' to create a Jetbase project."
        )
