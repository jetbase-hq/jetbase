from typing import Any

from sqlalchemy import Table, create_engine, text
from sqlalchemy.engine import Connection

from jetbase.config import get_config
from jetbase.database.queries.base import detect_db
from jetbase.engine.schema_diff import SchemaDiff
from jetbase.engine.schema_introspection import ColumnInfo
from jetbase.enums import DatabaseType


class SQLGeneratorError(Exception):
    """Base exception for SQL generation errors."""

    pass


def get_db_type() -> DatabaseType:
    """
    Get the current database type.

    Returns:
        DatabaseType: The detected database type.
    """
    sqlalchemy_url = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    return detect_db(sqlalchemy_url=sqlalchemy_url)


def sql_type_to_string(col_type: str, db_type: DatabaseType) -> str:
    """
    Convert a SQLAlchemy column type to a database-specific SQL string.

    Args:
        col_type (str): The SQLAlchemy column type string.
        db_type (DatabaseType): The target database type.

    Returns:
        str: The database-specific SQL type string.
    """
    type_map = {
        DatabaseType.POSTGRESQL: {
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "smallint": "SMALLINT",
            "float": "DOUBLE PRECISION",
            "numeric": "NUMERIC",
            "decimal": "DECIMAL",
            "varchar": "VARCHAR",
            "char": "CHAR",
            "text": "TEXT",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
            "time": "TIME",
            "json": "JSONB",
            "uuid": "UUID",
            "bytea": "BYTEA",
        },
        DatabaseType.MYSQL: {
            "integer": "INT",
            "bigint": "BIGINT",
            "smallint": "SMALLINT",
            "float": "DOUBLE",
            "numeric": "DECIMAL",
            "decimal": "DECIMAL",
            "varchar": "VARCHAR",
            "char": "CHAR",
            "text": "TEXT",
            "boolean": "TINYINT(1)",
            "date": "DATE",
            "datetime": "DATETIME",
            "timestamp": "TIMESTAMP",
            "time": "TIME",
            "json": "JSON",
            "uuid": "CHAR(36)",
            "bytea": "BLOB",
        },
        DatabaseType.SQLITE: {
            "integer": "INTEGER",
            "bigint": "INTEGER",
            "smallint": "INTEGER",
            "float": "REAL",
            "numeric": "NUMERIC",
            "decimal": "NUMERIC",
            "varchar": "TEXT",
            "char": "TEXT",
            "text": "TEXT",
            "boolean": "INTEGER",
            "date": "TEXT",
            "datetime": "TEXT",
            "timestamp": "TEXT",
            "time": "TEXT",
            "json": "TEXT",
            "uuid": "TEXT",
            "bytea": "BLOB",
        },
        DatabaseType.SNOWFLAKE: {
            "integer": "INTEGER",
            "bigint": "BIGINT",
            "smallint": "INTEGER",
            "float": "FLOAT",
            "numeric": "NUMERIC",
            "decimal": "DECIMAL",
            "varchar": "VARCHAR",
            "char": "CHAR",
            "text": "TEXT",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
            "time": "TIME",
            "json": "VARIANT",
            "uuid": "UUID",
            "bytea": "BINARY",
        },
        DatabaseType.DATABRICKS: {
            "integer": "INT",
            "bigint": "BIGINT",
            "smallint": "SMALLINT",
            "float": "DOUBLE",
            "numeric": "DECIMAL",
            "decimal": "DECIMAL",
            "varchar": "STRING",
            "char": "STRING",
            "text": "STRING",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "timestamp": "TIMESTAMP",
            "time": "STRING",
            "json": "STRING",
            "uuid": "STRING",
            "bytea": "BINARY",
        },
    }

    type_lower = col_type.lower()

    if "(" in type_lower:
        base_type = type_lower.split("(")[0].strip()
        if base_type in type_map.get(db_type, {}):
            params = type_lower.split("(")[1].rstrip(")")
            return f"{type_map[db_type][base_type]}({params})"
    else:
        if type_lower in type_map.get(db_type, {}):
            return type_map[db_type][type_lower]

    return col_type.upper()


