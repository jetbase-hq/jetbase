from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.engine import Inspector

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection

from jetbase.config import get_config
from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType


@dataclass
class ColumnInfo:
    """Represents information about a database column."""

    name: str
    type: str
    nullable: bool
    default: str | None
    primary_key: bool
    autoincrement: bool


@dataclass
class TableInfo:
    """Represents information about a database table."""

    name: str
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[dict[str, Any]] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    unique_constraints: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SchemaInfo:
    """Represents the complete database schema."""

    tables: dict[str, TableInfo] = field(default_factory=dict)


class SchemaIntrospectionError(Exception):
    """Base exception for schema introspection errors."""

    pass


class DatabaseConnectionError(SchemaIntrospectionError):
    """Raised when database connection fails."""

    pass


def get_inspector() -> "Inspector":
    """
    Get a SQLAlchemy Inspector for the configured database.

    Returns:
        Inspector: SQLAlchemy Inspector object.

    Raises:
        DatabaseConnectionError: If database connection fails.
    """
    try:
        sqlalchemy_url = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
        engine = create_engine(sqlalchemy_url)
        return inspect(engine)
    except Exception as e:
        raise DatabaseConnectionError(f"Failed to connect to database: {e}")


def introspect_database(
    connection: Connection, schema: str | None = None
) -> SchemaInfo:
    """
    Introspect the current database schema.

    Args:
        connection (Connection): SQLAlchemy database connection.
        schema (str | None): Optional schema name for PostgreSQL.

    Returns:
        SchemaInfo: Object containing all schema information.
    """
    inspector = inspect(connection)
    schema_info = SchemaInfo()

    db_type = detect_db(sqlalchemy_url=str(connection.engine.url))

    if db_type == DatabaseType.POSTGRESQL:
        schema = schema or get_config().postgres_schema or "public"

    table_names = inspector.get_table_names(schema=schema)

    for table_name in table_names:
        table_info = introspect_table(inspector, table_name, schema)
        schema_info.tables[table_name] = table_info

    return schema_info


def introspect_table(
    inspector: "Inspector", table_name: str, schema: str | None = None
) -> TableInfo:
    """
    Introspect a single table.

    Args:
        inspector (Inspector): SQLAlchemy Inspector.
        table_name (str): Name of the table to introspect.
        schema (str | None): Optional schema name.

    Returns:
        TableInfo: Object containing table information.
    """
    columns = inspector.get_columns(table_name, schema=schema)
    pk_columns = inspector.get_pk_constraint(table_name, schema=schema)
    foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
    indexes = inspector.get_indexes(table_name, schema=schema)

    table_info = TableInfo(name=table_name)

    for col in columns:
        column_info = ColumnInfo(
            name=col["name"],
            type=str(col["type"]),
            nullable=col.get("nullable", True),
            default=str(col.get("default")) if col.get("default") else None,
            primary_key=col["name"] in pk_columns.get("constrained_columns", []),
            autoincrement=col.get("autoincrement", False),
        )
        table_info.columns.append(column_info)

    table_info.primary_keys = pk_columns.get("constrained_columns", [])
    table_info.foreign_keys = [
        {
            "name": fk["name"],
            "constrained_columns": fk["constrained_columns"],
            "referred_table": fk["referred_table"],
            "referred_columns": fk["referred_columns"],
        }
        for fk in foreign_keys
    ]

    table_info.indexes = [
        {
            "name": idx["name"],
            "column_names": idx["column_names"],
            "unique": idx.get("unique", False),
        }
        for idx in indexes
        if not idx.get("primary_key", False)
    ]

    unique_constraints = inspector.get_unique_constraints(table_name, schema=schema)
    table_info.unique_constraints = [
        {
            "name": uc["name"],
            "column_names": uc["column_names"],
        }
        for uc in unique_constraints
    ]

    return table_info


def compare_column(col1: ColumnInfo, col2: ColumnInfo) -> bool:
    """
    Compare two columns for equality.

    Args:
        col1 (ColumnInfo): First column.
        col2 (ColumnInfo): Second column.

    Returns:
        bool: True if columns are equivalent, False otherwise.
    """
    return (
        col1.name == col2.name
        and col1.type.lower() == col2.type.lower()
        and col1.nullable == col2.nullable
        and col1.primary_key == col2.primary_key
    )


def schema_info_to_dict(schema_info: SchemaInfo) -> dict[str, Any]:
    """
    Convert SchemaInfo to a serializable dictionary.

    Args:
        schema_info (SchemaInfo): The schema information.

    Returns:
        dict: Serializable dictionary representation.
    """
    result = {"tables": {}}

    for table_name, table in schema_info.tables.items():
        result["tables"][table_name] = {
            "columns": [
                {
                    "name": col.name,
                    "type": col.type,
                    "nullable": col.nullable,
                    "default": col.default,
                    "primary_key": col.primary_key,
                    "autoincrement": col.autoincrement,
                }
                for col in table.columns
            ],
            "primary_keys": table.primary_keys,
            "foreign_keys": table.foreign_keys,
            "indexes": table.indexes,
            "unique_constraints": table.unique_constraints,
        }

    return result
