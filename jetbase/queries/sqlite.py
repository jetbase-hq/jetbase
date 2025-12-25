from sqlalchemy import TextClause

from jetbase.queries.base import BaseQueries


class SQLiteQueries(BaseQueries):
    """SQLite-specific queries."""

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        return TextClause("""
        CREATE TABLE IF NOT EXISTS jetbase_migrations (
            order_executed INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT,
            description TEXT,
            filename TEXT,
            migration_type TEXT NOT NULL,
            applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT
        );
        """)

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        return TextClause("""
        SELECT COUNT(*) > 0
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'jetbase_migrations'
        """)

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        return TextClause("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='lock';
        """)

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        return TextClause("""
        CREATE TABLE IF NOT EXISTS lock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            is_locked BOOLEAN NOT NULL DEFAULT 0,
            locked_at TIMESTAMP
        );
        """)
