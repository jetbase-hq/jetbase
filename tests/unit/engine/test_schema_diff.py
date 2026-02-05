from unittest.mock import MagicMock

import pytest
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base

from jetbase.engine.schema_diff import (
    SchemaDiff,
    compare_schemas,
    compare_tables,
    get_model_table_columns,
    get_model_table_info,
    get_models_schema_info,
    get_tables_from_migration_files,
    has_changes,
)
from jetbase.engine.schema_introspection import (
    ColumnInfo,
    SchemaInfo,
    TableInfo,
)


Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)


class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)


def test_schema_diff_defaults():
    """Test SchemaDiff default values."""
    diff = SchemaDiff()

    assert diff.tables_to_create == []
    assert diff.tables_to_drop == []
    assert diff.columns_to_add == {}
    assert diff.columns_to_remove == {}
    assert diff.columns_to_modify == {}
    assert diff.indexes_to_create == {}
    assert diff.indexes_to_drop == {}


def test_schema_diff_with_values():
    """Test SchemaDiff with values."""
    diff = SchemaDiff(
        tables_to_create=["new_table"],
        tables_to_drop=["old_table"],
        columns_to_add={
            "users": [ColumnInfo("age", "INTEGER", True, None, False, False)]
        },
        columns_to_remove={"users": ["old_col"]},
    )

    assert diff.tables_to_create == ["new_table"]
    assert diff.tables_to_drop == ["old_table"]
    assert "users" in diff.columns_to_add
    assert "users" in diff.columns_to_remove


def test_get_model_table_columns():
    """Test extracting columns from model."""
    columns = get_model_table_columns(UserModel)

    column_names = [col.name for col in columns]
    assert "id" in column_names
    assert "email" in column_names
    assert "name" in column_names


def test_get_model_table_columns_pk():
    """Test that primary key is detected."""
    columns = get_model_table_columns(UserModel)

    for col in columns:
        if col.name == "id":
            assert col.primary_key is True
        else:
            assert col.primary_key is False


def test_get_model_table_columns_nullable():
    """Test that nullable is detected."""
    columns = get_model_table_columns(UserModel)

    for col in columns:
        if col.name == "email":
            assert col.nullable is False
        elif col.name == "name":
            assert col.nullable is True


def test_get_model_table_info():
    """Test extracting table info from model."""
    table_info = get_model_table_info(UserModel)

    assert table_info.name == "users"
    assert len(table_info.columns) >= 2
    assert "id" in table_info.primary_keys


def test_get_models_schema_info():
    """Test extracting schema info from multiple models."""
    models = {
        "users": UserModel,
        "products": ProductModel,
    }

    schema_info = get_models_schema_info(models)

    assert "users" in schema_info
    assert "products" in schema_info
    assert schema_info["users"].name == "users"
    assert schema_info["products"].name == "products"


def test_compare_schemas_no_changes():
    """Test comparing identical schemas."""
    models = {"users": UserModel}
    database_schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                    ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
                    ColumnInfo("name", "VARCHAR(100)", True, None, False, False),
                ],
                primary_keys=["id"],
            )
        }
    )

    connection = MagicMock()

    diff = compare_schemas(models, database_schema, connection)

    assert diff.tables_to_create == []
    assert diff.tables_to_drop == []
    assert not has_changes(diff)


def test_compare_schemas_new_table():
    """Test detecting new tables."""
    models = {"users": UserModel, "products": ProductModel}
    database_schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                    ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
                ],
                primary_keys=["id"],
            )
        }
    )

    connection = MagicMock()

    diff = compare_schemas(models, database_schema, connection)

    assert "products" in diff.tables_to_create
    assert "products" == diff.tables_to_create[0]


def test_compare_schemas_dropped_table():
    """Test detecting tables to drop."""
    models = {"users": UserModel}
    database_schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                    ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
                ],
                primary_keys=["id"],
            ),
            "old_table": TableInfo(
                name="old_table",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                ],
                primary_keys=["id"],
            ),
        }
    )

    connection = MagicMock()

    diff = compare_schemas(models, database_schema, connection)

    assert "old_table" in diff.tables_to_drop


def test_compare_schemas_new_column():
    """Test detecting new columns."""
    models = {"users": UserModel}
    database_schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                ],
                primary_keys=["id"],
            )
        }
    )

    connection = MagicMock()

    diff = compare_schemas(models, database_schema, connection)

    assert "users" in diff.columns_to_add
    column_names = [col.name for col in diff.columns_to_add["users"]]
    assert "email" in column_names
    assert "name" in column_names


def test_compare_schemas_removed_column():
    """Test detecting removed columns."""
    models = {"users": UserModel}
    database_schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo("id", "INTEGER", False, None, True, False),
                    ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
                    ColumnInfo("old_column", "INTEGER", True, None, False, False),
                ],
                primary_keys=["id"],
            )
        }
    )

    connection = MagicMock()

    diff = compare_schemas(models, database_schema, connection)

    assert "users" in diff.columns_to_remove
    assert "old_column" in diff.columns_to_remove["users"]


def test_compare_tables():
    """Test comparing individual tables."""
    model_table = TableInfo(
        name="users",
        columns=[
            ColumnInfo("id", "INTEGER", False, None, True, False),
            ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
        ],
        primary_keys=["id"],
    )

    db_table = TableInfo(
        name="users",
        columns=[
            ColumnInfo("id", "INTEGER", False, None, True, False),
        ],
        primary_keys=["id"],
    )

    diff = SchemaDiff()
    compare_tables(model_table, db_table, diff, "users")

    assert "users" in diff.columns_to_add
    assert "email" in [col.name for col in diff.columns_to_add["users"]]


def test_has_changes():
    """Test has_changes function."""
    diff_no_changes = SchemaDiff()
    assert has_changes(diff_no_changes) is False

    diff_with_changes = SchemaDiff(tables_to_create=["new_table"])
    assert has_changes(diff_with_changes) is True

    diff_with_column_changes = SchemaDiff(
        columns_to_add={
            "users": [ColumnInfo("new", "INTEGER", True, None, False, False)]
        }
    )
    assert has_changes(diff_with_column_changes) is True


def test_get_tables_from_migration_files(tmp_path):
    """Test extracting table names from migration files."""
    from jetbase.constants import MIGRATIONS_DIR

    migrations_dir = tmp_path / MIGRATIONS_DIR
    migrations_dir.mkdir()

    migration_content = """-- upgrade

CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

CREATE TABLE products (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(255) NOT NULL
);

-- rollback

DROP TABLE users;

DROP TABLE products;
"""
    migration_file = migrations_dir / "V1__test.sql"
    migration_file.write_text(migration_content)

    tables = get_tables_from_migration_files([str(migration_file)])

    assert "users" in tables
    assert "products" in tables


def test_compare_schemas_with_already_migrated_tables():
    """Test that compare_schemas excludes already migrated tables."""
    models = {"users": UserModel, "products": ProductModel}
    database_schema = SchemaInfo(tables={})

    connection = MagicMock()

    diff = compare_schemas(
        models, database_schema, connection, already_migrated_tables={"users"}
    )

    assert "users" not in diff.tables_to_create
    assert "products" in diff.tables_to_create
