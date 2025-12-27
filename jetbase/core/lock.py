import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.engine import CursorResult

from jetbase.repositories.lock_repo import lock_database, release_lock


def acquire_lock() -> str:
    """
    Attempt to acquire the migration lock immediately.

    Returns:
        process_id: Unique identifier for this lock acquisition

    Raises:
        RuntimeError: If lock is already held by another process
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
