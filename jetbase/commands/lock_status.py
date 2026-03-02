from jetbase.logging import logger
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
        logger.info("Status: UNLOCKED")
        return

    lock_status: LockStatus = fetch_lock_status()
    if lock_status.is_locked:
        logger.info("Status: LOCKED\nLocked At: %s", lock_status.locked_at)
    else:
        logger.info("Status: UNLOCKED")
