import os

from jetbase.core.file_parser import parse_upgrade_statements
from jetbase.core.repository import (
    create_migrations_table,
    get_last_updated_version,
    run_migration,
)
from jetbase.core.version import get_versions
from jetbase.enums import MigrationOperationType


def upgrade_cmd(count: int | None = None, to_version: str | None = None) -> None:
    """
    Run database migrations by applying all pending SQL migration files.
    Executes migration files in order starting from the last applied version,
    updating the migrations tracking table after each successful migration.

    Returns:
        None
    """

    if count is not None and to_version is not None:
        raise ValueError(
            "Cannot specify both 'count' and 'to_version' for upgrade. "
            "Select only one, or do not specify either to run all pending migrations."
        )

    create_migrations_table()
    latest_version: str | None = get_last_updated_version()

    all_versions: dict[str, str] = get_versions(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_version,
    )

    if latest_version:
        all_versions = dict(list(all_versions.items())[1:])

    if count:
        all_versions = dict(list(all_versions.items())[:count])
    elif to_version:
        if all_versions.get(to_version) is None:
            raise ValueError(
                f"The specified to_version '{to_version}' does not exist among pending migrations."
            )
        all_versions_list = []
        for file_version, file_path in all_versions.items():
            all_versions_list.append((file_version, file_path))
            if file_version == to_version:
                break
        all_versions = dict(all_versions_list)

    for version, file_path in all_versions.items():
        sql_statements: list[str] = parse_upgrade_statements(file_path=file_path)
        run_migration(
            sql_statements=sql_statements,
            version=version,
            migration_operation=MigrationOperationType.UPGRADE,
        )
        filename: str = os.path.basename(file_path)

        print(f"Migration applied successfully: {filename}")
