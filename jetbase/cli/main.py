import typer

from jetbase.core.initialize import initialize_cmd
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
):
    """Execute pending migrations"""
    upgrade_cmd(count=count)


@app.command()
def rollback(
    count: int = typer.Option(
        None, "--count", "-c", help="Number of migrations to rollback"
    ),
    to_version: str | None = typer.Option(
        None, "--to-version", "-t", help="Rollback to a specific version"
    ),
):
    """Rollback migration(s)"""
    rollback_cmd(count=count, to_version=to_version)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
