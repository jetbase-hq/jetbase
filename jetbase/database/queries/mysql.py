from sqlalchemy import TextClause, text

from jetbase.database.queries.base import BaseQueries


class MySQLQueries(BaseQueries):
    """
    MySQL-specific SQL queries.

    Provides MySQL-compatible implementations for queries that differ
    from the default PostgreSQL syntax.
    """

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_migrations (
                order_executed INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(255),
                description VARCHAR(500) NOT NULL,
                filename VARCHAR(512) NOT NULL,
                migration_type VARCHAR(32) NOT NULL,
                applied_at TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
                checksum VARCHAR(64) NOT NULL
            )
            """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'jetbase_migrations'
            """
        )

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'jetbase_lock'
            """
        )

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_lock (
                id INT PRIMARY KEY CHECK (id = 1),
                is_locked BOOLEAN NOT NULL DEFAULT FALSE,
                locked_at TIMESTAMP(6) NULL,
                process_id VARCHAR(36)
            )
            """
        )

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        return text(
            """
            INSERT IGNORE INTO jetbase_lock (id, is_locked)
            VALUES (1, FALSE)
            """
        )

    @staticmethod
    def acquire_lock_stmt() -> TextClause:
        return text(
            """
            UPDATE jetbase_lock
            SET is_locked = TRUE,
                locked_at = CURRENT_TIMESTAMP(6),
                process_id = :process_id
            WHERE id = 1 AND is_locked = FALSE
            """
        )

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        return text(
            """
            UPDATE jetbase_migrations
            SET checksum = :checksum,
                applied_at = CURRENT_TIMESTAMP(6)
            WHERE filename = :filename
            AND migration_type = :migration_type
            """
        )
