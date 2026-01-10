from sqlalchemy import TextClause, text

from jetbase.database.queries.base import BaseQueries


class SnowflakeQueries(BaseQueries):
    """
    Snowflake-specific SQL queries.

    Provides Snowflake-compatible implementations for queries that differ
    from the default PostgreSQL syntax.
    """

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        """
        Get Snowflake statement to create the jetbase_migrations table.

        Uses AUTOINCREMENT for the identity column and Snowflake-compatible
        data types.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_migrations (
                order_executed INT AUTOINCREMENT PRIMARY KEY,
                version VARCHAR(255),
                description VARCHAR(500) NOT NULL,
                filename VARCHAR(512) NOT NULL,
                migration_type VARCHAR(32) NOT NULL,
                applied_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP() NOT NULL,
                checksum VARCHAR(64) NOT NULL
            )
            """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        """
        Get Snowflake query to check if the jetbase_migrations table exists.

        Uses INFORMATION_SCHEMA.TABLES with CURRENT_SCHEMA() for Snowflake
        compatibility.

        Returns:
            TextClause: SQLAlchemy text clause that returns a count.
        """
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
              AND TABLE_NAME = 'JETBASE_MIGRATIONS'
            """
        )

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        """
        Get Snowflake query to check if the jetbase_lock table exists.

        Uses INFORMATION_SCHEMA.TABLES with CURRENT_SCHEMA() for Snowflake
        compatibility.

        Returns:
            TextClause: SQLAlchemy text clause that returns a count.
        """
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
              AND TABLE_NAME = 'JETBASE_LOCK'
            """
        )

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        """
        Get Snowflake statement to create the jetbase_lock table.

        Uses Snowflake-compatible syntax for PRIMARY KEY and BOOLEAN types.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_lock (
                id INTEGER PRIMARY KEY,
                is_locked BOOLEAN NOT NULL DEFAULT FALSE,
                locked_at TIMESTAMP_NTZ,
                process_id VARCHAR(36)
            )
            """
        )

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        """
        Get Snowflake statement to initialize the lock record.

        Uses MERGE statement for Snowflake-optimized upsert behavior.

        Returns:
            TextClause: SQLAlchemy text clause for the MERGE statement.
        """
        return text(
            """
            MERGE INTO jetbase_lock AS target
            USING (SELECT 1 AS id, FALSE AS is_locked) AS source
            ON target.id = source.id
            WHEN NOT MATCHED THEN
                INSERT (id, is_locked) VALUES (source.id, source.is_locked)
            """
        )

    @staticmethod
    def acquire_lock_stmt() -> TextClause:
        """
        Get Snowflake statement to atomically acquire the migration lock.

        Uses CURRENT_TIMESTAMP() function for Snowflake compatibility.

        Returns:
            TextClause: SQLAlchemy text clause with :process_id parameter.
        """
        return text(
            """
            UPDATE jetbase_lock
            SET is_locked = TRUE,
                locked_at = CURRENT_TIMESTAMP(),
                process_id = :process_id
            WHERE id = 1 AND is_locked = FALSE
            """
        )

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        """
        Get Snowflake statement to update a repeatable migration record.

        Uses CURRENT_TIMESTAMP() function for Snowflake compatibility.

        Returns:
            TextClause: SQLAlchemy text clause with :checksum, :filename,
                and :migration_type parameters.
        """
        return text(
            """
            UPDATE jetbase_migrations
            SET checksum = :checksum,
                applied_at = CURRENT_TIMESTAMP()
            WHERE filename = :filename
            AND migration_type = :migration_type
            """
        )
