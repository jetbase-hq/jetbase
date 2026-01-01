from typing import Any

from sqlalchemy import Result, Row
from sqlalchemy.engine import CursorResult

from jetbase.database.connection import get_db_connection
from jetbase.database.queries.base import QueryMethod
from jetbase.database.queries.query_loader import get_query
from jetbase.models import LockStatus


def lock_table_exists() -> bool:
    """
    Check if the jetbase_lock table exists in the database.

    Queries the database to determine if the lock table has been created.

    Returns:
        bool: True if the jetbase_lock table exists, False otherwise.
    """
    with get_db_connection() as connection:
        result: Result[tuple[bool]] = connection.execute(
            statement=get_query(QueryMethod.CHECK_IF_LOCK_TABLE_EXISTS_QUERY)
        )
        table_exists: bool = result.scalar_one()

    return table_exists


def create_lock_table_if_not_exists() -> None:
    """
    Create the jetbase_lock table if it doesn't already exist.

    Creates the lock table and initializes it with a single unlocked
    record. This table is used to prevent concurrent migrations.

    Returns:
        None: Table is created as a side effect.
    """
    with get_db_connection() as connection:
        connection.execute(get_query(query_name=QueryMethod.CREATE_LOCK_TABLE_STMT))

        # Initialize with single row if empty
        connection.execute(
            get_query(query_name=QueryMethod.INITIALIZE_LOCK_RECORD_STMT)
        )


def fetch_lock_status() -> LockStatus:
    """
    Get the current migration lock status from the database.

    Queries the jetbase_lock table to determine if migrations are
    currently locked and when the lock was acquired.

    Returns:
        LockStatus: A dataclass containing is_locked (bool) and
            locked_at (datetime | None) fields.
    """
    with get_db_connection() as connection:
        result: Row[Any] | None = connection.execute(
            get_query(query_name=QueryMethod.CHECK_LOCK_STATUS_STMT)
        ).first()
        if result:
            return LockStatus(is_locked=result.is_locked, locked_at=result.locked_at)
        return LockStatus(is_locked=False, locked_at=None)


def unlock_database() -> None:
    """
    Force unlock the migration lock unconditionally.

    Clears the lock status regardless of which process holds it.
    Use with caution as this can cause issues if a migration is
    actually running.

    Returns:
        None: Lock is released as a side effect.
    """
    with get_db_connection() as connection:
        connection.execute(get_query(query_name=QueryMethod.FORCE_UNLOCK_STMT))


def lock_database(process_id: str) -> CursorResult:
    """
    Attempt to acquire the migration lock for a specific process.

    Uses an atomic update to acquire the lock only if it is not
    already held. The rowcount of the result indicates success.

    Args:
        process_id (str): Unique identifier for the process acquiring
            the lock.

    Returns:
        CursorResult: Result object where rowcount=1 indicates success,
            rowcount=0 indicates the lock is already held.
    """
    with get_db_connection() as connection:
        result = connection.execute(
            get_query(query_name=QueryMethod.ACQUIRE_LOCK_STMT),
            {
                "process_id": process_id,
            },
        )

    return result


def release_lock(process_id: str) -> None:
    """
    Release the migration lock held by a specific process.

    Only releases the lock if it is currently held by the specified
    process ID.

    Args:
        process_id (str): The unique identifier of the process that
            acquired the lock.

    Returns:
        None: Lock is released as a side effect.
    """

    with get_db_connection() as connection:
        connection.execute(
            get_query(query_name=QueryMethod.RELEASE_LOCK_STMT),
            {"process_id": process_id},
        )
