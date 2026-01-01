import datetime as dt


def get_display_version(
    migration_type: str,
    version: str | None = None,
) -> str:
    """
    Get the display string for a migration version.

    Returns the version string for versioned migrations, or a label
    for repeatable migrations.

    Args:
        migration_type (str): The type of migration ('runs_always',
            'runs_on_change', or 'versioned').
        version (str | None): The version string for versioned migrations.
            Defaults to None.

    Returns:
        str: The version string if provided, "RUNS_ALWAYS" for runs_always
            migrations, or "RUNS_ON_CHANGE" for runs_on_change migrations.

    Raises:
        ValueError: If migration_type is invalid and version is None.

    Example:
        >>> get_display_version("runs_always")
        'RUNS_ALWAYS'
    """

    if version:
        return version
    if migration_type.lower() == "runs_always":
        return "RUNS_ALWAYS"
    elif migration_type.lower() == "runs_on_change":
        return "RUNS_ON_CHANGE"
    raise ValueError("Invalid migration type for display version.")


def format_applied_at(applied_at: dt.datetime | str | None) -> str:
    """
    Format a timestamp for display in migration history.

    Handles both datetime objects (PostgreSQL) and string timestamps
    (SQLite) by truncating to a consistent 22-character format.

    Args:
        applied_at (dt.datetime | str | None): The timestamp to format.
            Can be a datetime object, string, or None.

    Returns:
        str: Formatted timestamp string truncated to 22 characters,
            or empty string if input is None.
    """
    if applied_at is None:
        return ""
    if isinstance(applied_at, str):
        # SQLite returns strings - just truncate to match format
        return applied_at[:22]
    return applied_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:22]
