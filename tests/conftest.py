import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner

from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_db_url(tmp_path):
    """
    Provide a test database URL.
    For SQLite, creates a file-based database in the temp directory.
    For PostgreSQL, uses the environment variable.
    """
    db_url = os.getenv("JETBASE_SQLALCHEMY_URL")

    assert db_url is not None, "JETBASE_SQLALCHEMY_URL must be set for tests."
    # If using SQLite, convert to absolute file path for test isolation
    if db_url.startswith("sqlite"):
        db_file = tmp_path / "test.db"
        file_url = f"sqlite:///{db_file}"
        os.environ["JETBASE_SQLALCHEMY_URL"] = file_url
        return file_url

    return db_url


@pytest.fixture
def migrations_fixture_dir(test_db_url):
    """Path to the fixtures migrations directory."""
    base_path: Path = Path(__file__).parent / "cli"

    if detect_db(test_db_url) == DatabaseType.SNOWFLAKE:
        return base_path / "migrations_snowflake"

    if detect_db(test_db_url) == DatabaseType.MYSQL:
        return base_path / "migrations_mysql"

    if detect_db(test_db_url) == DatabaseType.DATABRICKS:
        return base_path / "migrations_databricks"

    return base_path / "migrations"


@pytest.fixture
def migrations_versions_only_fixture_dir(test_db_url):
    """Path to the fixtures migrations directory."""
    base_path = Path(__file__).parent / "cli"

    if detect_db(test_db_url) == DatabaseType.SNOWFLAKE:
        return base_path / "migrations_snowflake_versions_only"

    if detect_db(test_db_url) == DatabaseType.MYSQL:
        return base_path / "migrations_mysql_versions_only"

    if detect_db(test_db_url) == DatabaseType.DATABRICKS:
        return base_path / "migrations_databricks_versions_only"

    return base_path / "migrations_versions_only"


@pytest.fixture
def setup_migrations(tmp_path, migrations_fixture_dir):
    """Copy migration files from fixtures to temp directory."""
    jetbase_dir = tmp_path / "jetbase"
    jetbase_dir.mkdir()

    migrations_dir = jetbase_dir / "migrations"
    migrations_dir.mkdir()

    # Copy all migration files from fixtures
    if migrations_fixture_dir.exists():
        for migration_file in migrations_fixture_dir.glob("*.sql"):
            shutil.copy(migration_file, migrations_dir)

    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    yield migrations_dir

    # Restore original directory
    os.chdir(original_dir)


@pytest.fixture
def setup_migrations_versions_only(tmp_path, migrations_versions_only_fixture_dir):
    """Copy migration files from fixtures to temp directory."""
    jetbase_dir = tmp_path / "jetbase"
    jetbase_dir.mkdir()

    migrations_dir = jetbase_dir / "migrations"
    migrations_dir.mkdir()

    # Copy all migration files from fixtures
    if migrations_versions_only_fixture_dir.exists():
        for migration_file in migrations_versions_only_fixture_dir.glob("*.sql"):
            shutil.copy(migration_file, migrations_dir)

    # Change to temp directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    yield migrations_dir

    # Restore original directory
    os.chdir(original_dir)


@pytest.fixture
def clean_db(test_db_url):
    """Clean up database before and after tests."""
    engine = create_engine(test_db_url)

    def cleanup():
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS users"))
            connection.execute(text("DROP TABLE IF EXISTS jetbase_migrations"))
            connection.execute(text("DROP TABLE IF EXISTS jetbase_lock"))

    cleanup()
    yield engine
    cleanup()
    engine.dispose()
