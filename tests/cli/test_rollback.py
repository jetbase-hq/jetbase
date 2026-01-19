import os

from sqlalchemy import text

from jetbase.cli.main import app
from jetbase.exceptions import VersionNotFoundError
import pytest


@pytest.mark.snowflake
def test_rollback(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        # Rollback the migration
        result = runner.invoke(app, ["rollback"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration record was removed
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 6


def test_rollback_with_count(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    with clean_db.begin() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        # Rollback the migration
        result = runner.invoke(app, ["rollback", "--count", "3"])
        assert result.exit_code == 0

        # Verify table was dropped

    with clean_db.begin() as connection:
        # Verify migration record was removed
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 4


def test_rollback_to_version(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    with clean_db.begin() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        # Rollback the migration
        result = runner.invoke(app, ["rollback", "--to-version", "2"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 4

        result = runner.invoke(app, ["rollback", "--to-version", "1.5"])
        assert result.exit_code != 0

        assert isinstance(result.exception, VersionNotFoundError), (
            f"Expected VersionNotFoundError but got {type(result.exception)}"
        )


def test_rollback_with_dry_run(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    with clean_db.begin() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        result = runner.invoke(app, ["rollback", "--dry-run"])
        assert result.exit_code == 0

        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        assert "Dry Run Mode" in result.output


def test_rollback_with_deleted_file(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 7

        # Change version of latest migration to simulate missing file
        migration_to_delete = setup_migrations / "V21__mi21.sql"
        migration_to_delete.unlink(missing_ok=True)

        # Rollback the migration
        result = runner.invoke(app, ["rollback"])
        assert result.exit_code != 0
        assert isinstance(result.exception, VersionNotFoundError), (
            f"Expected VersionNotFoundError but got {type(result.exception)}"
        )

        result = runner.invoke(app, ["rollback", "--to-version", "2"])
        assert result.exit_code != 0
        assert isinstance(result.exception, VersionNotFoundError), (
            f"Expected VersionNotFoundError but got {type(result.exception)}"
        )

        result = runner.invoke(app, ["rollback", "--count", "3"])
        assert result.exit_code != 0
        assert isinstance(result.exception, VersionNotFoundError), (
            f"Expected VersionNotFoundError but got {type(result.exception)}"
        )
