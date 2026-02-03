from unittest.mock import patch

import pytest

from jetbase.engine.schema_diff import SchemaDiff
from jetbase.engine.schema_introspection import ColumnInfo
from jetbase.engine.sql_generator import (
    generate_add_column_sql,
    generate_add_foreign_key_sql,
    generate_create_index_sql,
    generate_create_table_sql,
    generate_drop_column_sql,
    generate_drop_foreign_key_sql,
    generate_drop_index_sql,
    generate_drop_table_sql,
    generate_migration_sql,
    generate_rollback_sql,
    generate_upgrade_sql,
    get_db_type,
    sql_type_to_string,
)
from jetbase.enums import DatabaseType


class TestSQLTypeToString:
    """Tests for sql_type_to_string function."""

    def test_integer_postgresql(self):
        """Test INTEGER type conversion for PostgreSQL."""
        result = sql_type_to_string("INTEGER", DatabaseType.POSTGRESQL)
        assert result == "INTEGER"

    def test_varchar_postgresql(self):
        """Test VARCHAR type conversion for PostgreSQL."""
        result = sql_type_to_string("VARCHAR(255)", DatabaseType.POSTGRESQL)
        assert result == "VARCHAR(255)"

    def test_integer_mysql(self):
        """Test INTEGER type conversion for MySQL."""
        result = sql_type_to_string("INTEGER", DatabaseType.MYSQL)
        assert result == "INT"

    def test_boolean_mysql(self):
        """Test BOOLEAN type conversion for MySQL."""
        result = sql_type_to_string("BOOLEAN", DatabaseType.MYSQL)
        assert result == "TINYINT(1)"

    def test_text_sqlite(self):
        """Test TEXT type conversion for SQLite."""
        result = sql_type_to_string("TEXT", DatabaseType.SQLITE)
        assert result == "TEXT"

    def test_integer_sqlite(self):
        """Test INTEGER type conversion for SQLite."""
        result = sql_type_to_string("INTEGER", DatabaseType.SQLITE)
        assert result == "INTEGER"

    def test_unknown_type(self):
        """Test unknown type returns as-is."""
        result = sql_type_to_string("CUSTOM_TYPE", DatabaseType.POSTGRESQL)
        assert result == "CUSTOM_TYPE"


class TestGenerateCreateTableSQL:
    """Tests for generate_create_table_sql function."""

    def test_create_simple_table_postgresql(self):
        """Test generating CREATE TABLE for PostgreSQL."""
        columns = [
            ColumnInfo("id", "INTEGER", False, None, True, False),
            ColumnInfo("name", "VARCHAR(255)", False, None, False, False),
        ]

        sql = generate_create_table_sql(
            table_name="users",
            columns=columns,
            primary_keys=["id"],
            db_type=DatabaseType.POSTGRESQL,
        )

        assert "CREATE TABLE users" in sql
        assert "id INTEGER" in sql
        assert "name VARCHAR(255)" in sql
        assert "PRIMARY KEY (id)" in sql

    def test_create_table_with_not_null(self):
        """Test generating CREATE TABLE with NOT NULL constraints."""
        columns = [
            ColumnInfo("id", "INTEGER", False, None, True, False),
            ColumnInfo("email", "VARCHAR(255)", False, None, False, False),
        ]

        sql = generate_create_table_sql(
            table_name="users",
            columns=columns,
            primary_keys=["id"],
            db_type=DatabaseType.POSTGRESQL,
        )

        assert "NOT NULL" in sql

    def test_create_table_mysql(self):
        """Test generating CREATE TABLE for MySQL."""
        columns = [
            ColumnInfo("id", "INTEGER", False, None, True, False),
            ColumnInfo("name", "VARCHAR(255)", False, None, False, False),
        ]

        sql = generate_create_table_sql(
            table_name="users",
            columns=columns,
            primary_keys=["id"],
            db_type=DatabaseType.MYSQL,
        )

        assert "ENGINE=InnoDB" in sql
        assert "CHARSET=utf8mb4" in sql

    def test_create_table_sqlite(self):
        """Test generating CREATE TABLE for SQLite."""
        columns = [
            ColumnInfo("id", "INTEGER", False, None, True, False),
            ColumnInfo("name", "VARCHAR(255)", False, None, False, False),
        ]

        sql = generate_create_table_sql(
            table_name="users",
            columns=columns,
            primary_keys=["id"],
            db_type=DatabaseType.SQLITE,
        )

        assert "CREATE TABLE users" in sql


class TestGenerateDropTableSQL:
    """Tests for generate_drop_table_sql function."""

    def test_drop_table_postgresql(self):
        """Test generating DROP TABLE for PostgreSQL."""
        sql = generate_drop_table_sql("users", DatabaseType.POSTGRESQL)
        assert sql == "DROP TABLE users;"

    def test_drop_table_databricks(self):
        """Test generating DROP TABLE for Databricks with IF EXISTS."""
        sql = generate_drop_table_sql("users", DatabaseType.DATABRICKS)
        assert sql == "DROP TABLE IF EXISTS users;"


class TestGenerateAddColumnSQL:
    """Tests for generate_add_column_sql function."""

    def test_add_column_postgresql(self):
        """Test generating ALTER TABLE ADD COLUMN for PostgreSQL."""
        column = ColumnInfo("age", "INTEGER", True, None, False, False)

        sql = generate_add_column_sql("users", column, DatabaseType.POSTGRESQL)

        assert "ALTER TABLE users ADD COLUMN" in sql
        assert "age INTEGER" in sql

    def test_add_column_with_not_null(self):
        """Test adding NOT NULL column."""
        column = ColumnInfo("email", "VARCHAR(255)", False, None, False, False)

        sql = generate_add_column_sql("users", column, DatabaseType.POSTGRESQL)

        assert "NOT NULL" in sql


