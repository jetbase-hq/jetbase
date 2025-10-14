from sqlalchemy import create_engine, Engine, Result, text

from jetbase.queries import (
    CREATE_MIGRATIONS_TABLE_STMT,
    LATEST_VERSION_QUERY,
    INSERT_VERSION_STMT,
)
from jetbase.config import get_sqlalchemy_url


def get_last_updated_version() -> str | None:
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result: Result[tuple[str]] = connection.execute(LATEST_VERSION_QUERY)
        latest_version: str | None = result.scalar()
    if not latest_version:
        return None
    return latest_version


def create_migrations_table() -> None:
    engine: Engine = create_engine(url=get_sqlalchemy_url())
    with engine.begin() as connection:
        connection.execute(statement=CREATE_MIGRATIONS_TABLE_STMT)


def run_migration(sql_statements: list[str], version: str) -> None:
    engine: Engine = create_engine(url=get_sqlalchemy_url())
    with engine.begin() as connection:
        for statement in sql_statements:
            connection.execute(text(statement))
        connection.execute(
            statement=INSERT_VERSION_STMT, parameters={"version": version}
        )
