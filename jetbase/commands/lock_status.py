from jetbase.config import get_config
from jetbase.core.models import LockStatus
from jetbase.core.repository import (
    fetch_lock_status,
    lock_table_exists,
    migrations_table_exists,
)

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

    lock_status: LockStatus = fetch_lock_status()
    if lock_status.is_locked:
        print(f"Status: LOCKED\nLocked At: {lock_status.locked_at}")
    else:
        print("Status: UNLOCKED")
