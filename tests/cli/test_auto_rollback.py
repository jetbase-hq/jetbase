import os
import subprocess

from sqlalchemy import text

from jetbase.cli.main import app
from jetbase.exceptions import MissingMigrationFileError


def _git(*args: str, cwd) -> None:
    """Run a git command in cwd with a deterministic identity."""
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=test@example.com",
            "-c",
            "user.name=test",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def test_upgrade_records_git_commit_hash_and_auto_rolls_back_missing_file(
    runner, test_db_url, clean_db, setup_migrations_versions_only, tmp_path
):
    """End-to-end: hash is recorded, and --auto-rollback recovers a missing file."""
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    # Initialize a git repo containing the migration files (cwd is tmp_path here).
    _git("init", cwd=tmp_path)
    _git("add", "-A", cwd=tmp_path)
    _git("commit", "-m", "initial migrations", cwd=tmp_path)

    migrations_dir = setup_migrations_versions_only

    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0, result.output

    with clean_db.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT version, git_commit_hash FROM jetbase_migrations "
                "WHERE migration_type = 'VERSIONED'"
            )
        ).fetchall()
    assert len(rows) == 5
    # Every applied versioned migration recorded the current commit hash.
    assert all(row.git_commit_hash for row in rows)

    # Delete the trailing (highest-version) migration file locally; it remains in git.
    (migrations_dir / "V21__mi21.sql").unlink()

    # Without the flag, the upgrade fails because an applied file is missing.
    result_no_flag = runner.invoke(app, ["upgrade"])
    assert result_no_flag.exit_code != 0
    assert isinstance(result_no_flag.exception, MissingMigrationFileError)

    # With --auto-rollback, V21 is rolled back (its rollback SQL recovered from git)
    # and the upgrade re-runs from the V4 baseline.
    result_auto = runner.invoke(app, ["upgrade", "--auto-rollback"])
    assert result_auto.exit_code == 0, result_auto.output

    with clean_db.connect() as connection:
        remaining = connection.execute(
            text(
                "SELECT version FROM jetbase_migrations "
                "WHERE migration_type = 'VERSIONED'"
            )
        ).fetchall()
    versions = {row.version for row in remaining}
    assert "21" not in versions
    assert len(remaining) == 4
