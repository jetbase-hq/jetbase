import os

from jetbase.core.file_parser import parse_sql_file
from jetbase.core.repository import (
    create_migrations_table,
    get_last_updated_version,
    run_migration,
)
from jetbase.core.version import get_versions


def upgrade() -> None:
    create_migrations_table()
    latest_version: str = get_last_updated_version()
    all_versions = get_versions(
        directory=os.path.join(os.getcwd(), "migrations"),
        version_to_start_from=latest_version,
    )

    for version, file_path in all_versions.items():
        sql_statements: list[str] = parse_sql_file(file_path)
        run_migration(sql_statements=sql_statements, version=version)
        filename: str = os.path.basename(file_path)

        print(f"Migration applied successfully: {filename}")
