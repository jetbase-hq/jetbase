import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base

from jetbase.commands.make_migrations import (
    MakeMigrationsError,
    NoChangesDetectedError,
    _generate_create_table_from_model,
    _make_migrations_sync,
    _write_migration_file,
    make_migrations_cmd,
)
from jetbase.constants import MIGRATIONS_DIR


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


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)


class ProfileModel(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    bio = Column(String(500), nullable=True)
    active = Column(Boolean, default=True)


@pytest.fixture
def sample_model_file(tmp_path):
    """Create a temporary model file with SQLAlchemy models."""
    model_content = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
"""
    model_path = tmp_path / "models.py"
    model_path.write_text(model_content)
    return str(model_path)


@pytest.fixture
def complex_model_file(tmp_path):
    """Create a temporary model file with multiple models including FKs."""
    model_content = """
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

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

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
"""
    model_path = tmp_path / "models.py"
    model_path.write_text(model_content)
    return str(model_path)


@pytest.fixture
def migrations_dir(tmp_path):
    """Create a temporary migrations directory."""
    migrations_dir = tmp_path / MIGRATIONS_DIR
    migrations_dir.mkdir()
    return migrations_dir


@pytest.fixture
def sync_db(tmp_path):
    """Create a temporary SQLite database for sync tests."""
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    return engine


class TestGenerateCreateTableFromModel:
    """Tests for _generate_create_table_from_model function."""

    def test_generate_simple_table(self, sync_db):
        """Test generating CREATE TABLE for a simple model."""
        with sync_db.connect() as conn:
            sql = _generate_create_table_from_model(UserModel, conn)

            assert "CREATE TABLE users" in sql
            assert "id INTEGER" in sql
            assert "PRIMARY KEY" in sql

    def test_generate_table_with_not_null(self, sync_db):
        """Test generating CREATE TABLE with NOT NULL constraints."""
        with sync_db.connect() as conn:
            sql = _generate_create_table_from_model(UserModel, conn)

            assert "NOT NULL" in sql
            assert "email" in sql

    def test_generate_table_with_nullable(self, sync_db):
        """Test generating CREATE TABLE with nullable columns."""
        with sync_db.connect() as conn:
            sql = _generate_create_table_from_model(UserModel, conn)

            assert "name" in sql

    def test_generate_table_with_foreign_key(self, sync_db):
        """Test generating CREATE TABLE with foreign keys."""
        with sync_db.connect() as conn:
            sql = _generate_create_table_from_model(OrderModel, conn)

            assert "CREATE TABLE orders" in sql
            assert "user_id" in sql
            assert "product_id" in sql

    def test_generate_table_with_boolean(self, sync_db):
        """Test generating CREATE TABLE with Boolean column."""
        with sync_db.connect() as conn:
            sql = _generate_create_table_from_model(ProfileModel, conn)

            assert "active" in sql


class TestMakeMigrationsSync:
    """Tests for _make_migrations_sync function."""

    def test_make_migrations_sync_new_tables(self, tmp_path, sync_db):
        """Test generating migrations for new tables."""
        models = {"users": UserModel, "products": ProductModel}
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        with patch("jetbase.commands.make_migrations.get_connection") as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "jetbase.commands.make_migrations.introspect_database"
            ) as mock_introspect:
                from jetbase.engine.schema_introspection import SchemaInfo

                mock_introspect.return_value = SchemaInfo(tables={})

                with patch(
                    "jetbase.commands.make_migrations.compare_schemas"
                ) as mock_compare:
                    from jetbase.engine.schema_diff import SchemaDiff

                    mock_compare.return_value = SchemaDiff(
                        tables_to_create=["users", "products"]
                    )

                    with patch(
                        "jetbase.commands.make_migrations.get_db_type"
                    ) as mock_db:
                        mock_db.return_value = "sqlite"

                        with patch(
                            "jetbase.commands.make_migrations._write_migration_file"
                        ) as mock_write:
                            _make_migrations_sync(models, "test description", set())

                            mock_write.assert_called_once()
                            args, kwargs = mock_write.call_args
                            assert len(args[0]) == 2
                            assert "users" in args[0][0]
                            assert "products" in args[0][1]

    def test_make_migrations_sync_no_changes(self, tmp_path, sync_db):
        """Test that no migration file is created when there are no changes."""
        models = {"users": UserModel}
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        with patch("jetbase.commands.make_migrations.get_connection") as mock_conn:
            mock_connection = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_connection)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)

            with patch(
                "jetbase.commands.make_migrations.introspect_database"
            ) as mock_introspect:
                from jetbase.engine.schema_introspection import (
                    SchemaInfo,
                    TableInfo,
                    ColumnInfo,
                )

                mock_introspect.return_value = SchemaInfo(
                    tables={
                        "users": TableInfo(
                            name="users",
                            columns=[
                                ColumnInfo("id", "INTEGER", False, None, True, False),
                                ColumnInfo(
                                    "email", "VARCHAR(255)", False, None, False, False
                                ),
                            ],
                            primary_keys=["id"],
                        )
                    }
                )

                with patch(
                    "jetbase.commands.make_migrations.compare_schemas"
                ) as mock_compare:
                    from jetbase.engine.schema_diff import SchemaDiff

                    mock_compare.return_value = SchemaDiff()

                    with patch(
                        "jetbase.commands.make_migrations._write_migration_file"
                    ) as mock_write:
                        _make_migrations_sync(models, "test description", set())

                        mock_write.assert_not_called()


class TestMakeMigrationsCmd:
    """Tests for make_migrations_cmd function."""

    def test_make_migrations_model_paths_not_set(self, tmp_path, migrations_dir):
        """Test error when JETBASE_MODELS is not set."""
        os.chdir(tmp_path)

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MakeMigrationsError) as exc_info:
                make_migrations_cmd()

            assert "JETBASE_MODELS" in str(exc_info.value)

    def test_make_migrations_model_file_not_found(self, tmp_path, migrations_dir):
        """Test error when model file path doesn't exist."""
        os.chdir(tmp_path)

        with patch.dict(os.environ, {"JETBASE_MODELS": "./nonexistent/models.py"}):
            with pytest.raises(MakeMigrationsError) as exc_info:
                make_migrations_cmd()

            assert "not found" in str(exc_info.value).lower()

    def test_make_migrations_with_model_file(self, tmp_path, sample_model_file):
        """Test make_migrations_cmd with a valid model file."""
        os.chdir(tmp_path)

        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        with patch.dict(
            os.environ,
            {
                "JETBASE_MODELS": sample_model_file,
                "ASYNC": "false",
                "JETBASE_SQLALCHEMY_URL": "sqlite:///./test.db",
            },
            clear=False,
        ):
            with patch("jetbase.commands.make_migrations.get_connection") as mock_conn:
                mock_connection = MagicMock()
                mock_conn.return_value.__enter__ = MagicMock(
                    return_value=mock_connection
                )
                mock_conn.return_value.__exit__ = MagicMock(return_value=False)

                with patch(
                    "jetbase.commands.make_migrations.introspect_database"
                ) as mock_introspect:
                    from jetbase.engine.schema_introspection import SchemaInfo

                    mock_introspect.return_value = SchemaInfo(tables={})

                    with patch(
                        "jetbase.commands.make_migrations.compare_schemas"
                    ) as mock_compare:
                        from jetbase.engine.schema_diff import SchemaDiff
                        from jetbase.engine.model_discovery import discover_all_models

                        mock_compare.return_value = SchemaDiff(
                            tables_to_create=["users"]
                        )

                        with patch(
                            "jetbase.commands.make_migrations.get_db_type"
                        ) as mock_db:
                            mock_db.return_value = "sqlite"

                            with patch(
                                "jetbase.commands.make_migrations._write_migration_file"
                            ) as mock_write:
                                make_migrations_cmd(description="create users")

                                mock_write.assert_called_once()


class TestWriteMigrationFile:
    """Tests for _write_migration_file function."""

    def test_write_migration_file_creates_directory(self, tmp_path):
        """Test that migrations directory is created if it doesn't exist."""
        os.chdir(tmp_path)

        upgrade_statements = ["CREATE TABLE users (id INTEGER PRIMARY KEY);"]
        rollback_statements = ["DROP TABLE users;"]

        with patch(
            "jetbase.commands.make_migrations._generate_new_filename"
        ) as mock_filename:
            mock_filename.return_value = "V1__test.sql"

            _write_migration_file(upgrade_statements, rollback_statements, "test")

            migrations_dir = tmp_path / MIGRATIONS_DIR
            assert migrations_dir.exists()

            migration_file = migrations_dir / "V1__test.sql"
            assert migration_file.exists()

    def test_write_migration_file_content(self, tmp_path):
        """Test that migration file contains correct content."""
        os.chdir(tmp_path)
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        upgrade_statements = [
            "CREATE TABLE users (id INTEGER PRIMARY KEY);",
            "CREATE TABLE products (id INTEGER PRIMARY KEY);",
        ]
        rollback_statements = [
            "DROP TABLE products;",
            "DROP TABLE users;",
        ]

        _write_migration_file(upgrade_statements, rollback_statements, "test")

        files = list(migrations_dir.glob("V*__test.sql"))
        assert len(files) == 1
        content = files[0].read_text()

        assert "-- upgrade" in content
        assert "-- rollback" in content
        assert "CREATE TABLE users" in content
        assert "CREATE TABLE products" in content
        assert "DROP TABLE users" in content
        assert "DROP TABLE products" in content

    def test_write_migration_file_with_description(self, tmp_path):
        """Test that migration file uses custom description."""
        os.chdir(tmp_path)
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        upgrade_statements = ["CREATE TABLE users (id INTEGER PRIMARY KEY);"]
        rollback_statements = ["DROP TABLE users;"]

        _write_migration_file(
            upgrade_statements, rollback_statements, "my_custom_description"
        )

        files = list(migrations_dir.glob("V*__my_custom_description.sql"))
        assert len(files) == 1


class TestMakeMigrationsError:
    """Tests for MakeMigrationsError exception."""

    def test_make_migrations_error(self):
        """Test MakeMigrationsError can be raised."""
        with pytest.raises(MakeMigrationsError):
            raise MakeMigrationsError("Test error message")

    def test_no_changes_detected_error(self):
        """Test NoChangesDetectedError can be raised."""
        with pytest.raises(NoChangesDetectedError):
            raise NoChangesDetectedError("No changes detected")


class TestSQLGenerationFromModels:
    """Integration tests for SQL generation from SQLAlchemy models."""

    def test_generate_sql_for_user_model(self, tmp_path):
        """Test SQL generation for User model."""
        from jetbase.engine.schema_introspection import SchemaInfo
        from jetbase.engine.schema_diff import SchemaDiff

        models = {"users": UserModel}
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        db_file = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_file}")

        with engine.connect() as connection:
            with patch(
                "jetbase.commands.make_migrations.introspect_database"
            ) as mock_introspect:
                mock_introspect.return_value = SchemaInfo(tables={})

                with patch(
                    "jetbase.commands.make_migrations.compare_schemas"
                ) as mock_compare:
                    mock_compare.return_value = SchemaDiff(tables_to_create=["users"])

                    with patch(
                        "jetbase.commands.make_migrations.get_db_type"
                    ) as mock_db:
                        mock_db.return_value = "sqlite"

                        with patch(
                            "jetbase.commands.make_migrations._write_migration_file"
                        ) as mock_write:
                            with patch(
                                "jetbase.commands.make_migrations.get_connection"
                            ) as mock_get_conn:
                                mock_get_conn.return_value.__enter__ = MagicMock(
                                    return_value=connection
                                )
                                mock_get_conn.return_value.__exit__ = MagicMock(
                                    return_value=False
                                )

                                _make_migrations_sync(models, "create users", set())

                                mock_write.assert_called_once()
                                args, kwargs = mock_write.call_args
                                upgrade_sql = "\n\n".join(args[0])

                                assert "CREATE TABLE users" in upgrade_sql
                                assert "id INTEGER" in upgrade_sql
                                assert "email" in upgrade_sql
                                assert "NOT NULL" in upgrade_sql

    def test_generate_sql_with_foreign_keys(self, tmp_path):
        """Test SQL generation for models with foreign keys."""
        from jetbase.engine.schema_introspection import SchemaInfo
        from jetbase.engine.schema_diff import SchemaDiff

        models = {"orders": OrderModel}
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        db_file = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_file}")

        with engine.connect() as connection:
            with patch(
                "jetbase.commands.make_migrations.introspect_database"
            ) as mock_introspect:
                mock_introspect.return_value = SchemaInfo(tables={})

                with patch(
                    "jetbase.commands.make_migrations.compare_schemas"
                ) as mock_compare:
                    mock_compare.return_value = SchemaDiff(tables_to_create=["orders"])

                    with patch(
                        "jetbase.commands.make_migrations.get_db_type"
                    ) as mock_db:
                        mock_db.return_value = "sqlite"

                        with patch(
                            "jetbase.commands.make_migrations._write_migration_file"
                        ) as mock_write:
                            with patch(
                                "jetbase.commands.make_migrations.get_connection"
                            ) as mock_get_conn:
                                mock_get_conn.return_value.__enter__ = MagicMock(
                                    return_value=connection
                                )
                                mock_get_conn.return_value.__exit__ = MagicMock(
                                    return_value=False
                                )

                                _make_migrations_sync(models, "create orders", set())

                                mock_write.assert_called_once()
                                args, kwargs = mock_write.call_args
                                upgrade_sql = "\n\n".join(args[0])

                                assert "CREATE TABLE orders" in upgrade_sql
                                assert "user_id" in upgrade_sql
                                assert "product_id" in upgrade_sql

    def test_generate_sql_multiple_tables(self, tmp_path):
        """Test SQL generation for multiple tables."""
        from jetbase.engine.schema_introspection import SchemaInfo
        from jetbase.engine.schema_diff import SchemaDiff

        models = {"users": UserModel, "products": ProductModel}
        migrations_dir = tmp_path / MIGRATIONS_DIR
        migrations_dir.mkdir()

        db_file = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_file}")

        with engine.connect() as connection:
            with patch(
                "jetbase.commands.make_migrations.introspect_database"
            ) as mock_introspect:
                mock_introspect.return_value = SchemaInfo(tables={})

                with patch(
                    "jetbase.commands.make_migrations.compare_schemas"
                ) as mock_compare:
                    mock_compare.return_value = SchemaDiff(
                        tables_to_create=["users", "products"]
                    )

                    with patch(
                        "jetbase.commands.make_migrations.get_db_type"
                    ) as mock_db:
                        mock_db.return_value = "sqlite"

                        with patch(
                            "jetbase.commands.make_migrations._write_migration_file"
                        ) as mock_write:
                            with patch(
                                "jetbase.commands.make_migrations.get_connection"
                            ) as mock_get_conn:
                                mock_get_conn.return_value.__enter__ = MagicMock(
                                    return_value=connection
                                )
                                mock_get_conn.return_value.__exit__ = MagicMock(
                                    return_value=False
                                )

                                _make_migrations_sync(
                                    models, "create all tables", set()
                                )

                                mock_write.assert_called_once()
                                args, kwargs = mock_write.call_args
                                upgrade_sql = "\n\n".join(args[0])

                                assert "CREATE TABLE users" in upgrade_sql
                                assert "CREATE TABLE products" in upgrade_sql

                                rollback_sql = "\n\n".join(args[1])
                                assert "DROP TABLE products" in rollback_sql
                                assert "DROP TABLE users" in rollback_sql
