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
    migration_history_table.add_column(
        "Order Executed", style="green", justify="center"
    )
    migration_history_table.add_column("Description", style="white")

    for record in migration_records:
        migration_history_table.add_row(
            record.version, str(record.order_executed), record.description
        )

    console.print(migration_history_table)
