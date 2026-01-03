from jetbase.models import LockStatus
from jetbase.repositories.lock_repo import fetch_lock_status, lock_table_exists
from jetbase.repositories.migrations_repo import migrations_table_exists


def lock_status_cmd() -> None:
    """
    Display whether the migration lock is currently held.

    Queries the jetbase_lock table to check if migrations are currently
    locked. If locked, displays the timestamp when the lock was acquired.

    Returns:
        None: Prints "LOCKED" with timestamp or "UNLOCKED" to stdout.
    """

    if not lock_table_exists() or not migrations_table_exists():
        print("Status: UNLOCKED")
        return

    lock_status: LockStatus = fetch_lock_status()
    if lock_status.is_locked:
        print(f"Status: LOCKED\nLocked At: {lock_status.locked_at}")
    else:
        print("Status: UNLOCKED")
