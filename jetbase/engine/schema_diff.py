from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Column
from sqlalchemy.engine import Connection

from jetbase.engine.schema_introspection import (
    ColumnInfo,
    SchemaInfo,
    TableInfo,
    introspect_database,
)


@dataclass
class SchemaDiff:
    """Represents the differences between model schema and database schema."""

    tables_to_create: list[str] = field(default_factory=list)
    tables_to_drop: list[str] = field(default_factory=list)
    columns_to_add: dict[str, list[ColumnInfo]] = field(default_factory=dict)
    columns_to_remove: dict[str, list[str]] = field(default_factory=dict)
    columns_to_modify: dict[str, dict[str, tuple[ColumnInfo, ColumnInfo]]] = field(
        default_factory=dict
    )
    indexes_to_create: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    indexes_to_drop: dict[str, list[str]] = field(default_factory=dict)
    foreign_keys_to_create: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )
    foreign_keys_to_drop: dict[str, list[str]] = field(default_factory=dict)


def get_model_table_columns(model_class: type) -> list[ColumnInfo]:
    """
    Extract column information from a SQLAlchemy model class.

    Args:
        model_class: The SQLAlchemy model class.

    Returns:
        list[ColumnInfo]: List of column information.
    """
    columns = []
    for column in model_class.__table__.columns:
        col_info = ColumnInfo(
            name=column.name,
            type=str(column.type),
            nullable=column.nullable,
            default=str(column.default) if column.default else None,
            primary_key=column.primary_key,
            autoincrement=column.autoincrement
            if hasattr(column, "autoincrement")
            else False,
        )
        columns.append(col_info)
    return columns


def get_model_table_info(model_class: type) -> TableInfo:
    """
    Extract table information from a SQLAlchemy model class.

    Args:
        model_class: The SQLAlchemy model class.

    Returns:
        TableInfo: Table information extracted from the model.
    """
    table = model_class.__table__
    table_info = TableInfo(
        name=table.name,
        columns=get_model_table_columns(model_class),
        primary_keys=[c.name for c in table.primary_key.columns],
    )

    for fk in table.foreign_keys:
        constrained_columns = [c.name for c in table.c if c.foreign_keys]
        table_info.foreign_keys.append(
            {
                "name": fk.name,
                "constrained_columns": constrained_columns,
                "referred_table": fk.column.table.name,
                "referred_columns": [
                    c.name for c in fk.column.table.primary_key.columns
                ],
            }
        )

    for index in table.indexes:
        table_info.indexes.append(
            {
                "name": index.name,
                "column_names": list(index.columns),
                "unique": index.unique,
            }
        )

    return table_info


def get_models_schema_info(models: dict[str, type]) -> dict[str, TableInfo]:
    """
    Get schema information from model classes.

    Args:
        models (dict[str, type]): Dictionary mapping table names to model classes.

    Returns:
        dict[str, TableInfo]: Dictionary mapping table names to TableInfo.
    """
    return {
        table_name: get_model_table_info(model_class)
        for table_name, model_class in models.items()
    }


def compare_schemas(
    models: dict[str, type],
    database_schema: SchemaInfo,
    connection: Connection,
) -> SchemaDiff:
    """
    Compare model schema against database schema to detect differences.

    Args:
        models (dict[str, type]): Dictionary mapping table names to model classes.
        database_schema (SchemaInfo): The current database schema.
        connection (Connection): Database connection.

    Returns:
        SchemaDiff: Object containing all detected differences.
    """
    diff = SchemaDiff()
    models_schema = get_models_schema_info(models)

    model_table_names = set(models_schema.keys())
    db_table_names = set(database_schema.tables.keys())

    diff.tables_to_create = sorted(list(model_table_names - db_table_names))
    diff.tables_to_drop = sorted(list(db_table_names - model_table_names))

    for table_name in model_table_names & db_table_names:
        model_table = models_schema[table_name]
        db_table = database_schema.tables[table_name]

        compare_tables(model_table, db_table, diff, table_name)

    return diff


def compare_tables(
    model_table: TableInfo,
    db_table: TableInfo,
    diff: SchemaDiff,
    table_name: str,
) -> None:
    """
    Compare a single model's table against the database table.

    Args:
        model_table (TableInfo): The model's table definition.
        db_table (TableInfo): The database table definition.
        diff (SchemaDiff): The diff object to update.
        table_name (str): Name of the table being compared.
    """
    model_column_map = {col.name: col for col in model_table.columns}
    db_column_map = {col.name: col for col in db_table.columns}

    columns_to_add = [
        col for col in model_table.columns if col.name not in db_column_map
    ]
    if columns_to_add:
        diff.columns_to_add[table_name] = columns_to_add

    columns_to_remove = [
        col.name for col in db_table.columns if col.name not in model_column_map
    ]
    if columns_to_remove:
        diff.columns_to_remove[table_name] = columns_to_remove

    columns_to_modify = {}
    for col_name in model_column_map:
        if col_name in db_column_map:
            model_col = model_column_map[col_name]
            db_col = db_column_map[col_name]
            if not columns_match(model_col, db_col):
                columns_to_modify[col_name] = (model_col, db_col)
    if columns_to_modify:
        diff.columns_to_modify[table_name] = columns_to_modify

    model_fk_names = {fk["name"] for fk in model_table.foreign_keys}
    db_fk_names = {fk["name"] for fk in db_table.foreign_keys}

    fks_to_create = [
        fk for fk in model_table.foreign_keys if fk["name"] not in db_fk_names
    ]
    if fks_to_create:
        diff.foreign_keys_to_create[table_name] = fks_to_create

    fks_to_drop = [
        fk["name"] for fk in db_table.foreign_keys if fk["name"] not in model_fk_names
    ]
    if fks_to_drop:
        diff.foreign_keys_to_drop[table_name] = fks_to_drop

    model_index_names = {idx["name"] for idx in model_table.indexes}
    db_index_names = {idx["name"] for idx in db_table.indexes}

    indexes_to_create = [
        idx for idx in model_table.indexes if idx["name"] not in db_index_names
    ]
    if indexes_to_create:
        diff.indexes_to_create[table_name] = indexes_to_create

    indexes_to_drop = [
        idx["name"] for idx in db_table.indexes if idx["name"] not in model_index_names
    ]
    if indexes_to_drop:
        diff.indexes_to_drop[table_name] = indexes_to_drop


def columns_match(col1: ColumnInfo, col2: ColumnInfo) -> bool:
    """
    Check if two columns match in their essential properties.

    Args:
        col1 (ColumnInfo): First column.
        col2 (ColumnInfo): Second column.

    Returns:
        bool: True if columns match, False otherwise.
    """
    type1 = col1.type.lower()
    type2 = col2.type.lower()

    type1 = type1.replace("(", "").replace(")", "").replace(" ", "")
    type2 = type2.replace("(", "").replace(")", "").replace(" ", "")

    return (
        type1 == type2
        and col1.nullable == col2.nullable
        and col1.primary_key == col2.primary_key
    )


def has_changes(diff: SchemaDiff) -> bool:
    """
    Check if the schema diff contains any changes.

    Args:
        diff (SchemaDiff): The schema diff to check.

    Returns:
        bool: True if there are changes, False otherwise.
    """
    return (
        bool(diff.tables_to_create)
        or bool(diff.tables_to_drop)
        or bool(diff.columns_to_add)
        or bool(diff.columns_to_remove)
        or bool(diff.columns_to_modify)
        or bool(diff.indexes_to_create)
        or bool(diff.indexes_to_drop)
        or bool(diff.foreign_keys_to_create)
        or bool(diff.foreign_keys_to_drop)
    )
