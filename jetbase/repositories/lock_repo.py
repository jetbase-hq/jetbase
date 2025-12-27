import datetime as dt
from typing import Any

from sqlalchemy import Result, Row
from sqlalchemy.engine import CursorResult

from jetbase.core.models import LockStatus
from jetbase.queries.base import QueryMethod
from jetbase.queries.query_loader import get_query
from jetbase.repositories.db import get_db_connection


def lock_table_exists() -> bool:
    """
    Check if the jetbase_lock table exists in the database.
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
    Create the migrations lock table if it doesn't exist.
    Returns:
        None
    """
    with get_db_connection() as connection:
        connection.execute(get_query(query_name=QueryMethod.CREATE_LOCK_TABLE_STMT))

        # Initialize with single row if empty
        connection.execute(
            get_query(query_name=QueryMethod.INITIALIZE_LOCK_RECORD_STMT)
        )


def fetch_lock_status() -> LockStatus:
    with get_db_connection() as connection:
        result: Row[Any] | None = connection.execute(
            get_query(query_name=QueryMethod.CHECK_LOCK_STATUS_STMT)
        ).first()
        if result:
            return LockStatus(is_locked=result.is_locked, locked_at=result.locked_at)
        return LockStatus(is_locked=False, locked_at=None)


def unlock_database() -> None:
    with get_db_connection() as connection:
        connection.execute(get_query(query_name=QueryMethod.FORCE_UNLOCK_STMT))


def lock_database(process_id: str) -> CursorResult:
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
    Release the migration lock.

    Args:
        process_id: The process ID that acquired the lock
    """

    with get_db_connection() as connection:
        connection.execute(
            get_query(query_name=QueryMethod.RELEASE_LOCK_STMT),
            {"process_id": process_id},
        )
