import os

from jetbase.core.file_parser import parse_rollback_statements
from jetbase.core.repository import get_latest_versions, run_migration
from jetbase.core.version import get_versions
from jetbase.enums import MigrationOperationType


def rollback_cmd() -> None:
    number_of_migrations_to_rollback: int = 1
    latest_migration_versions: list[str] = get_latest_versions(
        limit=number_of_migrations_to_rollback
    )

    if not latest_migration_versions:
        raise RuntimeError("No migrations have been applied; cannot perform rollback.")

    versions_to_rollback: dict[str, str] = get_versions(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_migration_versions[0],
        end_version=latest_migration_versions[-1],
    )

    versions_to_rollback: dict[str, str] = dict(reversed(versions_to_rollback.items()))

    for version, file_path in versions_to_rollback.items():
        sql_statements: list[str] = parse_rollback_statements(file_path=file_path)
        run_migration(
            sql_statements=sql_statements,
            version=version,
            migration_operation=MigrationOperationType.ROLLBACK,
        )
        filename: str = os.path.basename(file_path)

        print(f"Rollback applied successfully: {filename}")
