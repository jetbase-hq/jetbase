import os

from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.core.repository import (
    create_migrations_table,
    get_last_updated_version,
    run_migration,
)
from jetbase.core.version import get_versions
from jetbase.enums import MigrationOperationType


def upgrade_cmd(count: int | None = None) -> None:
    """
    Run database migrations by applying all pending SQL migration files.
    Executes migration files in order starting from the last applied version,
    updating the migrations tracking table after each successful migration.

    Returns:
        None
    """

    create_migrations_table()
    latest_version: str | None = get_last_updated_version()

    all_versions: dict[str, str] = get_versions(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_version,
    )

    if latest_version is not None:
        all_versions = dict(list(all_versions.items())[1:])

    if count is not None:
        all_versions = dict(list(all_versions.items())[:count])

    for version, file_path in all_versions.items():
        sql_statements: list[str] = parse_upgrade_statements(file_path=file_path)
        run_migration(
            sql_statements=sql_statements,
            version=version,
            migration_operation=MigrationOperationType.UPGRADE,
        )
        filename: str = os.path.basename(file_path)

        print(f"Migration applied successfully: {filename}")
