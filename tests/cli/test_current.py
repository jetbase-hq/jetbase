import os

from jetbase.cli.main import app
from jetbase.queries import LATEST_VERSION_QUERY


def test_current_success_versions_only(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["current"])
        assert result.exit_code == 0

        assert "21" in result.output
        result = connection.execute(LATEST_VERSION_QUERY)
        latest_version = result.scalar()
        assert latest_version == "21"


def test_current_success_repeatables(runner, test_db_url, clean_db, setup_migrations):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    with clean_db.begin() as connection:
        os.chdir("jetbase")
        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["current"])
        assert result.exit_code == 0

        assert "21" in result.output
        result = connection.execute(LATEST_VERSION_QUERY)
        latest_version = result.scalar()
        assert latest_version == "21"


def test_current_no_migrations_or_tables(
    runner, test_db_url, clean_db, setup_migrations_versions_only
):
    os.environ["JETBASE_SQLALCHEMY_URL"] = test_db_url

    os.chdir("jetbase")

    result = runner.invoke(app, ["current"])
    assert result.exit_code == 0
    assert "no migrations" in result.output.lower()
