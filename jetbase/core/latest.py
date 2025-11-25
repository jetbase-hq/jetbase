from jetbase.core.repository import get_last_updated_version


def latest_cmd() -> None:
    """Show the latest migration version"""
    latest_migrated_version: str | None = get_last_updated_version()
    if latest_migrated_version:
        print(f"Latest migration version: {latest_migrated_version}")
    else:
        print("No migrations have been applied yet.")
