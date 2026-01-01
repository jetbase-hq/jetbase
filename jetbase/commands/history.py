from rich.console import Console
from rich.table import Table

from jetbase.engine.formatters import format_applied_at, get_display_version
from jetbase.models import MigrationRecord
from jetbase.repositories.migrations_repo import (
    get_migration_records,
    migrations_table_exists,
)


def history_cmd() -> None:
    """
    Display the migration history in a formatted table.

    Retrieves all applied migrations from the database and displays them
    in a rich-formatted table showing version numbers, execution order,
    descriptions, and timestamps.

    Returns:
        None: Prints a formatted table to stdout, or a message if no
            migrations have been applied.
    """
    console: Console = Console()
    table_exists: bool = migrations_table_exists()
    if not table_exists:
        console.print("[yellow]No migrations have been applied.[/yellow]")
        return None

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

    for record in migration_records:
        migration_history_table.add_row(
            get_display_version(
                version=record.version, migration_type=record.migration_type
            ),
            str(record.order_executed),
            record.description,
            format_applied_at(applied_at=record.applied_at),
        )

    console.print(migration_history_table)
