import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.engine import CursorResult

from jetbase.repositories.lock_repo import lock_database, release_lock


def acquire_lock() -> str:
    """
    Acquire the migration lock immediately.

    Attempts to acquire the database migration lock using a unique process ID.
    The lock prevents concurrent migrations from running.

    Returns:
        str: Unique UUID process identifier for this lock acquisition.

    Raises:
        RuntimeError: If the lock is already held by another process.
    """
    process_id = str(uuid.uuid4())

    result: CursorResult = lock_database(process_id=process_id)

    if result.rowcount == 0:  # already locked
        raise RuntimeError(
            "Migration lock is already held by another process.\n\n"
            "If you are completely sure that no other migrations are running, "
            "you can unlock using:\n"
            "  jetbase unlock\n\n"
            "WARNING: Unlocking then running a migration while another migration process is running may "
            "lead to database corruption."
        )

    return process_id


@contextmanager
def migration_lock() -> Generator[None, None, None]:
    """
    Context manager for acquiring and releasing the migration lock.

    Acquires the lock on entry and ensures it is released on exit,
    even if an exception occurs. Fails immediately if the lock is
    already held by another process.

    Yields:
        None: Yields control to the context block.

    Raises:
        RuntimeError: If the lock is already held by another process.

    Example:
        >>> with migration_lock():
        ...     run_migration()
    """
    process_id: str | None = None
    try:
        process_id = acquire_lock()
        yield
    finally:
        if process_id:
            release_lock(process_id=process_id)
