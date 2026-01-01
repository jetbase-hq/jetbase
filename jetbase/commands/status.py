import os

from rich.console import Console
from rich.table import Table

from jetbase.engine.file_parser import get_description_from_filename
from jetbase.engine.formatters import get_display_version
from jetbase.engine.repeatable import get_ra_filenames, get_runs_on_change_filepaths
from jetbase.engine.version import get_migration_filepaths_by_version
from jetbase.enums import MigrationType
from jetbase.models import MigrationRecord
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    get_existing_on_change_filenames_to_checksums,
    get_migration_records,
    migrations_table_exists,
)


def status_cmd() -> None:
    """
    Display applied and pending migrations.

    Shows two tables: one listing all migrations that have been applied to
    the database, and another listing pending migrations that are available
    in the migrations directory but have not yet been applied.

    Returns:
        None: Prints formatted tables to stdout showing migration status.
    """
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

    pending_versioned_filepaths: dict[str, str] = get_migration_filepaths_by_version(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migrated_version,
    )

    if latest_migrated_version:
        pending_versioned_filepaths = dict(
            list(pending_versioned_filepaths.items())[1:]
        )

    all_roc_filenames: list[str] = get_ra_filenames()

    roc_filenames_changed_only: list[str] = [
        os.path.basename(filepath)
        for filepath in get_runs_on_change_filepaths(
            directory=os.path.join(os.getcwd(), "migrations"), changed_only=True
        )
    ]

    roc_filenames_migrated: list[str] = list(
        get_existing_on_change_filenames_to_checksums().keys()
    )

    all_roc_filenames: list[str] = [
        os.path.basename(filepath)
        for filepath in get_runs_on_change_filepaths(
            directory=os.path.join(os.getcwd(), "migrations")
        )
    ]

    console = Console()

    applied_table: Table = _create_migrations_display_table(title="Migrations Applied")

    _add_applied_rows(table=applied_table, migration_records=migration_records)

    console.print(applied_table)
    console.print()

    pending_table: Table = _create_migrations_display_table(title="Migrations Pending")

    _add_pending_rows(
        table=pending_table,
        pending_versioned_filepaths=pending_versioned_filepaths,
        migration_records=migration_records,
        roc_filenames_changed_only=roc_filenames_changed_only,
        all_roc_filenames=all_roc_filenames,
        roc_filenames_migrated=roc_filenames_migrated,
    )

    console.print(pending_table)


def _create_migrations_display_table(title: str) -> Table:
    """
    Create a rich Table for displaying migrations.

    Configures a table with styled columns for displaying migration
    version numbers and descriptions.

    Args:
        title (str): The title to display above the table.

    Returns:
        Table: A configured rich Table with Version and Description columns.
    """
    display_table: Table = Table(
        title=title, show_header=True, header_style="bold magenta"
    )
    display_table.add_column("Version", style="cyan")
    display_table.add_column("Description", style="green")

    return display_table


def _add_applied_rows(table: Table, migration_records: list[MigrationRecord]) -> None:
    """
    Add applied migration rows to the table.

    Populates the table with rows for each applied migration, displaying
    the version number and description for both versioned and repeatable
    migrations.

    Args:
        table (Table): The rich Table to add rows to.
        migration_records (list[MigrationRecord]): List of migration records
            that have been applied to the database.

    Returns:
        None: Modifies the table in place.
    """
    for record in migration_records:
        if record.migration_type == MigrationType.VERSIONED.value:
            table.add_row(record.version, record.description)
        else:
            table.add_row(
                get_display_version(migration_type=record.migration_type),
                record.description,
            )


def _add_pending_rows(
    table: Table,
    pending_versioned_filepaths: dict[str, str],
    migration_records: list[MigrationRecord],
    roc_filenames_changed_only: list[str],
    all_roc_filenames: list[str],
    roc_filenames_migrated: list[str],
) -> None:
    """
    Add pending migration rows to the table.

    Populates the table with rows for each pending migration including
    versioned migrations, runs-always migrations, and runs-on-change
    migrations that have been modified or not yet applied.

    Args:
        table (Table): The rich Table to add rows to.
        pending_versioned_filepaths (dict[str, str]): Mapping of version
            strings to file paths for pending versioned migrations.
        migration_records (list[MigrationRecord]): All migration records
            from the database.
        roc_filenames_changed_only (list[str]): Filenames of runs-on-change
            migrations that have been modified since last applied.
        all_roc_filenames (list[str]): All runs-on-change migration filenames.
        roc_filenames_migrated (list[str]): Runs-on-change migrations that
            have been previously applied.

    Returns:
        None: Modifies the table in place.
    """
    for version, filepath in pending_versioned_filepaths.items():
        table.add_row(
            version, get_description_from_filename(filename=os.path.basename(filepath))
        )

    # Runs always
    for ra_filename in get_ra_filenames():
        description: str = get_description_from_filename(filename=ra_filename)
        table.add_row(
            get_display_version(migration_type=MigrationType.RUNS_ALWAYS.value),
            description,
        )

    # Runs on change - changed only
    for record in migration_records:
        if (
            record.migration_type == MigrationType.RUNS_ON_CHANGE.value
            and record.filename in roc_filenames_changed_only
        ):
            table.add_row(
                get_display_version(migration_type=MigrationType.RUNS_ON_CHANGE.value),
                record.description,
            )

    # Runs on change - new
    for filename in all_roc_filenames:
        if filename not in roc_filenames_migrated:
            description: str = get_description_from_filename(filename=filename)
            table.add_row(
                get_display_version(migration_type=MigrationType.RUNS_ON_CHANGE.value),
                description,
            )
