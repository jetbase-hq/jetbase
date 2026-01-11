import typer

from jetbase.commands.current import current_cmd
from jetbase.commands.fix_checksums import fix_checksums_cmd
from jetbase.commands.fix_files import fix_files_cmd
from jetbase.commands.history import history_cmd
from jetbase.commands.init import initialize_cmd
from jetbase.commands.lock_status import lock_status_cmd
from jetbase.commands.new import generate_new_migration_file_cmd
from jetbase.commands.rollback import rollback_cmd
from jetbase.commands.status import status_cmd
from jetbase.commands.unlock import unlock_cmd
from jetbase.commands.upgrade import upgrade_cmd
from jetbase.commands.validators import validate_jetbase_directory

app = typer.Typer(help="Jetbase CLI")


@app.command()
def init():
    """Initialize jetbase in current directory"""
    initialize_cmd()


@app.command()
def upgrade(
    count: int = typer.Option(
        None, "--count", "-c", help="Number of migrations to apply"
    ),
    to_version: str | None = typer.Option(
        None, "--to-version", "-t", help="Rollback to a specific version"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Simulate the upgrade without making changes"
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip both checksum and file version validation when running migrations",
    ),
    skip_checksum_validation: bool = typer.Option(
        False,
        "--skip-checksum-validation",
        help="Skip checksum validation when running migrations",
    ),
    skip_file_validation: bool = typer.Option(
        False,
        "--skip-file-validation",
        help="Skip file version validation when running migrations",
    ),
):
    """Execute pending migrations"""
    validate_jetbase_directory()
    upgrade_cmd(
        count=count,
        to_version=to_version.replace("_", ".") if to_version else None,
        dry_run=dry_run,
        skip_validation=skip_validation,
        skip_checksum_validation=skip_checksum_validation,
        skip_file_validation=skip_file_validation,
    )


@app.command()
def rollback(
    count: int = typer.Option(
        None, "--count", "-c", help="Number of migrations to rollback"
    ),
    to_version: str | None = typer.Option(
        None, "--to-version", "-t", help="Rollback to a specific version"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Simulate the rollback without making changes"
    ),
):
    """Rollback migration(s)"""
    validate_jetbase_directory()
    rollback_cmd(
        count=count,
        to_version=to_version.replace("_", ".") if to_version else None,
        dry_run=dry_run,
    )


@app.command()
def history():
    """Show migration history"""
    validate_jetbase_directory()
    history_cmd()


@app.command()
def current():
    """Show the latest version that has been migrated"""
    validate_jetbase_directory()
    current_cmd()


@app.command()
def unlock():
    """
    Unlock the migration lock to allow migrations to run again.

    WARNING: Only use this if you're certain no migration is currently running.
    Unlocking then running a migration during an active migration can cause database corruption.
    """
    validate_jetbase_directory()
    unlock_cmd()


@app.command()
def lock_status() -> None:
    """Checks if the database is currently locked for migrations or not."""
    validate_jetbase_directory()
    lock_status_cmd()


@app.command()
def fix_checksums() -> None:
    """Updates all stored checksums to their current values."""
    validate_jetbase_directory()
    fix_checksums_cmd()


@app.command()
def fix() -> None:
    """Repair migration files and versions."""
    validate_jetbase_directory()
    fix_files_cmd(audit_only=False)
    fix_checksums_cmd(audit_only=False)
    print("Fix completed successfully.")


@app.command()
def validate_checksums(
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Fix any detected checksum mismatches by updating the stored checksum to match any changes in its corresponding migration file",
    ),
) -> None:
    """Audit migration checksums without making changes. Use --fix to update stored checksums to match current migration files."""
    validate_jetbase_directory()
    if fix:
        fix_checksums_cmd(audit_only=False)
    else:
        fix_checksums_cmd(audit_only=True)


@app.command()
def validate_files(
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Fix any detected migration file issues",
    ),
) -> None:
    """Check if any migration files are missing. Use --fix to clean up records of migrations whose files no longer exist."""
    validate_jetbase_directory()
    if fix:
        fix_files_cmd(audit_only=False)
    else:
        fix_files_cmd(audit_only=True)


@app.command()
def fix_files() -> None:
    """Stops jetbase from tracking migrations whose files no longer exist."""
    validate_jetbase_directory()
    fix_files_cmd(audit_only=False)


@app.command()
def status() -> None:
    """Display migration status: applied migrations and pending migrations."""
    validate_jetbase_directory()
    status_cmd()


# check if typer enforces enum types - if yes then create enum for migration type
@app.command()
def new(
    description: str = typer.Argument(..., help="Description of the migration"),
    version: str = typer.Option(
        None, "--version", "-v", help="Version of the migration"
    ),
) -> None:
    """Create a new migration file with a timestamp-based version and the provided description."""
    validate_jetbase_directory()
    generate_new_migration_file_cmd(description=description, version=version)


def main() -> None:
    """
    Entry point for the Jetbase CLI application.

    Initializes and runs the Typer application that handles all CLI commands
    including migrations, rollbacks, and database management operations.
    """
    app()


if __name__ == "__main__":
    main()
