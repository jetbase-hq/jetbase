from sqlalchemy import TextClause, text

from jetbase.queries.base import BaseQueries


class SQLiteQueries(BaseQueries):
    """SQLite-specific queries."""

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        return text("""
        CREATE TABLE IF NOT EXISTS jetbase_migrations (
            order_executed INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT,
            description TEXT,
            filename TEXT NOT NULL,
            migration_type TEXT NOT NULL,
            applied_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
            checksum TEXT
        );
        """)

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        return text("""
        SELECT COUNT(*) > 0
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'jetbase_migrations'
        """)

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        return text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='jetbase_lock'
        """)

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        return text("""
        CREATE TABLE IF NOT EXISTS jetbase_lock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            is_locked BOOLEAN NOT NULL DEFAULT 0,
            locked_at TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
            process_id TEXT
        );
        """)

    @staticmethod
    def force_unlock_stmt() -> TextClause:
        return text("""
        UPDATE jetbase_lock
        SET is_locked = 0,
            locked_at = NULL,
            process_id = NULL
        WHERE id = 1;
        """)

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        return text("""
        INSERT OR IGNORE INTO jetbase_lock (id, is_locked)
        VALUES (1, 0)
        """)

    @staticmethod
    def acquire_lock_stmt() -> TextClause:
        return text("""
        UPDATE jetbase_lock
        SET is_locked = 1,
            locked_at = :locked_at,
            process_id = :process_id
        WHERE id = 1 AND is_locked = 0
        """)

    @staticmethod
    def release_lock_stmt() -> TextClause:
        return text("""
        UPDATE jetbase_lock
        SET is_locked = 0,
            locked_at = NULL,
            process_id = NULL
        WHERE id = 1 AND process_id = :process_id
        """)

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        return text("""
        UPDATE jetbase_migrations
        SET checksum = :checksum,
            applied_at = STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
        WHERE filename = :filename
        AND migration_type = :migration_type
        """)
