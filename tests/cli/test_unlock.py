import datetime as dt
import os
import uuid

from jetbase.cli.main import app
from jetbase.queries import ACQUIRE_LOCK_STMT


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
            ACQUIRE_LOCK_STMT,
            {
                "locked_at": dt.datetime.now(dt.timezone.utc),
                "process_id": str(uuid.uuid4()),
            },
        )

        result = runner.invoke(app, ["lock-status"])
        assert result.exit_code == 0
        assert "locked" in result.output.lower()
