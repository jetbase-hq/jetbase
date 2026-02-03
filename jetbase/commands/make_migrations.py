import os

from sqlalchemy.engine import Connection

from jetbase.commands.new import _generate_new_filename
from jetbase.constants import MIGRATIONS_DIR
from jetbase.database.connection import get_db_connection
from jetbase.engine.model_discovery import (
    ModelDiscoveryError,
    discover_all_models,
)
from jetbase.engine.schema_diff import compare_schemas, has_changes
from jetbase.engine.schema_introspection import introspect_database
from jetbase.engine.sql_generator import (
    generate_drop_table_sql,
    generate_add_column_sql,
    generate_drop_column_sql,
    generate_create_index_sql,
    generate_drop_index_sql,
    generate_add_foreign_key_sql,
    generate_drop_foreign_key_sql,
    get_db_type,
)


class MakeMigrationsError(Exception):
    """Base exception for make-migrations errors."""

    pass


class NoChangesDetectedError(MakeMigrationsError):
    """Raised when no schema changes are detected."""

    pass


def generate_create_table_from_model(model_class, connection: Connection) -> str:
    """
    Generate CREATE TABLE SQL from a SQLAlchemy model class.

    Args:
        model_class: The SQLAlchemy model class.
        connection: Database connection.

    Returns:
        str: CREATE TABLE SQL statement.
    """
    table = model_class.__table__

    columns = []
    for col in table.columns:
        col_def = f"{col.name} {col.type.compile(dialect=connection.engine.dialect)}"
        if not col.nullable:
            col_def += " NOT NULL"
        if col.primary_key:
            col_def += " PRIMARY KEY"
        columns.append(col_def)

    pk_cols = ", ".join([c.name for c in table.primary_key.columns])
    cols_sql = ",\n    ".join(columns)
    return f"CREATE TABLE {table.name} (\n    {cols_sql}\n);"


def make_migrations_cmd(description: str | None = None) -> None:
    """
    Generate migration files automatically from model definitions.

    This command:
    1. Reads JETBASE_MODELS env var
    2. Validates model paths exist
    3. Discovers SQLAlchemy models
    4. Introspects current database schema
    5. Generates diff between models and database
    6. Generates upgrade and rollback SQL
    7. Creates migration file using existing _generate_new_filename

    Args:
        description (str | None): Optional description for the migration.
                                   If not provided, uses "auto_generated".

    Raises:
        MakeMigrationsError: If migration generation fails.
        NoChangesDetectedError: If no schema changes are detected.
    """
    try:
        _, models = discover_all_models()
    except ModelDiscoveryError as e:
        raise MakeMigrationsError(f"Failed to discover models: {e}")

    try:
        with get_db_connection() as connection:
            database_schema = introspect_database(connection)
    except Exception as e:
        raise MakeMigrationsError(f"Failed to introspect database: {e}")

    diff = compare_schemas(models, database_schema, connection)

    if not has_changes(diff):
        print("No changes detected.")
        return

    db_type = get_db_type()

    upgrade_statements = []
    rollback_statements = []

    with get_db_connection() as connection:
        for table_name in diff.tables_to_create:
            model_class = models[table_name]
            sql = generate_create_table_from_model(model_class, connection)
            upgrade_statements.append(sql)
            rollback_statements.append(generate_drop_table_sql(table_name, db_type))

        for table_name in diff.columns_to_add:
            for column in diff.columns_to_add[table_name]:
                upgrade_statements.append(
                    generate_add_column_sql(table_name, column, db_type)
                )
                rollback_statements.append(
                    generate_drop_column_sql(table_name, column.name, db_type)
                )

        for table_name in diff.indexes_to_create:
            for index_info in diff.indexes_to_create[table_name]:
                upgrade_statements.append(
                    generate_create_index_sql(table_name, index_info, db_type)
                )
                rollback_statements.append(
                    generate_drop_index_sql(index_info["name"], table_name, db_type)
                )

        for table_name in diff.foreign_keys_to_create:
            for fk_info in diff.foreign_keys_to_create[table_name]:
                upgrade_statements.append(
                    generate_add_foreign_key_sql(table_name, fk_info, db_type)
                )
                rollback_statements.append(
                    generate_drop_foreign_key_sql(table_name, fk_info["name"], db_type)
                )

    upgrade_sql = "\n\n".join(upgrade_statements)
    rollback_sql = "\n\n".join(rollback_statements)

    migration_description = description or "auto_generated"

    filename = _generate_new_filename(description=migration_description)
    filepath = os.path.join(os.getcwd(), MIGRATIONS_DIR, filename)

    migration_content = f"""-- upgrade

{upgrade_sql}

-- rollback

{rollback_sql}
"""

    with open(filepath, "w") as f:
        f.write(migration_content)

    print(f"Created migration file: {filename}")
