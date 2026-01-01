from jetbase.models import MigrationRecord
from jetbase.repositories.migrations_repo import fetch_latest_versioned_migration


def current_cmd() -> None:
    """
    Display the current (latest applied) migration version.

    Queries the database for the most recently applied versioned migration
    and prints its version number. If no migrations have been applied,
    displays a message indicating that.

    Returns:
        None: Prints the current migration version to stdout.
    """
    latest_migration: MigrationRecord | None = fetch_latest_versioned_migration()
    if latest_migration:
        print(f"Latest migration version: {latest_migration.version}")
    else:
        print("No migrations have been applied yet.")
