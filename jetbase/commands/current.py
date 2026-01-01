from jetbase.models import MigrationRecord
from jetbase.repositories.migrations_repo import fetch_latest_versioned_migration


def current_cmd() -> None:
    """Show the latest migration version"""
    latest_migration: MigrationRecord | None = fetch_latest_versioned_migration()
    if latest_migration:
        print(f"Latest migration version: {latest_migration.version}")
    else:
        print("No migrations have been applied yet.")
