def get_display_version(
    migration_type: str,
    version: str | None = None,
) -> str:
    """
    Get the display version string for a migration.
    Args:
        version (str | None): The version string of the migration. If provided, this value is returned directly.
        migration_type (str): The type of migration. Expected values are "repeatable_always" or "repeatable_on_change".
    Returns:
        str: The display version string. Returns the version if provided, "[RA]" for repeatable_always migrations,
             or "[RC]" for repeatable_on_change migrations.
    Raises:
        ValueError: If the migration_type is invalid (not "repeatable_always" or "repeatable_on_change") and
                    version is None.
    """

    if version:
        return version
    if migration_type.lower() == "repeatable_always":
        return "RUNS_ALWAYS"
    elif migration_type.lower() == "repeatable_on_change":
        return "RUNS_ON_CHANGE"
    raise ValueError("Invalid migration type for display version.")
