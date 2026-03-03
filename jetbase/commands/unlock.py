from jetbase.config import get_config
from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType
from jetbase.logging import logger
from jetbase.repositories.lock_repo import (
    lock_table_exists,
    unlock_database,
)
from jetbase.repositories.migrations_repo import migrations_table_exists


def unlock_cmd() -> None:
    """
    Force release the migration lock.

    Unconditionally releases the migration lock in the jetbase_lock table.
    Use this only if you are certain that no migration is currently running,
    as unlocking during an active migration can cause database corruption.

    For ClickHouse, displays a message that locking is not supported.

    Returns:
        None: Prints "Unlock successful." to stdout.
    """
    # Check for ClickHouse first
    sqlalchemy_url: str = get_config(required={"sqlalchemy_url"}).sqlalchemy_url
    if detect_db(sqlalchemy_url) == DatabaseType.CLICKHOUSE:
        logger.info("ClickHouse does not support database locking. No lock to release.")
        return

    if not lock_table_exists() or not migrations_table_exists():
        logger.info("Unlock successful.")
        return
    #
    unlock_database()

    logger.info("Unlock successful.")
