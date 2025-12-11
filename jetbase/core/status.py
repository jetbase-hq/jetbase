import os

from rich.console import Console
from rich.table import Table

from jetbase.core.file_parser import get_description_from_filename
from jetbase.core.models import MigrationRecord
from jetbase.core.repository import (
    get_migration_records,
    get_repeatable_on_change_filepaths,
)
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationType


def status_cmd() -> None:
    migration_records: list[MigrationRecord] = get_migration_records()

    versioned_migration_records: list[MigrationRecord] = [
        record
        for record in migration_records
        if record.migration_type == MigrationType.VERSIONED.value
    ]

    latest_migrated_version: str | None = (
        versioned_migration_records[-1].version if versioned_migration_records else None
    )

    migration_filepaths_by_version_to_be_migrated: dict[str, str] = (
        get_migration_filepaths_by_version(
            directory=os.path.join(os.getcwd(), "migrations"),
            version_to_start_from=latest_migrated_version,
        )
    )

    if latest_migrated_version:
        migration_filepaths_by_version_to_be_migrated = dict(
            list(migration_filepaths_by_version_to_be_migrated.items())[1:]
        )

    roc_filepaths_to_be_migrated: list[str] = get_repeatable_on_change_filepaths(
        directory=os.path.join(os.getcwd(), "migrations"), changed_only=True
    )

    roc_filenames_to_be_migrated: list[str] = [
        os.path.basename(filepath) for filepath in roc_filepaths_to_be_migrated
    ]

    console = Console()

    # Table for applied migrations
    applied_table = Table(
        title="Migrations Applied", show_header=True, header_style="bold magenta"
    )
    applied_table.add_column("Version", style="cyan")
    applied_table.add_column("Description", style="green")

    for record in migration_records:
        if record.migration_type == MigrationType.VERSIONED.value:
            applied_table.add_row(record.version, record.description)
        else:
            applied_table.add_row(record.migration_type, record.description)

    console.print(applied_table)
    console.print()

    # Table for pending migrations
    pending_table = Table(
        title="Migrations Pending", show_header=True, header_style="bold magenta"
    )
    pending_table.add_column("Version", style="cyan")
    pending_table.add_column("Description", style="green")

    for version, filepath in migration_filepaths_by_version_to_be_migrated.items():
        pending_table.add_row(
            version, get_description_from_filename(filename=os.path.basename(filepath))
        )

    for record in migration_records:
        if record.migration_type == MigrationType.REPEATABLE_ALWAYS.value:
            pending_table.add_row(record.migration_type, record.description)

    for record in migration_records:
        if (
            record.migration_type == MigrationType.REPEATABLE_ON_CHANGE.value
            and record.filename in roc_filenames_to_be_migrated
        ):
            pending_table.add_row(record.migration_type, record.description)

    console.print(pending_table)
