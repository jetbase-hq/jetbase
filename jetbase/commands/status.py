import os

from rich.console import Console
from rich.table import Table

from jetbase.core.file_parser import get_description_from_filename
from jetbase.core.formatters import get_display_version
from jetbase.core.models import MigrationRecord
from jetbase.core.repeatable import get_ra_filenames, get_runs_on_change_filepaths
from jetbase.core.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationType
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    get_existing_on_change_filenames_to_checksums,
    get_migration_records,
    migrations_table_exists,
)


def status_cmd() -> None:
    is_migrations_table: bool = migrations_table_exists()
    if not is_migrations_table:
        create_migrations_table_if_not_exists()
        is_migrations_table = True

    migration_records: list[MigrationRecord] = (
        get_migration_records() if is_migrations_table else []
    )

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

    all_roc_filenames: list[str] = get_ra_filenames()

    roc_filepaths_changed_only: list[str] = get_runs_on_change_filepaths(
        directory=os.path.join(os.getcwd(), "migrations"), changed_only=True
    )

    roc_filenames_changed_only: list[str] = [
        os.path.basename(filepath) for filepath in roc_filepaths_changed_only
    ]

    roc_filenames_migrated: list[str] = list(
        get_existing_on_change_filenames_to_checksums().keys()
    )

    all_roc_filepaths: list[str] = get_runs_on_change_filepaths(
        directory=os.path.join(os.getcwd(), "migrations")
    )

    all_roc_filenames: list[str] = [
        os.path.basename(filepath) for filepath in all_roc_filepaths
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
            applied_table.add_row(
                get_display_version(migration_type=record.migration_type),
                record.description,
            )

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

    # Repeatable always
    for ra_filename in get_ra_filenames():
        description: str = get_description_from_filename(filename=ra_filename)
        pending_table.add_row(
            get_display_version(migration_type=MigrationType.RUNS_ALWAYS.value),
            description,
        )

    # Repeatable on change
    for record in migration_records:
        if (
            record.migration_type == MigrationType.RUNS_ON_CHANGE.value
            and record.filename in roc_filenames_changed_only
        ):
            pending_table.add_row(
                get_display_version(migration_type=MigrationType.RUNS_ON_CHANGE.value),
                record.description,
            )

    for filename in all_roc_filenames:
        if filename not in roc_filenames_migrated:
            description: str = get_description_from_filename(filename=filename)
            pending_table.add_row(
                get_display_version(migration_type=MigrationType.RUNS_ALWAYS.value),
                description,
            )

    console.print(pending_table)
