from jetbase.config import get_config
from jetbase.repositories.lock_repo import (
    lock_table_exists,
    unlock_database,
)
from jetbase.repositories.migrations_repo import migrations_table_exists

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
    #
    unlock_database()

    print("Unlock successful.")
