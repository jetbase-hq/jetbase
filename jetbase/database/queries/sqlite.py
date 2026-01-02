from sqlalchemy import TextClause, text

from jetbase.database.queries.base import BaseQueries


class SQLiteQueries(BaseQueries):
    """
    SQLite-specific SQL queries.

    Provides SQLite-compatible implementations for queries that differ
    from the default PostgreSQL syntax.
    """

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        """
        Get SQLite statement to create the jetbase_migrations table.

        Uses INTEGER PRIMARY KEY AUTOINCREMENT and TEXT types for
        SQLite compatibility.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
        CREATE TABLE IF NOT EXISTS jetbase_migrations (
            order_executed INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT,
            description TEXT,
            filename TEXT NOT NULL,
            migration_type TEXT NOT NULL,
            applied_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
            checksum TEXT
        );
        """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        """
        Get SQLite query to check if the jetbase_migrations table exists.

        Uses sqlite_master to check for table existence.

        Returns:
            TextClause: SQLAlchemy text clause that returns a boolean.
        """
        return text(
            """
        SELECT COUNT(*) > 0
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'jetbase_migrations'
        """
        )

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        """
        Get SQLite query to check if the jetbase_lock table exists.

        Uses sqlite_master to check for table existence.

        Returns:
            TextClause: SQLAlchemy text clause that returns the table name
                if it exists.
        """
        return text(
            """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='jetbase_lock'
        """
        )

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        """
        Get SQLite statement to create the jetbase_lock table.

        Uses CHECK constraint to ensure only one row exists, and
        TEXT type for timestamp storage.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
        CREATE TABLE IF NOT EXISTS jetbase_lock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            is_locked BOOLEAN NOT NULL DEFAULT 0,
            locked_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
            process_id TEXT
        );
        """
        )

    @staticmethod
    def force_unlock_stmt() -> TextClause:
        """
        Get SQLite statement to force release the migration lock.

        Sets is_locked to 0 and clears the locked_at and process_id fields.

        Returns:
            TextClause: SQLAlchemy text clause for the UPDATE statement.
        """
        return text(
            """
        UPDATE jetbase_lock
        SET is_locked = 0,
            locked_at = NULL,
            process_id = NULL
        WHERE id = 1;
        """
        )

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        """
        Get SQLite statement to initialize the lock record.

        Uses INSERT OR IGNORE to create the initial unlocked record
        without failing if it already exists.

        Returns:
            TextClause: SQLAlchemy text clause for the INSERT statement.
        """
        return text(
            """
        INSERT OR IGNORE INTO jetbase_lock (id, is_locked)
        VALUES (1, 0)
        """
        )

    @staticmethod
    def acquire_lock_stmt() -> TextClause:
        """
        Get SQLite statement to atomically acquire the migration lock.

        Only updates if the lock is not currently held. Uses STRFTIME
        for timestamp generation.

        Returns:
            TextClause: SQLAlchemy text clause with :process_id parameter.
        """
        return text(
            """
        UPDATE jetbase_lock
        SET is_locked = 1,
            locked_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW'),
            process_id = :process_id
        WHERE id = 1 AND is_locked = 0
        """
        )

    @staticmethod
    def release_lock_stmt() -> TextClause:
        """
        Get SQLite statement to release the migration lock.

        Only releases if the lock is held by the specified process ID.

        Returns:
            TextClause: SQLAlchemy text clause with :process_id parameter.
        """
        return text(
            """
        UPDATE jetbase_lock
        SET is_locked = 0,
            locked_at = NULL,
            process_id = NULL
        WHERE id = 1 AND process_id = :process_id
        """
        )

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        """
        Get SQLite statement to update a repeatable migration record.

        Updates the checksum and applied_at timestamp using SQLite's
        STRFTIME function for the current time.

        Returns:
            TextClause: SQLAlchemy text clause with :checksum, :filename,
                and :migration_type parameters.
        """
        return text(
            """
        UPDATE jetbase_migrations
        SET checksum = :checksum,
            applied_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
        WHERE filename = :filename
        AND migration_type = :migration_type
        """
        )
