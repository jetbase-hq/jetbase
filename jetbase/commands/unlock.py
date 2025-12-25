from sqlalchemy import Engine, create_engine

from jetbase.config import get_config
from jetbase.core.repository import lock_table_exists, migrations_table_exists
from jetbase.queries.base import QueryMethod
from jetbase.queries.query_loader import get_query

sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url


def unlock_cmd() -> None:
    """
    Unlocks the database migration lock unconditionally.
    Use with caution. This should only be used if you are certain that no migration
    is currently running.
    Returns:
    None: This function does not return a value. It prints the unlock status
            to standard output.
    """

    if not lock_table_exists() or not migrations_table_exists():
        print("Unlock successful.")
        return
    engine: Engine = create_engine(url=sqlalchemy_url)

    with engine.begin() as connection:
        connection.execute(get_query(query_name=QueryMethod.FORCE_UNLOCK_STMT))

    print("Unlock successful.")
