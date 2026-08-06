import os

import pytest
from sqlalchemy import text

from jetbase.cli.main import app
from jetbase.repositories.migrations_repo import (
    create_migrations_table_if_not_exists,
    migrations_table_exists,
)
from tests.utils import is_postgres


@pytest.mark.skipif(not is_postgres(), reason="postgres_schema is PostgreSQL-only")
def test_migrations_table_exists_detects_custom_schema(
    test_db_url, custom_postgres_schema, setup_migrations_versions_only
):
    os.chdir("jetbase")

    create_migrations_table_if_not_exists()

    assert migrations_table_exists() is True


@pytest.mark.skipif(not is_postgres(), reason="postgres_schema is PostgreSQL-only")
def test_upgrade_is_idempotent_in_custom_schema(
    runner,
    test_db_url,
    clean_db,
    custom_postgres_schema,
    setup_migrations_versions_only,
    caplog,
):
    os.chdir("jetbase")
    assert runner.invoke(app, ["upgrade"]).exit_code == 0
    caplog.clear()
    second_run = runner.invoke(app, ["upgrade"])
    assert second_run.exit_code == 0, second_run.exception
    assert "up to date" in caplog.text.lower()
    with clean_db.connect() as connection:
        count = connection.execute(
            text(f"SELECT COUNT(*) FROM {custom_postgres_schema}.jetbase_migrations")
        ).scalar()
        assert count == 5
