import os

from sqlalchemy import text

from jetbase.cli.main import app


def test_fix_files_success(
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

        # Delete the migration file
        migrations_dir = os.path.join(os.getcwd(), "migrations")
        file_to_delete = os.path.join(migrations_dir, "V2__m2.sql")
        os.remove(file_to_delete)

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code != 0

        assert isinstance(result.exception, FileNotFoundError), (
            f"Expected FileNotFoundError but got {type(result.exception)}"
        )

        result = runner.invoke(app, ["fix-files"])
        assert result.exit_code == 0

    with clean_db.connect() as connection:
        result = connection.execute(
            (text("select version from jetbase_migrations where version = '2'"))
        )
        fixed_version = result.scalar()
        assert fixed_version is None

        result = runner.invoke(app, ["upgrade"])
        assert result.exit_code == 0