def generate_create_table_sql(
    table_name: str,
    columns: list[ColumnInfo],
    primary_keys: list[str],
    db_type: DatabaseType,
) -> str:
    """
    Generate CREATE TABLE SQL statement.

    Args:
        table_name (str): Name of the table to create.
        columns (list[ColumnInfo]): List of column definitions.
        primary_keys (list[str]): List of primary key column names.
        db_type (DatabaseType): The database type.

    Returns:
        str: CREATE TABLE SQL statement.
    """
    col_defs = []

    for col in columns:
        col_sql = f"{col.name} {sql_type_to_string(col.type, db_type)}"

        if col.primary_key:
            pass
        elif not col.nullable:
            col_sql += " NOT NULL"

        if col.default:
            if db_type == DatabaseType.POSTGRESQL:
                col_sql += f" DEFAULT {col.default}"
            elif db_type == DatabaseType.MYSQL:
                col_sql += f" DEFAULT {col.default}"
            elif db_type == DatabaseType.SQLITE:
                if "CURRENT_TIMESTAMP" in str(col.default):
                    col_sql += " DEFAULT CURRENT_TIMESTAMP"
            elif db_type == DatabaseType.SNOWFLAKE:
                col_sql += f" DEFAULT {col.default}"
            elif db_type == DatabaseType.DATABRICKS:
                col_sql += f" DEFAULT {col.default}"

        col_defs.append(col_sql)

    if primary_keys:
        pk_cols = ", ".join(primary_keys)
        col_defs.append(f"PRIMARY KEY ({pk_cols})")

    cols_sql = ",\n    ".join(col_defs)

    if db_type == DatabaseType.POSTGRESQL:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n);"
    elif db_type == DatabaseType.MYSQL:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
    elif db_type == DatabaseType.SQLITE:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n);"
    elif db_type == DatabaseType.SNOWFLAKE:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n);"
    elif db_type == DatabaseType.DATABRICKS:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n);"
    else:
        return f"CREATE TABLE {table_name} (\n    {cols_sql}\n);"


def generate_drop_table_sql(table_name: str, db_type: DatabaseType) -> str:
    """
    Generate DROP TABLE SQL statement.

    Args:
        table_name (str): Name of the table to drop.
        db_type (DatabaseType): The database type.

    Returns:
        str: DROP TABLE SQL statement.
    """
    if db_type == DatabaseType.DATABRICKS:
        return f"DROP TABLE IF EXISTS {table_name};"
    return f"DROP TABLE {table_name};"


def generate_add_column_sql(
    table_name: str,
    column: ColumnInfo,
    db_type: DatabaseType,
) -> str:
    """
    Generate ALTER TABLE ADD COLUMN SQL statement.

    Args:
        table_name (str): Name of the table.
        column (ColumnInfo): Column to add.
        db_type (DatabaseType): The database type.

    Returns:
        str: ALTER TABLE ADD COLUMN SQL statement.
    """
    col_sql = f"{column.name} {sql_type_to_string(column.type, db_type)}"

    if not column.nullable:
        col_sql += " NOT NULL"

    if column.default:
        if db_type == DatabaseType.POSTGRESQL:
            col_sql += f" DEFAULT {column.default}"
        elif db_type == DatabaseType.MYSQL:
            col_sql += f" DEFAULT {column.default}"
        elif db_type == DatabaseType.SQLITE:
            if "CURRENT_TIMESTAMP" in str(column.default):
                col_sql += " DEFAULT CURRENT_TIMESTAMP"
        elif db_type == DatabaseType.SNOWFLAKE:
            col_sql += f" DEFAULT {column.default}"
        elif db_type == DatabaseType.DATABRICKS:
            col_sql += f" DEFAULT {column.default}"

    return f"ALTER TABLE {table_name} ADD COLUMN {col_sql};"


def generate_drop_column_sql(
    table_name: str, column_name: str, db_type: DatabaseType
) -> str:
    """
    Generate ALTER TABLE DROP COLUMN SQL statement.

    Args:
        table_name (str): Name of the table.
        column_name (str): Name of the column to drop.
        db_type (DatabaseType): The database type.

    Returns:
        str: ALTER TABLE DROP COLUMN SQL statement.
    """
    if db_type == DatabaseType.DATABRICKS:
        return f"ALTER TABLE {table_name} DROP COLUMN {column_name};"
    return f"ALTER TABLE {table_name} DROP COLUMN {column_name};"


def generate_create_index_sql(
    table_name: str,
    index_info: dict[str, Any],
    db_type: DatabaseType,
) -> str:
    """
    Generate CREATE INDEX SQL statement.

    Args:
        table_name (str): Name of the table.
        index_info (dict): Index information.
        db_type (DatabaseType): The database type.

    Returns:
        str: CREATE INDEX SQL statement.
    """
    index_name = index_info["name"]
    columns = ", ".join(index_info["column_names"])

    if index_info.get("unique"):
        if db_type == DatabaseType.DATABRICKS:
            return f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({columns});"
        return f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({columns});"
    else:
        return f"CREATE INDEX {index_name} ON {table_name} ({columns});"


