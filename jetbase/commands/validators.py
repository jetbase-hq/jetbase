from pathlib import Path

from jetbase.exceptions import DirectoryNotFoundError


def validate_jetbase_directory() -> None:
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
