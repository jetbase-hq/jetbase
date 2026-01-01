from jetbase.config import get_config
from jetbase.repositories.lock_repo import (
    lock_table_exists,
    unlock_database,
)
from jetbase.repositories.migrations_repo import migrations_table_exists

sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url


def unlock_cmd() -> None:
    """
    Force release the migration lock.

    Unconditionally releases the migration lock in the jetbase_lock table.
    Use this only if you are certain that no migration is currently running,
    as unlocking during an active migration can cause database corruption.

    Returns:
        None: Prints "Unlock successful." to stdout.
    """

    if not lock_table_exists() or not migrations_table_exists():
        print("Unlock successful.")
        return
    #
    unlock_database()

    print("Unlock successful.")
