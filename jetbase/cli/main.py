import typer

from jetbase.core.checksum_cmd import repair_checksums_cmd
from jetbase.core.generate import generate_new_migration_file_cmd
from jetbase.core.history import history_cmd
from jetbase.core.initialize import initialize_cmd
from jetbase.core.latest import latest_cmd
from jetbase.core.lock import check_lock_cmd, force_unlock_cmd
from jetbase.core.rollback import rollback_cmd
from jetbase.core.status import status_cmd
from jetbase.core.upgrade import upgrade_cmd
from jetbase.core.validation import fix_files_cmd

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
    upgrade_cmd(
        count=count,
        to_version=to_version.replace("_", ".") if to_version else None,
        dry_run=dry_run,
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
    rollback_cmd(
        count=count,
        to_version=to_version.replace("_", ".") if to_version else None,
        dry_run=dry_run,
    )


@app.command()
def history():
    """Show migration history"""
    history_cmd()


@app.command()
def current():
    """Show the latest version that has been migrated"""
    latest_cmd()


@app.command()
def unlock():
    """
    Unlock the migration lock to allow migrations to run again.

    WARNING: Only use this if you're certain no migration is currently running.
    Unlocking then running a migration during an active migration can cause database corruption.
    """
    force_unlock_cmd()


@app.command()
def lock_status() -> None:
    """Checks if the database is currently locked for migrations or not."""
    check_lock_cmd()


@app.command()
def fix_checksums() -> None:
    """Updates all stored checksums to their current values."""
    repair_checksums_cmd()


@app.command()
def fix() -> None:
    """Repair migration files and versions."""
    fix_files_cmd(audit_only=False)
    repair_checksums_cmd(audit_only=False)


@app.command()
def validate_checksums(
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Fix any detected checksum mismatches by updating the stored checksum to match any changes in its corresponding migration file",
    ),
) -> None:
    """Audit migration checksums without making changes."""

    if fix:
        repair_checksums_cmd(audit_only=False)
    else:
        repair_checksums_cmd(audit_only=True)


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

    if fix:
        fix_files_cmd(audit_only=False)
    else:
        fix_files_cmd(audit_only=True)


@app.command()
def fix_files() -> None:
    """Stops jetbase from tracking migrations whose files no longer exist."""
    fix_files_cmd(audit_only=False)


@app.command()
def status() -> None:
    """Display migration status: applied migrations and pending migrations."""
    status_cmd()


@app.command()
def new(
    description: str = typer.Argument(..., help="Description of the migration"),
) -> None:
    """Create a new migration file with a timestamp-based version and the provided description."""
    generate_new_migration_file_cmd(description=description)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
