import os
import shutil
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def test_db_url():
    """
    Provide a test database URL.
    Set the JETBASE_DATABASE_URL environment variable with your test database.
    Example: postgresql://user:password@localhost:5432/jetbase_test
    """
    db_url = os.getenv("JETBASE_SQLALCHEMY_URL")
    if not db_url:
        pytest.skip("JETBASE_SQLALCHEMY_URL environment variable not set")
    return db_url


@pytest.fixture
def migrations_fixture_dir():
    """Path to the fixtures migrations directory."""
    return Path(__file__).parent / "cli" / "migrations"


@pytest.fixture
def migrations_versions_only_fixture_dir():
    """Path to the fixtures migrations directory."""
    return Path(__file__).parent / "cli" / "migrations_versions_only"


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
            connection.execute(text("DROP TABLE IF EXISTS test_users"))
            connection.execute(text("DROP TABLE IF EXISTS users"))
            connection.execute(text("DROP TABLE IF EXISTS test_posts"))
            connection.execute(text("DROP TABLE IF EXISTS jetbase_migrations"))
            connection.execute(text("DROP TABLE IF EXISTS jetbase_lock"))

    cleanup()
    yield engine
    cleanup()
    engine.dispose()