def generate_drop_index_sql(
    index_name: str, table_name: str, db_type: DatabaseType
) -> str:
    """
    Generate DROP INDEX SQL statement.

    Args:
        index_name (str): Name of the index.
        table_name (str): Name of the table.
        db_type (DatabaseType): The database type.

    Returns:
        str: DROP INDEX SQL statement.
    """
    if db_type == DatabaseType.DATABRICKS:
        return f"DROP INDEX {index_name} ON {table_name};"
    return f"DROP INDEX {index_name} ON {table_name};"


def generate_add_foreign_key_sql(
    table_name: str,
    fk_info: dict[str, Any],
    db_type: DatabaseType,
) -> str:
    """
    Generate ALTER TABLE ADD FOREIGN KEY SQL statement.

    Args:
        table_name (str): Name of the table.
        fk_info (dict): Foreign key information.
        db_type (DatabaseType): The database type.

    Returns:
        str: ALTER TABLE ADD FOREIGN KEY SQL statement.
    """
    fk_name = fk_info.get("name")
    columns = ", ".join(fk_info["constrained_columns"])
    ref_table = fk_info["referred_table"]
    ref_columns = ", ".join(fk_info["referred_columns"])

    if fk_name:
        return (
            f"ALTER TABLE {table_name} ADD CONSTRAINT {fk_name} "
            f"FOREIGN KEY ({columns}) REFERENCES {ref_table} ({ref_columns});"
        )
    else:
        return (
            f"ALTER TABLE {table_name} ADD FOREIGN KEY ({columns}) "
            f"REFERENCES {ref_table} ({ref_columns});"
        )


def generate_drop_foreign_key_sql(
    table_name: str,
    fk_name: str,
    db_type: DatabaseType,
) -> str:
    """
    Generate ALTER TABLE DROP FOREIGN KEY SQL statement.

    Args:
        table_name (str): Name of the table.
        fk_name (str): Name of the foreign key constraint.
        db_type (DatabaseType): The database type.

    Returns:
        str: ALTER TABLE DROP FOREIGN KEY SQL statement.
    """
    return f"ALTER TABLE {table_name} DROP CONSTRAINT {fk_name};"


def generate_upgrade_sql(diff: SchemaDiff, db_type: DatabaseType) -> str:
    """
    Generate the upgrade SQL from a schema diff.

    Args:
        diff (SchemaDiff): The schema diff.
        db_type (DatabaseType): The database type.

    Returns:
        str: Complete upgrade SQL statement.
    """
    statements = []

    for table_name in diff.tables_to_create:
        pass

    for table_name in diff.columns_to_add:
        for column in diff.columns_to_add[table_name]:
            statements.append(generate_add_column_sql(table_name, column, db_type))

    for table_name in diff.indexes_to_create:
        for index_info in diff.indexes_to_create[table_name]:
            statements.append(
                generate_create_index_sql(table_name, index_info, db_type)
            )

    for table_name in diff.foreign_keys_to_create:
        for fk_info in diff.foreign_keys_to_create[table_name]:
            statements.append(
                generate_add_foreign_key_sql(table_name, fk_info, db_type)
            )

    return "\n\n".join(statements)


def generate_rollback_sql(diff: SchemaDiff, db_type: DatabaseType) -> str:
    """
    Generate the rollback SQL from a schema diff.

    Args:
        diff (SchemaDiff): The schema diff.
        db_type (DatabaseType): The database type.

    Returns:
        str: Complete rollback SQL statement.
    """
    statements = []

    for table_name in reversed(diff.tables_to_create):
        statements.append(generate_drop_table_sql(table_name, db_type))

    for table_name in diff.foreign_keys_to_drop:
        for fk_name in diff.foreign_keys_to_drop[table_name]:
            statements.append(
                generate_drop_foreign_key_sql(table_name, fk_name, db_type)
            )

    for table_name in diff.indexes_to_drop:
        for index_name in diff.indexes_to_drop[table_name]:
            statements.append(generate_drop_index_sql(index_name, table_name, db_type))

    for table_name in diff.columns_to_remove:
        for column_name in diff.columns_to_remove[table_name]:
            statements.append(
                generate_drop_column_sql(table_name, column_name, db_type)
            )

    for table_name in diff.columns_to_add:
        for column in diff.columns_to_add[table_name]:
            statements.append(
                generate_drop_column_sql(table_name, column.name, db_type)
            )

    return "\n\n".join(statements)


def generate_migration_sql(diff: SchemaDiff) -> tuple[str, str]:
    """
    Generate both upgrade and rollback SQL from a schema diff.

    Args:
        diff (SchemaDiff): The schema diff.

    Returns:
        tuple: (upgrade_sql, rollback_sql)
    """
    db_type = get_db_type()
    upgrade_sql = generate_upgrade_sql(diff, db_type)
    rollback_sql = generate_rollback_sql(diff, db_type)
    return upgrade_sql, rollback_sql
