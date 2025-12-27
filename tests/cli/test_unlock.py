import datetime as dt
import os
import uuid

from sqlalchemy import text

from jetbase.cli.main import app


def test_unlock_already_unlocked(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["unlock"])
    assert result.exit_code == 0
    assert "unlock" in result.output.lower()


def test_lock_status_locked(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

        connection.execute(
            text("""
            UPDATE jetbase_lock
            SET is_locked = TRUE,
                locked_at = :locked_at,
                process_id = :process_id
            WHERE id = 1 AND is_locked = FALSE
            """),
            {
                "locked_at": dt.datetime.now(dt.timezone.utc),
                "process_id": str(uuid.uuid4()),
            },
        )

        result = runner.invoke(app, ["lock-status"])
        assert result.exit_code == 0
        assert "locked" in result.output.lower()
