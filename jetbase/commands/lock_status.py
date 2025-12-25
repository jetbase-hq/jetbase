from sqlalchemy import Engine, create_engine

from jetbase.config import get_config
from jetbase.core.repository import lock_table_exists, migrations_table_exists
from jetbase.queries.base import QueryMethod
from jetbase.queries.query_loader import get_query

sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url


def lock_status_cmd() -> None:
    """
    Check and display the current lock status of the database migration system.
    This function queries the current lock status. It prints whether the database
    migrations are locked or unlocked, and if locked, displays the timestamp
    when it was locked.
    Returns:
        None: Prints the lock status directly to stdout.
    """

    if not lock_table_exists() or not migrations_table_exists():
        print("Status: UNLOCKED")
        return

    engine: Engine = create_engine(url=sqlalchemy_url)

    with engine.begin() as connection:
        result = connection.execute(
            get_query(query_name=QueryMethod.CHECK_LOCK_STATUS_STMT)
        )
        row = result.fetchone()
        if row and row[0]:  # is_locked
            locked_at = row[1]

            print(f"Status: LOCKED\nLocked At: {locked_at}")
        else:
            print("Status: UNLOCKED")
