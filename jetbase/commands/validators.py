from jetbase.paths import get_migrations_directory


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
