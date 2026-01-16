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
        """
        Get MySQL statement to create the jetbase_migrations table.

        Uses AUTO_INCREMENT instead of PostgreSQL's GENERATED ALWAYS AS IDENTITY.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_migrations (
                order_executed INT AUTO_INCREMENT PRIMARY KEY,
                version VARCHAR(255),
                description VARCHAR(500) NOT NULL,
                filename VARCHAR(512) NOT NULL,
                migration_type VARCHAR(32) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                checksum VARCHAR(64) NOT NULL
            )
            """
        )

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        """
        Get MySQL query to check if the jetbase_migrations table exists.

        Uses DATABASE() function to get the current database name instead
        of PostgreSQL's 'public' schema.

        Returns:
            TextClause: SQLAlchemy text clause that returns a boolean.
        """
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
        """
        Get MySQL query to check if the jetbase_lock table exists.

        Uses DATABASE() function to get the current database name instead
        of PostgreSQL's 'public' schema.

        Returns:
            TextClause: SQLAlchemy text clause that returns a boolean.
        """
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
        """
        Get MySQL statement to create the jetbase_lock table.

        Uses MySQL-compatible syntax. CHECK constraint is enforced in
        MySQL 8.0.16+.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return text(
            """
            CREATE TABLE IF NOT EXISTS jetbase_lock (
                id INT PRIMARY KEY CHECK (id = 1),
                is_locked BOOLEAN NOT NULL DEFAULT FALSE,
                locked_at TIMESTAMP NULL,
                process_id VARCHAR(36)
            )
            """
        )

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        """
        Get MySQL statement to initialize the lock record.

        Uses INSERT IGNORE to avoid errors if the record already exists,
        since MySQL doesn't support INSERT ... WHERE NOT EXISTS referencing
        the same table.

        Returns:
            TextClause: SQLAlchemy text clause for the INSERT statement.
        """
        return text(
            """
            INSERT IGNORE INTO jetbase_lock (id, is_locked)
            VALUES (1, FALSE)
            """
        )
