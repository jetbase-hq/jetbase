import pytest
import os
from sqlalchemy import text

from jetbase.cli.main import app
from jetbase.exceptions import (
    ChecksumMismatchError,
)


def test_validate_checksums(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    pass


@pytest.mark.snowflake
def test_validate_checksums_with_fix(
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

        # Get initial checksum value
        checksum_result = connection.execute(
            text("SELECT checksum FROM jetbase_migrations WHERE version = '2'")
        )
        initial_checksum = checksum_result.scalar()
        assert initial_checksum is not None

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

        result = runner.invoke(app, ["validate-checksums", "--fix"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        migrations_result = connection.execute(
            text("SELECT COUNT(*) FROM jetbase_migrations")
        )
        count = migrations_result.scalar()
        assert count == 5

        # Get modified checksum value
        checksum_result = connection.execute(
            text("SELECT checksum FROM jetbase_migrations WHERE version = '2'")
        )
        modified_checksum = checksum_result.scalar()
        assert modified_checksum is not None

        assert initial_checksum != modified_checksum, (
            "Checksum should have changed after file modification"
        )