class TestGenerateDropColumnSQL:
    """Tests for generate_drop_column_sql function."""

    def test_drop_column(self):
        """Test generating ALTER TABLE DROP COLUMN."""
        sql = generate_drop_column_sql("users", "old_column", DatabaseType.POSTGRESQL)

        assert "ALTER TABLE users DROP COLUMN old_column;" in sql


class TestGenerateCreateIndexSQL:
    """Tests for generate_create_index_sql function."""

    def test_create_index(self):
        """Test generating CREATE INDEX."""
        index_info = {
            "name": "idx_users_email",
            "column_names": ["email"],
            "unique": False,
        }

        sql = generate_create_index_sql("users", index_info, DatabaseType.POSTGRESQL)

        assert "CREATE INDEX idx_users_email ON users (email);" in sql

    def test_create_unique_index(self):
        """Test generating CREATE UNIQUE INDEX."""
        index_info = {
            "name": "uniq_users_email",
            "column_names": ["email"],
            "unique": True,
        }

        sql = generate_create_index_sql("users", index_info, DatabaseType.POSTGRESQL)

        assert "CREATE UNIQUE INDEX" in sql


class TestGenerateDropIndexSQL:
    """Tests for generate_drop_index_sql function."""

    def test_drop_index(self):
        """Test generating DROP INDEX."""
        sql = generate_drop_index_sql(
            "idx_users_email", "users", DatabaseType.POSTGRESQL
        )

        assert "DROP INDEX idx_users_email ON users;" in sql


class TestGenerateAddForeignKeySQL:
    """Tests for generate_add_foreign_key_sql function."""

    def test_add_foreign_key(self):
        """Test generating ALTER TABLE ADD FOREIGN KEY."""
        fk_info = {
            "name": "fk_users_address",
            "constrained_columns": ["address_id"],
            "referred_table": "addresses",
            "referred_columns": ["id"],
        }

        sql = generate_add_foreign_key_sql("users", fk_info, DatabaseType.POSTGRESQL)

        assert "ALTER TABLE users ADD CONSTRAINT fk_users_address" in sql
        assert "FOREIGN KEY (address_id) REFERENCES addresses (id)" in sql


class TestGenerateDropForeignKeySQL:
    """Tests for generate_drop_foreign_key_sql function."""

    def test_drop_foreign_key(self):
        """Test generating ALTER TABLE DROP FOREIGN KEY."""
        sql = generate_drop_foreign_key_sql(
            "users", "fk_users_address", DatabaseType.POSTGRESQL
        )

        assert "ALTER TABLE users DROP CONSTRAINT fk_users_address;" in sql


class TestGenerateUpgradeSQL:
    """Tests for generate_upgrade_sql function."""

    def test_upgrade_with_columns_to_add(self):
        """Test generating upgrade SQL with columns to add."""
        diff = SchemaDiff(
            columns_to_add={
                "users": [ColumnInfo("age", "INTEGER", True, None, False, False)]
            }
        )

        sql = generate_upgrade_sql(diff, DatabaseType.POSTGRESQL)

        assert "ALTER TABLE users ADD COLUMN" in sql
        assert "age INTEGER" in sql

    def test_upgrade_with_indexes(self):
        """Test generating upgrade SQL with indexes."""
        diff = SchemaDiff(
            indexes_to_create={
                "users": [
                    {
                        "name": "idx_users_email",
                        "column_names": ["email"],
                        "unique": False,
                    }
                ]
            }
        )

        sql = generate_upgrade_sql(diff, DatabaseType.POSTGRESQL)

        assert "CREATE INDEX" in sql


class TestGenerateRollbackSQL:
    """Tests for generate_rollback_sql function."""

    def test_rollback_with_tables_to_drop(self):
        """Test generating rollback SQL with tables to drop."""
        diff = SchemaDiff(tables_to_create=["new_table"])

        sql = generate_rollback_sql(diff, DatabaseType.POSTGRESQL)

        assert "DROP TABLE" in sql

    def test_rollback_with_columns_to_remove(self):
        """Test generating rollback SQL with columns to remove."""
        diff = SchemaDiff(columns_to_remove={"users": ["new_column"]})

        sql = generate_rollback_sql(diff, DatabaseType.POSTGRESQL)

        assert "DROP COLUMN" in sql


class TestGenerateMigrationSQL:
    """Tests for generate_migration_sql function."""

    def test_generate_migration_sql(self):
        """Test generating complete migration SQL."""
        diff = SchemaDiff(
            columns_to_add={
                "users": [ColumnInfo("phone", "VARCHAR(20)", True, None, False, False)]
            }
        )

        with patch("jetbase.engine.sql_generator.get_db_type") as mock_db_type:
            mock_db_type.return_value = DatabaseType.POSTGRESQL

            upgrade_sql, rollback_sql = generate_migration_sql(diff)

            assert "ALTER TABLE users ADD COLUMN phone" in upgrade_sql
            assert "ALTER TABLE users DROP COLUMN phone" in rollback_sql

    def test_empty_migration(self):
        """Test generating SQL for empty diff."""
        diff = SchemaDiff()

        with patch("jetbase.engine.sql_generator.get_db_type") as mock_db_type:
            mock_db_type.return_value = DatabaseType.POSTGRESQL

            upgrade_sql, rollback_sql = generate_migration_sql(diff)

            assert upgrade_sql == ""
            assert rollback_sql == ""
