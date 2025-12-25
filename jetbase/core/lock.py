import datetime as dt
import uuid
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine

from jetbase.config import get_config
from jetbase.queries.base import QueryMethod
from jetbase.queries.query_loader import get_query

sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url


def create_lock_table_if_not_exists() -> None:
    """
    Create the migrations lock table if it doesn't exist.
    Returns:
        None
    """
    engine: Engine = create_engine(url=sqlalchemy_url)

    with engine.begin() as connection:
        connection.execute(get_query(query_name=QueryMethod.CREATE_LOCK_TABLE_STMT))

        # Initialize with single row if empty
        connection.execute(
            get_query(query_name=QueryMethod.INITIALIZE_LOCK_RECORD_STMT)
        )


def acquire_lock() -> str:
    """
    Attempt to acquire the migration lock immediately.

    Returns:
        process_id: Unique identifier for this lock acquisition

    Raises:
        RuntimeError: If lock is already held by another process
    """
    process_id = str(uuid.uuid4())
    engine: Engine = create_engine(url=sqlalchemy_url)

    with engine.begin() as connection:
        # Try to acquire lock
        result = connection.execute(
            get_query(query_name=QueryMethod.ACQUIRE_LOCK_STMT),
            {
                "locked_at": dt.datetime.now(dt.timezone.utc),
                "process_id": process_id,
            },
        )

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


def release_lock(process_id: str) -> None:
    """
    Release the migration lock.

    Args:
        process_id: The process ID that acquired the lock
    """
    engine: Engine = create_engine(url=sqlalchemy_url)

    with engine.begin() as connection:
        connection.execute(
            get_query(query_name=QueryMethod.RELEASE_LOCK_STMT),
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
