import asyncio
import os

from typing import Union

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncConnection

from jetbase.commands.new import _generate_new_filename
from jetbase.constants import MIGRATIONS_DIR
from jetbase.database.connection import (
    get_db_connection,
    get_async_db_connection,
    get_connection,
    is_async_enabled,
)
from jetbase.enums import DatabaseType
from jetbase.engine.jetbase_locator import find_jetbase_directory
from jetbase.config import get_config
from jetbase.engine.model_discovery import (
    ModelDiscoveryError,
    discover_all_models,
)
from jetbase.engine.schema_diff import (
    compare_schemas,
    get_tables_from_migration_files,
    has_changes,
)
from jetbase.engine.schema_introspection import introspect_database
from jetbase.engine.version import get_migration_filepaths_by_version
from jetbase.engine.sql_generator import (
    generate_add_column_sql,
    generate_add_foreign_key_sql,
    generate_create_index_sql,
    generate_drop_column_sql,
    generate_drop_foreign_key_sql,
    generate_drop_index_sql,
    generate_drop_table_sql,
    get_db_type,
)


class MakeMigrationsError(Exception):
    """Base exception for make-migrations errors."""

    pass


class NoChangesDetectedError(MakeMigrationsError):
    """Raised when no schema changes are detected."""

    pass


def _generate_create_table_from_model(
    model_class, connection: Union[Connection, AsyncConnection]
) -> str:
    """
    Generate CREATE TABLE SQL from a SQLAlchemy model class.

    Args:
        model_class: The SQLAlchemy model class.
        connection: Database connection (sync or async).

    Returns:
        str: CREATE TABLE SQL statement.
    """
    table = model_class.__table__

    columns = []
    foreign_keys = []
    for col in table.columns:
        col_def = f"{col.name} {col.type.compile(dialect=connection.engine.dialect)}"
        if not col.nullable:
            col_def += " NOT NULL"
        if col.primary_key:
            col_def += " PRIMARY KEY"
        columns.append(col_def)
        if col.foreign_keys:
            for fk in col.foreign_keys:
                fk_def = f"FOREIGN KEY ({col.name}) REFERENCES {fk.column.table.name} ({fk.column.name})"
                foreign_keys.append(fk_def)

    pk_cols = ", ".join([c.name for c in table.primary_key.columns])
    cols_sql = ",\n    ".join(columns + foreign_keys)
    return f"CREATE TABLE {table.name} (\n    {cols_sql}\n);"


def make_migrations_cmd(description: str | None = None) -> None:
    """
    Generate migration files automatically from model definitions.

    This command:
    1. Reads model paths from config/env var or auto-discovers from model/models directories
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
    from jetbase.config import get_config

    try:
        _, models = discover_all_models()
    except ModelDiscoveryError as e:
        raise MakeMigrationsError(f"Failed to discover models: {e}")

    sqlalchemy_url = get_config(required={"sqlalchemy_url"}).sqlalchemy_url

    jetbase_dir = find_jetbase_directory()
    if jetbase_dir:
        migrations_dir = os.path.join(jetbase_dir, MIGRATIONS_DIR)
    else:
        migrations_dir = os.path.join(os.getcwd(), MIGRATIONS_DIR)

    existing_migration_files = list(
        get_migration_filepaths_by_version(migrations_dir).values()
    )
    already_migrated_tables = get_tables_from_migration_files(existing_migration_files)

    if is_async_enabled():
        asyncio.run(
            _make_migrations_async(models, description, already_migrated_tables)
        )
    else:
        _make_migrations_sync(models, description, already_migrated_tables)


def _make_migrations_sync(
    models: dict, description: str | None, already_migrated_tables: set[str]
) -> None:
    """
    Generate migrations using sync database connection.
    """
    try:
        with get_connection() as connection:
            database_schema = introspect_database(connection)
    except Exception as e:
        raise MakeMigrationsError(f"Failed to introspect database: {e}")

    diff = compare_schemas(models, database_schema, connection, already_migrated_tables)

    if not has_changes(diff):
        print("No changes detected.")
        return

    db_type = get_db_type()

    upgrade_statements = []
    rollback_statements = []

    with get_connection() as connection:
        for table_name in diff.tables_to_create:
            model_class = models[table_name]
            sql = _generate_create_table_from_model(model_class, connection)
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
            if db_type == DatabaseType.SQLITE:
                continue
            for fk_info in diff.foreign_keys_to_create[table_name]:
                upgrade_statements.append(
                    generate_add_foreign_key_sql(table_name, fk_info, db_type)
                )
                rollback_statements.append(
                    generate_drop_foreign_key_sql(table_name, fk_info["name"], db_type)
                )

    _write_migration_file(upgrade_statements, rollback_statements, description)


async def _make_migrations_async(
    models: dict, description: str | None, already_migrated_tables: set[str]
) -> None:
    """
    Generate migrations using async database connection.

    Note: Schema introspection uses a sync connection because async introspection
    is more complex and schema reading doesn't need to be async.
    """
    from sqlalchemy import create_engine

    from jetbase.config import get_config

    try:
        config = get_config()
        sync_url = (
            config.sqlalchemy_url.replace("+asyncpg", "")
            .replace("+async", "")
            .replace("+aiosqlite", "")
        )
        sync_url = sync_url.replace("postgresql+asyncpg:", "postgresql:").replace(
            "sqlite+aiosqlite:", "sqlite:"
        )
        engine = create_engine(sync_url)
        with engine.connect() as sync_conn:
            database_schema = introspect_database(sync_conn)
    except Exception as e:
        raise MakeMigrationsError(f"Failed to introspect database: {e}")

    diff = compare_schemas(models, database_schema, sync_conn, already_migrated_tables)

    if not has_changes(diff):
        print("No changes detected.")
        return

    db_type = get_db_type()

    upgrade_statements = []
    rollback_statements = []

    async with get_async_db_connection() as connection:
        for table_name in diff.tables_to_create:
            model_class = models[table_name]
            sql = _generate_create_table_from_model(model_class, connection)
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
            if db_type == DatabaseType.SQLITE:
                continue
            for fk_info in diff.foreign_keys_to_create[table_name]:
                upgrade_statements.append(
                    generate_add_foreign_key_sql(table_name, fk_info, db_type)
                )
                rollback_statements.append(
                    generate_drop_foreign_key_sql(table_name, fk_info["name"], db_type)
                )

    _write_migration_file(upgrade_statements, rollback_statements, description)


def _write_migration_file(
    upgrade_statements: list[str],
    rollback_statements: list[str],
    description: str | None,
) -> None:
    """
    Write the migration file to disk.
    """
    upgrade_sql = "\n\n".join(upgrade_statements)
    rollback_sql = "\n\n".join(rollback_statements)

    migration_description = description or "auto_generated"

    filename = _generate_new_filename(description=migration_description)
    jetbase_dir = find_jetbase_directory()
    if jetbase_dir:
        migrations_dir = os.path.join(jetbase_dir, MIGRATIONS_DIR)
    else:
        migrations_dir = os.path.join(os.getcwd(), MIGRATIONS_DIR)
    os.makedirs(migrations_dir, exist_ok=True)
    filepath = os.path.join(migrations_dir, filename)

    migration_content = f"""-- upgrade

{upgrade_sql}

-- rollback

{rollback_sql}
"""

    with open(filepath, "w") as f:
        f.write(migration_content)

    print(f"Created migration file: {filename}")
