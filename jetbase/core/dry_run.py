import os

from jetbase.core.file_parser import parse_rollback_statements, parse_upgrade_statements
from jetbase.enums import MigrationOperationType


def process_dry_run(
    version_to_filepath: dict[str, str], migration_operation: MigrationOperationType
) -> None:
    print("\nJETBASE - Dry Run Mode")
    print("No SQL will be executed. This is a preview of what would happen.")
    print("----------------------------------------\n\n")

    for version, file_path in version_to_filepath.items():
        if migration_operation == MigrationOperationType.UPGRADE:
            sql_statements: list[str] = parse_upgrade_statements(
                file_path=file_path, dry_run=True
            )
        elif migration_operation == MigrationOperationType.ROLLBACK:
            sql_statements: list[str] = parse_rollback_statements(
                file_path=file_path, dry_run=True
            )
        else:
            raise NotImplementedError(
                f"Dry run not implemented for migration operation: {migration_operation}"
            )

        filename: str = os.path.basename(file_path)

        num_sql_statements: int = len(sql_statements)

        print(
            f"\nSQL Preview for {filename} ({num_sql_statements} {'statements' if num_sql_statements != 1 else 'statement'})"
        )
        for statement in sql_statements:
            print("\n")
            print(statement)
        print("----------------------------------------\n")
