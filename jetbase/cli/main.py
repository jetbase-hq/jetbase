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
def upgrade():
    """Execute pending migrations"""
    upgrade_cmd()


@app.command()
def rollback(
    count: int = typer.Option(
        1, "--count", "-c", help="Number of migrations to rollback"
    ),
):
    """Rollback migration(s)"""
    rollback_cmd(count=count)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
