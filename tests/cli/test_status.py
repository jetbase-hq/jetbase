import os

from jetbase.cli.main import app


def test_status_success_all_applied_versions(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

    applied_start = result.output.index("Migrations Applied")
    pending_start = result.output.index("Migrations Pending")

    applied_section = result.output[applied_start:pending_start]
    pending_section = result.output[pending_start:]

    assert "m1" in applied_section
    assert "m2" in applied_section
    assert "m3" in applied_section
    assert "m4" in applied_section
    assert "mi21" in applied_section

    assert "m1" not in pending_section
    assert "m2" not in pending_section
    assert "m3" not in pending_section
    assert "m4" not in pending_section
    assert "mi21" not in pending_section


def test_status_success_repeatables(runner, test_db_url, clean_db, setup_migrations):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

    applied_start = result.output.index("Migrations Applied")
    pending_start = result.output.index("Migrations Pending")

    applied_section = result.output[applied_start:pending_start]
    pending_section = result.output[pending_start:]

    assert "m1" in applied_section
    assert "m2" in applied_section
    assert "m3" in applied_section
    assert "m4" in applied_section
    assert "mi21" in applied_section
    assert "RUNS_ALWAYS" in applied_section
    assert "RUNS_ON_CHANGE" in applied_section

    assert "m1" not in pending_section
    assert "m2" not in pending_section
    assert "m3" not in pending_section
    assert "m4" not in pending_section
    assert "mi21" not in pending_section
    assert "RUNS_ALWAYS" in pending_section
    assert "RUNS_ON_CHANGE" not in pending_section


def test_status_success_partial_applied_versions(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

    applied_start = result.output.index("Migrations Applied")
    pending_start = result.output.index("Migrations Pending")

    applied_section = result.output[applied_start:pending_start]
    pending_section = result.output[pending_start:]

    assert "m1" in applied_section
    assert "m2" in applied_section
    assert "m3" in applied_section
    assert "m4" not in applied_section
    assert "mi21" not in applied_section

    assert "m1" not in pending_section
    assert "m2" not in pending_section
    assert "m3" not in pending_section
    assert "m4" in pending_section
    assert "mi21" in pending_section


def test_status_success_roc_changed(runner, test_db_url, clean_db, setup_migrations):
    os.chdir("jetbase")
    result = runner.invoke(app, ["upgrade", "--count", "3"])
    assert result.exit_code == 0

    # Modify the migration file
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    file_to_modify = os.path.join(migrations_dir, "ROC__roc.sql")
    with open(file_to_modify, "w") as f:
        f.write("\n-- Modified content\n")

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

    applied_start = result.output.index("Migrations Applied")
    pending_start = result.output.index("Migrations Pending")

    applied_section = result.output[applied_start:pending_start]
    pending_section = result.output[pending_start:]

    assert "m1" in applied_section
    assert "m2" in applied_section
    assert "m3" in applied_section
    assert "RUNS_ALWAYS" in applied_section
    assert "RUNS_ON_CHANGE" in applied_section

    assert "m1" not in pending_section
    assert "m2" not in pending_section
    assert "m3" not in pending_section
    assert "m4" in pending_section
    assert "mi21" in pending_section
    assert "RUNS_ALWAYS" in pending_section
    assert "RUNS_ON_CHANGE" in pending_section


def test_status_success_roc_not_migrated(
    runner, test_db_url, clean_db, setup_migrations
):
    os.chdir("jetbase")

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0

    applied_start = result.output.index("Migrations Applied")
    pending_start = result.output.index("Migrations Pending")

    applied_section = result.output[applied_start:pending_start]
    pending_section = result.output[pending_start:]

    assert "RUNS_ON_CHANGE" not in applied_section

    assert "RUNS_ON_CHANGE" in pending_section
