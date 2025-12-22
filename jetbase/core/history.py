from rich.console import Console
from rich.table import Table

from jetbase.core.models import MigrationRecord
from jetbase.core.repository import get_migration_records, migrations_table_exists


def history_cmd() -> None:
    """
    Display the migration history in a formatted table.

    This command retrieves and displays all applied migrations from the database
    in a rich-formatted table showing version numbers, execution order, and
    descriptions.

    The table includes:
        - Version: The migration version identifier
        - Order Executed: The sequential order in which migrations were applied
        - Description: A brief description of what the migration does

    If no migrations have been applied, displays a message indicating that.

    Returns:
        None

    Example:
        >>> history_cmd()
        # Displays a formatted table with migration history
    """
    table_exists: bool = migrations_table_exists()
    if not table_exists:
        print("No migrations have been applied.")
        return None

    console: Console = Console()

    migration_records: list[MigrationRecord] = get_migration_records()
    if not migration_records:
        console.print("[yellow]No migrations have been applied yet.[/yellow]")
        return

    migration_history_table: Table = Table(
        title="Migration History", show_header=True, header_style="bold magenta"
    )
    migration_history_table.add_column("Version", style="cyan", no_wrap=True)
    migration_history_table.add_column("Order Executed", style="green")
    migration_history_table.add_column("Description", style="white")
    migration_history_table.add_column("Applied At", style="green", no_wrap=True)
    # migration_history_table.add_column("Migration Type", style="cyan")

    for record in migration_records:
        migration_history_table.add_row(
            get_display_version(
                version=record.version, migration_type=record.migration_type
            ),
            str(record.order_executed),
            record.description,
            record.applied_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:22],
            # get_display_migration_type(migration_type=record.migration_type),
        )

    console.print(migration_history_table)


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
