from sqlalchemy import TextClause, text

from jetbase.database.queries.base import BaseQueries


class DatabricksQueries(BaseQueries):
    """
    Databricks-specific SQL queries.

    Provides Databricks-compatible implementations for queries that differ
    from the default PostgreSQL syntax.
    """

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_migrations (
                order_executed BIGINT GENERATED ALWAYS AS IDENTITY,
                version STRING,
                description STRING NOT NULL,
                filename STRING NOT NULL,
                migration_type STRING NOT NULL,
                applied_at TIMESTAMP NOT NULL,
                checksum STRING NOT NULL
            )
            """
        )

    @staticmethod
    def insert_version_stmt() -> TextClause:
        return text(
            """
            INSERT INTO jetbase_migrations (version, description, filename, migration_type, checksum, applied_at) 
            VALUES (:version, :description, :filename, :migration_type, :checksum, CURRENT_TIMESTAMP())
            """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
              AND LOWER(TABLE_NAME) = 'jetbase_migrations'
            """
        )

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        return text(
            """
            SELECT COUNT(*) > 0 AS table_exists
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = CURRENT_SCHEMA()
              AND LOWER(TABLE_NAME) = 'jetbase_lock'
            """
        )

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_lock (
                id INT,
                is_locked BOOLEAN NOT NULL,
                locked_at TIMESTAMP,
                process_id STRING
            )
            """
        )

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
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
        return text(
            """
            UPDATE jetbase_migrations
            SET checksum = :checksum,
                applied_at = CURRENT_TIMESTAMP()
            WHERE filename = :filename
            AND migration_type = :migration_type
            """
        )
