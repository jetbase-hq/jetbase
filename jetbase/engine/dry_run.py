import os

from jetbase.engine.file_parser import (
    parse_rollback_statements,
    parse_upgrade_statements,
)
from jetbase.enums import MigrationDirectionType


def process_dry_run(
    version_to_filepath: dict[str, str],
    migration_operation: MigrationDirectionType,
    repeatable_always_filepaths: list[str] | None = None,
    runs_on_change_filepaths: list[str] | None = None,
) -> None:
    """
    Preview migrations without executing them.

    Parses and displays the SQL statements that would be executed for
    each migration, without actually running them against the database.

    Args:
        version_to_filepath (dict[str, str]): Mapping of version strings
            to migration file paths for versioned migrations.
        migration_operation (MigrationDirectionType): Whether this is an
            UPGRADE or ROLLBACK operation.
        repeatable_always_filepaths (list[str] | None): File paths for
            runs-always migrations. Defaults to None.
        runs_on_change_filepaths (list[str] | None): File paths for
            runs-on-change migrations. Defaults to None.

    Returns:
        None: Prints SQL preview to stdout.

    Raises:
        NotImplementedError: If migration_operation is not UPGRADE or ROLLBACK.
    """
    print("\nJETBASE - Dry Run Mode")
    print("No SQL will be executed. This is a preview of what would happen.")
    print("----------------------------------------\n\n")

    for version, file_path in version_to_filepath.items():
        if migration_operation == MigrationDirectionType.UPGRADE:
            sql_statements: list[str] = parse_upgrade_statements(
                file_path=file_path, dry_run=True
            )
        elif migration_operation == MigrationDirectionType.ROLLBACK:
            sql_statements: list[str] = parse_rollback_statements(
                file_path=file_path, dry_run=True
            )
        else:
            raise NotImplementedError(
                f"Dry run not implemented for migration operation: {migration_operation}"
            )

        filename: str = os.path.basename(file_path)

        print_migration_preview(
            filename=filename,
            sql_statements=sql_statements,
        )

    if migration_operation == MigrationDirectionType.UPGRADE:
        if repeatable_always_filepaths:
            for filepath in repeatable_always_filepaths:
                sql_statements: list[str] = parse_upgrade_statements(
                    file_path=filepath, dry_run=True
                )
                filename: str = os.path.basename(filepath)

                print_migration_preview(
                    filename=filename, sql_statements=sql_statements
                )

        if runs_on_change_filepaths:
            for filepath in runs_on_change_filepaths:
                sql_statements: list[str] = parse_upgrade_statements(
                    file_path=filepath, dry_run=True
                )

                print_migration_preview(
                    filename=os.path.basename(filepath), sql_statements=sql_statements
                )


def print_migration_preview(filename: str, sql_statements: list[str]) -> None:
    """
    Print SQL statements for a migration file preview.

    Displays the filename, statement count, and full SQL content for
    each statement in a formatted output.

    Args:
        filename (str): The name of the migration file being previewed.
        sql_statements (list[str]): List of SQL statements to display.

    Returns:
        None: Prints formatted preview to stdout.
    """
    print(
        f"SQL Preview for {filename} ({len(sql_statements)} {'statements' if len(sql_statements) != 1 else 'statement'})\n"
    )
    for statement in sql_statements:
        print(f"{statement}\n")
    print("----------------------------------------\n")
