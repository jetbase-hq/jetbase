import datetime as dt


def get_display_version(
    migration_type: str,
    version: str | None = None,
) -> str:
    """
    Get the display version string for a migration.
    Args:
        version (str | None): The version string of the migration. If provided, this value is returned directly.
        migration_type (str): The type of migration. Expected values are "repeatable_always" or "runs_on_change".
    Returns:
        str: The display version string. Returns the version if provided, "[RA]" for repeatable_always migrations,
             or "[ROC]" for runs_on_change migrations.
    Raises:
        ValueError: If the migration_type is invalid (not "repeatable_always" or "runs_on_change") and
                    version is None.
    """

    if version:
        return version
    if migration_type.lower() == "runs_always":
        return "RUNS_ALWAYS"
    elif migration_type.lower() == "runs_on_change":
        return "RUNS_ON_CHANGE"
    raise ValueError("Invalid migration type for display version.")


def format_applied_at(applied_at: dt.datetime | str | None) -> str:
    """Format applied_at timestamp for display, handling both datetime and string (sqlite returns a string)."""
    if applied_at is None:
        return ""
    if isinstance(applied_at, str):
        # SQLite returns strings - just truncate to match format
        return applied_at[:22]
    return applied_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:22]
