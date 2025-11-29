import typer

from jetbase.core.history import history_cmd
from jetbase.core.initialize import initialize_cmd
from jetbase.core.latest import latest_cmd
from jetbase.core.lock import check_lock_cmd, force_unlock_cmd
from jetbase.core.rollback import rollback_cmd
from jetbase.core.upgrade import upgrade_cmd

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
):
    """Execute pending migrations"""
    upgrade_cmd(
        count=count,
        to_version=to_version.replace("_", ".") if to_version else None,
        dry_run=dry_run,
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
        False, "--dry-run", "-d", help="Simulate the upgrade without making changes"
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
def latest():
    """Show the latest migration version"""
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
def check_lock() -> None:
    """Checks if the database is currently locked for migrations or not."""
    check_lock_cmd()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
