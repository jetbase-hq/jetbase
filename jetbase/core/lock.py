import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import Engine, create_engine

from jetbase.config import get_sqlalchemy_url
from jetbase.core.repository import lock_table_exists, migrations_table_exists
from jetbase.queries import (
    ACQUIRE_LOCK_STMT,
    CHECK_LOCK_STATUS_STMT,
    CREATE_LOCK_TABLE_STMT,
    FORCE_UNLOCK_STMT,
    INITIALIZE_LOCK_RECORD_STMT,
    RELEASE_LOCK_STMT,
)


def create_lock_table_if_not_exists() -> None:
    """Create the migrations lock table if it doesn't exist."""
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        connection.execute(CREATE_LOCK_TABLE_STMT)

        # Initialize with single row if empty
        connection.execute(INITIALIZE_LOCK_RECORD_STMT)


def acquire_lock() -> str:
    """
    Attempt to acquire the migration lock immediately.

    Returns:
        process_id: Unique identifier for this lock acquisition

    Raises:
        RuntimeError: If lock is already held by another process
    """
    process_id = str(uuid.uuid4())
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        # Try to acquire lock
        result = connection.execute(
            ACQUIRE_LOCK_STMT,
            {
                "locked_at": datetime.now(timezone.utc),
                "process_id": process_id,
            },
        )

        if result.rowcount == 0:  # already locked``
            raise RuntimeError(
                "Migration lock is already held by another process.\n\n"
                "If you are completely sure that no other migrations are running, "
                "you can forcibly unlock using:\n"
                "  jetbase force-unlock\n\n"
                "WARNING: Force-unlocking then running a migration while another migration process is running may "
                "lead to database corruption."
            )

        return process_id


def release_lock(process_id: str) -> None:
    """
    Release the migration lock.

    Args:
        process_id: The process ID that acquired the lock
    """
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        connection.execute(
            RELEASE_LOCK_STMT,
            {"process_id": process_id},
        )


@contextmanager
def migration_lock() -> Generator[None, None, None]:
    """
    Context manager for acquiring and releasing migration lock.
    Fails immediately if lock is already held.

    Usage:
        with migration_lock():
            # Run migrations
    """
    process_id: str | None = None
    try:
        process_id = acquire_lock()
        yield
    finally:
        if process_id:
            release_lock(process_id=process_id)


def force_unlock_cmd() -> None:
    """
    Command to forcibly unlock the migration lock.
    """
    if not lock_table_exists() or not migrations_table_exists():
        print("Unlock successful.")
        return
    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        connection.execute(FORCE_UNLOCK_STMT)

    print("Unlock successful.")


def check_lock_cmd() -> None:
    """
    Command to check if migrations are currently locked.
    """
    if not lock_table_exists() or not migrations_table_exists():
        print("Status: UNLOCKED")
        return

    engine: Engine = create_engine(url=get_sqlalchemy_url())

    with engine.begin() as connection:
        result = connection.execute(CHECK_LOCK_STATUS_STMT)
        row = result.fetchone()
        if row and row[0]:  # is_locked
            locked_at = row[1]

            print(f"Status: LOCKED\nLocked At: {locked_at}")
        else:
            print("Status: UNLOCKED")
