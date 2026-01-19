import os
import pytest
from sqlalchemy import text

from jetbase.cli.main import app
from jetbase.exceptions import (
    ChecksumMismatchError,
    DuplicateMigrationVersionError,
    OutOfOrderMigrationError,
)


def test_upgrade_versions(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
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
        assert count == 5


def test_upgrade_count(runner, test_db_url, clean_db, setup_migrations_versions_only):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        result = runner.invoke(app, ["upgrade", "-c", "1"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 4


def test_upgrade_count_greater_than_pending(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade", "--count", "20"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5

        result = runner.invoke(app, ["upgrade", "-c", "1"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5


def test_upgrade_count_negative(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "-1"])
    assert result.exit_code != 0

    assert isinstance(result.exception, ValueError), (
        f"Expected ValueError but got {type(result.exception)}"
    )


def test_upgrade_to_version(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade", "--to-version", "2"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 2


def test_upgrade_to_version_not_exists(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--to-version", "1.5"])
    assert result.exit_code != 0

    assert isinstance(result.exception, FileNotFoundError), (
        f"Expected FileNotFoundError but got {type(result.exception)}"
    )


def test_upgrade_then_remove_files(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade", "--count", "3"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Remove a migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        file_to_remove = os.path.join(migrations_dir, "V2__m2.sql")
        if os.path.exists(file_to_remove):
            os.remove(file_to_remove)

        # Run upgrade again
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, FileNotFoundError), (
            f"Expected FileNotFoundError but got {type(result.exception)}"
        )


def test_upgrade_with_dry_run(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade", "--dry-run"])
        assert result.exit_code == 0

        # Verify no migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 0


def test_upgrade_then_add_lower_version_file(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade", "--count", "3"])
        assert result.exit_code == 0

        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Add a lower version migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        lower_version_file = os.path.join(migrations_dir, "V1.5__m1_5.sql")
        with open(lower_version_file, "w") as f:
            f.write("-- SQL statements for migration V1.5\n")

        # Run upgrade again
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, OutOfOrderMigrationError), (
            f"Expected OutOfOrderMigrationError but got {type(result.exception)}"
        )


def test_upgrade_with_duplicate_version_files(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    # Add a duplicate version migration file
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    duplicate_version_file = os.path.join(migrations_dir, "V2__duplicate_m2.sql")
    with open(duplicate_version_file, "w") as f:
        f.write("-- SQL statements for duplicate migration V2\n")

    # Run upgrade
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code != 0

    assert isinstance(result.exception, DuplicateMigrationVersionError), (
        f"Expected DuplicateMigrationVersionError but got {type(result.exception)}"
    )


def test_upgrade_skip_checksum_validation(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Modify the migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        file_to_modify = os.path.join(migrations_dir, "V2__m2.sql")
        with open(file_to_modify, "w") as f:
            f.write("\n-- Modified content\n")

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, ChecksumMismatchError), (
            f"Expected ChecksumMismatchError but got {type(result.exception)}"
        )

        # Run upgrade again with skip-checksum-validation
        result = runner.invoke(app, ["upgrade", "--skip-checksum-validation"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5


@pytest.mark.snowflake
def test_upgrade_repeatables(runner, test_db_url, clean_db, setup_migrations):
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


def test_roc_with_no_changes(runner, test_db_url, clean_db, setup_migrations):
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

        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ON_CHANGE'"
            )
        )
        applied_at_before = timestamp_result.scalar()

        # Run upgrade again to test ROC with no changes
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ON_CHANGE'"
            )
        )
        applied_at_after = timestamp_result.scalar()

        assert applied_at_before == applied_at_after, (
            "RUNS_ON_CHANGE migration was reapplied despite no changes."
        )


def test_roc_with_changes(runner, test_db_url, clean_db, setup_migrations):
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

        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ON_CHANGE'"
            )
        )
        applied_at_before = timestamp_result.scalar()

        # Modify the ROC migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        roc_file = os.path.join(migrations_dir, "ROC__roc.sql")
        with open(roc_file, "w") as f:
            f.write("\n-- Modified content to trigger reapplication\n")

        # Run upgrade again to test ROC with changes
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ON_CHANGE'"
            )
        )
        applied_at_after = timestamp_result.scalar()

        assert applied_at_before < applied_at_after, (
            "RUNS_ON_CHANGE migration was not reapplied despite changes."
        )


def test_repeatable_always_multiple_upgrades(
    runner, test_db_url, clean_db, setup_migrations
):
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

        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ALWAYS'"
            )
        )
        applied_at_first = timestamp_result.scalar()

        # Run upgrade again to test RALWAYS
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        timestamp_result = connection.execute(
            text(
                "SELECT applied_at FROM jetbase_migrations WHERE migration_type = 'RUNS_ALWAYS'"
            )
        )
        applied_at_second = timestamp_result.scalar()

        assert applied_at_first < applied_at_second, (
            "RUNS_ALWAYS migration was not reapplied on subsequent upgrade."
        )


def test_upgrade_skip_validation(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Modify the migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        file_to_modify = os.path.join(migrations_dir, "V2__m2.sql")
        with open(file_to_modify, "w") as f:
            f.write("\n-- Modified content\n")

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, ChecksumMismatchError), (
            f"Expected ChecksumMismatchError but got {type(result.exception)}"
        )

        # Add a lower version migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        lower_version_file = os.path.join(migrations_dir, "V1.5__m1_5.sql")
        with open(lower_version_file, "w") as f:
            f.write("-- SQL statements for migration V1.5\n")

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0
        assert isinstance(result.exception, OutOfOrderMigrationError), (
            f"Expected OutOfOrderMigrationError but got {type(result.exception)}"
        )

        # Run upgrade again with skip-validation
        result = runner.invoke(app, ["upgrade", "--skip-validation"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5


def test_upgrade_skip_file_validation_lower_file(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Add a lower version migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        lower_version_file = os.path.join(migrations_dir, "V1.5__m1_5.sql")
        with open(lower_version_file, "w") as f:
            f.write("-- SQL statements for migration V1.5\n")

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0
        assert isinstance(result.exception, OutOfOrderMigrationError), (
            f"Expected OutOfOrderMigrationError but got {type(result.exception)}"
        )

        # Run upgrade again with skip-validation
        result = runner.invoke(app, ["upgrade", "--skip-validation"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5


def test_upgrade_skip_file_validation_deleted_migrated_file(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    with clean_db.connect() as connection:
        # Verify migration applied
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 3

        # Delete the migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        file_to_delete = os.path.join(migrations_dir, "V2__m2.sql")
        os.remove(file_to_delete)

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, FileNotFoundError), (
            f"Expected FileNotFoundError but got {type(result.exception)}"
        )

        # Run upgrade again with skip-file-validation
        result = runner.invoke(app, ["upgrade", "--skip-file-validation"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5
