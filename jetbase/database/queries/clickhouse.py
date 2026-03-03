from sqlalchemy import TextClause, text

from jetbase.database.queries.base import BaseQueries
from jetbase.enums import MigrationType


class ClickHouseQueries(BaseQueries):
    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_migrations (
                order_executed UInt64,
                version Nullable(String),
                description String,
                filename String,
                migration_type String,
                applied_at DateTime64(6) DEFAULT now64(6),
                checksum String
            ) ENGINE = MergeTree()
            ORDER BY order_executed
            """
        )

    @staticmethod
    def insert_version_stmt() -> TextClause:
        return text(
            """
            INSERT INTO jetbase_migrations (order_executed, version, description, filename, migration_type, checksum, applied_at) 
            SELECT 
                (SELECT COALESCE(MAX(order_executed), 0) + 1 FROM jetbase_migrations),
                :version, 
                :description, 
                :filename, 
                :migration_type, 
                :checksum,
                now64(6)
            """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        return text(
            """
            SELECT count() > 0 AS table_exists
            FROM system.tables
            WHERE database = currentDatabase()
              AND name = 'jetbase_migrations'
            """
        )

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        return text("SELECT 0 AS table_exists")

    @staticmethod
    def latest_version_query() -> TextClause:
        return text(
            f"""
            SELECT 
                version 
            FROM 
                jetbase_migrations
            WHERE
                migration_type = '{MigrationType.VERSIONED.value}'
            ORDER BY 
                order_executed DESC
            LIMIT 1
            """
        )

    @staticmethod
    def latest_versions_query() -> TextClause:
        return text(
            f"""
            SELECT 
                version 
            FROM 
                jetbase_migrations
            WHERE
                migration_type = '{MigrationType.VERSIONED.value}'
            ORDER BY 
                order_executed DESC
            LIMIT :limit
            """
        )

    @staticmethod
    def latest_versions_by_starting_version_query() -> TextClause:
        return text(
            f"""
            SELECT
                version
            FROM
                jetbase_migrations
            WHERE order_executed > 
                (SELECT order_executed FROM jetbase_migrations 
                    WHERE version = :starting_version AND migration_type = '{MigrationType.VERSIONED.value}')
            AND migration_type = '{MigrationType.VERSIONED.value}'
            ORDER BY 
                order_executed DESC
            """
        )

    @staticmethod
    def delete_version_stmt() -> TextClause:
        return text(
            f"""
            ALTER TABLE jetbase_migrations DELETE 
            WHERE version = :version
            AND migration_type = '{MigrationType.VERSIONED.value}'
            SETTINGS mutations_sync = 1
            """
        )

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        return text(
            """
            ALTER TABLE jetbase_migrations
            UPDATE checksum = :checksum, applied_at = now64(6)
            WHERE filename = :filename
            AND migration_type = :migration_type
            SETTINGS mutations_sync = 1
            """
        )

    @staticmethod
    def repair_migration_checksum_stmt() -> TextClause:
        return text(
            f"""
            ALTER TABLE jetbase_migrations
            UPDATE checksum = :checksum
            WHERE version = :version
            AND migration_type = '{MigrationType.VERSIONED.value}'
            SETTINGS mutations_sync = 1
            """
        )

    @staticmethod
    def delete_missing_version_stmt() -> TextClause:
        return text(
            f"""
            ALTER TABLE jetbase_migrations DELETE
            WHERE version = :version
            AND migration_type = '{MigrationType.VERSIONED.value}'
            SETTINGS mutations_sync = 1
            """
        )

    @staticmethod
    def delete_missing_repeatable_stmt() -> TextClause:
        return text(
            f"""
            ALTER TABLE jetbase_migrations DELETE
            WHERE filename = :filename
            AND migration_type IN ('{MigrationType.RUNS_ALWAYS.value}', '{MigrationType.RUNS_ON_CHANGE.value}')
            SETTINGS mutations_sync = 1
            """
        )

    @staticmethod
    def migration_records_query(
        ascending: bool = True,
        all_repeatables: bool = False,
        migration_type: MigrationType | None = None,
    ) -> TextClause:
        query: str = f"""
            SELECT
                order_executed, 
                version, 
                description,
                filename,
                migration_type,
                applied_at,
                checksum  
            FROM
                jetbase_migrations
            {"WHERE migration_type = " + f"'{migration_type.value}'" if migration_type else ""}
            {"WHERE migration_type IN ('RUNS_ON_CHANGE', 'RUNS_ALWAYS')" if all_repeatables else ""}
            ORDER BY
                order_executed {"ASC" if ascending else "DESC"}
        """

        return text(query)
