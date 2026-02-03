import tempfile
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, Integer, String, create_engine, inspect, text
from sqlalchemy.orm import declarative_base

from jetbase.engine.schema_introspection import (
    ColumnInfo,
    SchemaInfo,
    TableInfo,
    compare_column,
    introspect_database,
    introspect_table,
    schema_info_to_dict,
)


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)


@pytest.fixture
def sqlite_engine(tmp_path):
    """Create a SQLite engine for testing."""
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    return engine


@pytest.fixture
def populated_database(sqlite_engine):
    """Create a database with tables for testing."""
    Base.metadata.create_all(sqlite_engine)
    yield sqlite_engine


def test_column_info_creation():
    """Test ColumnInfo dataclass creation."""
    col = ColumnInfo(
        name="id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=True,
    )

    assert col.name == "id"
    assert col.type == "INTEGER"
    assert col.nullable is False
    assert col.primary_key is True
    assert col.autoincrement is True


def test_table_info_creation():
    """Test TableInfo dataclass creation."""
    table = TableInfo(
        name="users",
        columns=[
            ColumnInfo(
                name="id",
                type="INTEGER",
                nullable=False,
                default=None,
                primary_key=True,
                autoincrement=False,
            )
        ],
        primary_keys=["id"],
    )

    assert table.name == "users"
    assert len(table.columns) == 1
    assert table.columns[0].name == "id"
    assert table.primary_keys == ["id"]


def test_schema_info_creation():
    """Test SchemaInfo dataclass creation."""
    schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[],
                primary_keys=[],
            )
        }
    )

    assert "users" in schema.tables
    assert schema.tables["users"].name == "users"


def test_compare_column_equal():
    """Test comparing identical columns."""
    col1 = ColumnInfo(
        name="id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )
    col2 = ColumnInfo(
        name="id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )

    assert compare_column(col1, col2) is True


def test_compare_column_different_name():
    """Test comparing columns with different names."""
    col1 = ColumnInfo(
        name="id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )
    col2 = ColumnInfo(
        name="user_id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )

    assert compare_column(col1, col2) is False


def test_compare_column_different_type():
    """Test comparing columns with different types."""
    col1 = ColumnInfo(
        name="id",
        type="INTEGER",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )
    col2 = ColumnInfo(
        name="id",
        type="VARCHAR(255)",
        nullable=False,
        default=None,
        primary_key=True,
        autoincrement=False,
    )

    assert compare_column(col1, col2) is False


def test_compare_column_different_nullability():
    """Test comparing columns with different nullability."""
    col1 = ColumnInfo(
        name="email",
        type="VARCHAR(255)",
        nullable=False,
        default=None,
        primary_key=False,
        autoincrement=False,
    )
    col2 = ColumnInfo(
        name="email",
        type="VARCHAR(255)",
        nullable=True,
        default=None,
        primary_key=False,
        autoincrement=False,
    )

    assert compare_column(col1, col2) is False


def test_schema_info_to_dict():
    """Test converting SchemaInfo to dictionary."""
    schema = SchemaInfo(
        tables={
            "users": TableInfo(
                name="users",
                columns=[
                    ColumnInfo(
                        name="id",
                        type="INTEGER",
                        nullable=False,
                        default=None,
                        primary_key=True,
                        autoincrement=True,
                    )
                ],
                primary_keys=["id"],
            )
        }
    )

    result = schema_info_to_dict(schema)

    assert "tables" in result
    assert "users" in result["tables"]
    assert len(result["tables"]["users"]["columns"]) == 1
    assert result["tables"]["users"]["columns"][0]["name"] == "id"


def test_introspect_empty_database(sqlite_engine):
    """Test introspecting an empty database."""
    with sqlite_engine.connect() as connection:
        schema = introspect_database(connection)

    assert len(schema.tables) == 0


def test_introspect_populated_database(populated_database):
    """Test introspecting a database with tables."""
    with populated_database.connect() as connection:
        schema = introspect_database(connection)

    assert "users" in schema.tables
    assert "products" in schema.tables


def test_introspect_table_columns(populated_database):
    """Test introspecting table columns."""
    inspector = inspect(populated_database)

    table_info = introspect_table(inspector, "users")

    assert table_info.name == "users"
    column_names = [col.name for col in table_info.columns]
    assert "id" in column_names
    assert "email" in column_names
    assert "name" in column_names


def test_introspect_table_primary_keys(populated_database):
    """Test introspecting table primary keys."""
    inspector = inspect(populated_database)

    table_info = introspect_table(inspector, "users")

    assert "id" in table_info.primary_keys


def test_introspect_table_foreign_keys(populated_database):
    """Test introspecting table foreign keys (empty in test case)."""
    inspector = inspect(populated_database)

    table_info = introspect_table(inspector, "users")

    assert table_info.foreign_keys == []


def test_introspect_table_indexes(populated_database):
    """Test introspecting table indexes."""
    inspector = inspect(populated_database)

    table_info = introspect_table(inspector, "users")

    assert isinstance(table_info.indexes, list)


def test_introspect_with_schema():
    """Test that introspect_table function accepts schema parameter."""
    with patch("jetbase.engine.schema_introspection.get_config") as mock_config:
        mock_config.return_value.postgres_schema = "public"

        with patch("jetbase.engine.schema_introspection.detect_db") as mock_detect:
            mock_detect.return_value = "postgresql"

            inspector = MagicMock()
            inspector.get_columns.return_value = []
            inspector.get_pk_constraint.return_value = {"constrained_columns": []}
            inspector.get_foreign_keys.return_value = []
            inspector.get_indexes.return_value = []
            inspector.get_unique_constraints.return_value = []

            table_info = introspect_table(inspector, "users", schema="public")

            assert table_info.name == "users"
            inspector.get_columns.assert_called_with("users", schema="public")
