import os

from jetbase.cli.main import app


def test_history_success_versions(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0

    assert "1" in result.output
    assert "2" in result.output
    assert "3" in result.output
    assert "4" in result.output
    assert "21" in result.output


def test_history_success_repeatables(runner, test_db_url, clean_db, setup_migrations):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0

    assert "1" in result.output
    assert "2" in result.output
    assert "3" in result.output
    assert "4" in result.output
    assert "21" in result.output
    assert "RUNS_ALWAYS" in result.output
    assert "RUNS_ON_CHANGE" in result.output


def test_history_success_migrations_pending_versions(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0

    assert "1" in result.output
    assert "2" in result.output
    assert "3" in result.output
    assert "m4" not in result.output
    assert "mi21" not in result.output


def test_history_empty_migrations_dir(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.chdir("jetbase")

    result = runner.invoke(app, ["history"])
    assert result.exit_code == 0
