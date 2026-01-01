from enum import Enum

from sqlalchemy import TextClause, text
from sqlalchemy.engine import make_url

from jetbase.database.queries import default_queries
from jetbase.enums import DatabaseType, MigrationType


class BaseQueries:
    """
    Base class for database-specific SQL queries.

    Provides default implementations for all migration-related SQL queries.
    Database-specific subclasses can override methods to provide optimized
    or syntax-compatible versions.
    """

    @staticmethod
    def latest_version_query() -> TextClause:
        """
        Get query to fetch the latest migration version.

        Returns:
            TextClause: SQLAlchemy text clause for the query.
        """
        return default_queries.LATEST_VERSION_QUERY

    @staticmethod
    def create_migrations_table_stmt() -> TextClause:
        """
        Get statement to create the jetbase_migrations table.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return default_queries.CREATE_MIGRATIONS_TABLE_STMT

    @staticmethod
    def insert_version_stmt() -> TextClause:
        """
        Get statement to insert a new migration record.

        Returns:
            TextClause: SQLAlchemy text clause with :version, :description,
                :filename, :migration_type, and :checksum parameters.
        """
        return default_queries.INSERT_VERSION_STMT

    @staticmethod
    def delete_version_stmt() -> TextClause:
        """
        Get statement to delete a migration record by version.

        Returns:
            TextClause: SQLAlchemy text clause with :version parameter.
        """
        return default_queries.DELETE_VERSION_STMT

    @staticmethod
    def latest_versions_query() -> TextClause:
        """
        Get query to fetch the latest N migration versions.

        Returns:
            TextClause: SQLAlchemy text clause with :limit parameter.
        """
        return default_queries.LATEST_VERSIONS_QUERY

    @staticmethod
    def latest_versions_by_starting_version_query() -> TextClause:
        """
        Get query to fetch all versions applied after a starting version.

        Returns:
            TextClause: SQLAlchemy text clause with :starting_version parameter.
        """
        return default_queries.LATEST_VERSIONS_BY_STARTING_VERSION_QUERY

    @staticmethod
    def check_if_version_exists_query() -> TextClause:
        """
        Get query to check if a specific version exists in the database.

        Returns:
            TextClause: SQLAlchemy text clause with :version parameter.
        """
        return default_queries.CHECK_IF_VERSION_EXISTS_QUERY

    @staticmethod
    def check_if_migrations_table_exists_query() -> TextClause:
        """
        Get query to check if the jetbase_migrations table exists.

        Returns:
            TextClause: SQLAlchemy text clause that returns a boolean.
        """
        return default_queries.CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY

    @staticmethod
    def check_if_lock_table_exists_query() -> TextClause:
        """
        Get query to check if the jetbase_lock table exists.

        Returns:
            TextClause: SQLAlchemy text clause that returns a boolean.
        """
        return default_queries.CHECK_IF_LOCK_TABLE_EXISTS_QUERY

    @staticmethod
    def migration_records_query(
        ascending: bool = True,
        all_repeatables: bool = False,
        migration_type: MigrationType | None = None,
    ) -> TextClause:
        """
        Get query to fetch migration records with optional filters.

        Args:
            ascending (bool): If True, order by applied_at ascending.
                Defaults to True.
            all_repeatables (bool): If True, filter to only repeatable
                migrations. Defaults to False.
            migration_type (MigrationType | None): If provided, filter to
                only this migration type. Defaults to None.

        Returns:
            TextClause: SQLAlchemy text clause for the filtered query.
        """
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
                applied_at {"ASC" if ascending else "DESC"}
        """

        return text(query)

    @staticmethod
    def create_lock_table_stmt() -> TextClause:
        """
        Get statement to create the jetbase_lock table.

        Returns:
            TextClause: SQLAlchemy text clause for the CREATE TABLE statement.
        """
        return default_queries.CREATE_LOCK_TABLE_STMT

    @staticmethod
    def initialize_lock_record_stmt() -> TextClause:
        """
        Get statement to initialize the lock record with an unlocked state.

        Returns:
            TextClause: SQLAlchemy text clause for the INSERT statement.
        """
        return default_queries.INITIALIZE_LOCK_RECORD_STMT

    @staticmethod
    def check_lock_status_stmt() -> TextClause:
        """
        Get statement to check the current lock status.

        Returns:
            TextClause: SQLAlchemy text clause that returns is_locked
                and locked_at columns.
        """
        return default_queries.CHECK_LOCK_STATUS_STMT

    @staticmethod
    def acquire_lock_stmt() -> TextClause:
        """
        Get statement to atomically acquire the migration lock.

        Returns:
            TextClause: SQLAlchemy text clause with :process_id parameter.
        """
        return default_queries.ACQUIRE_LOCK_STMT

    @staticmethod
    def release_lock_stmt() -> TextClause:
        """
        Get statement to release the migration lock for a specific process.

        Returns:
            TextClause: SQLAlchemy text clause with :process_id parameter.
        """
        return default_queries.RELEASE_LOCK_STMT

    @staticmethod
    def force_unlock_stmt() -> TextClause:
        """
        Get statement to force release the migration lock unconditionally.

        Returns:
            TextClause: SQLAlchemy text clause for the UPDATE statement.
        """
        return default_queries.FORCE_UNLOCK_STMT

    @staticmethod
    def get_version_checksums_query() -> TextClause:
        """
        Get query to fetch version and checksum pairs for all migrations.

        Returns:
            TextClause: SQLAlchemy text clause that returns version
                and checksum columns.
        """
        return default_queries.GET_VERSION_CHECKSUMS_QUERY

    @staticmethod
    def repair_migration_checksum_stmt() -> TextClause:
        """
        Get statement to update the checksum for a specific version.

        Returns:
            TextClause: SQLAlchemy text clause with :version and
                :checksum parameters.
        """
        return default_queries.REPAIR_MIGRATION_CHECKSUM_STMT

    @staticmethod
    def get_runs_on_change_migrations_query() -> TextClause:
        """
        Get query to fetch all runs-on-change migration records.

        Returns:
            TextClause: SQLAlchemy text clause that returns filename
                and checksum columns.
        """
        return default_queries.GET_RUNS_ON_CHANGE_MIGRATIONS_QUERY

    @staticmethod
    def get_repeatable_always_migrations_query() -> TextClause:
        """
        Get query to fetch all runs-always migration records.

        Returns:
            TextClause: SQLAlchemy text clause that returns filename column.
        """
        return default_queries.GET_RUNS_ALWAYS_MIGRATIONS_QUERY

    @staticmethod
    def get_repeatable_migrations_query() -> TextClause:
        """
        Get query to fetch all repeatable migration records.

        Returns:
            TextClause: SQLAlchemy text clause for the SELECT query.
        """
        return default_queries.GET_REPEATABLE_MIGRATIONS_QUERY

    @staticmethod
    def update_repeatable_migration_stmt() -> TextClause:
        """
        Get statement to update a repeatable migration's checksum and timestamp.

        Returns:
            TextClause: SQLAlchemy text clause with :checksum, :filename,
                and :migration_type parameters.
        """
        return default_queries.UPDATE_REPEATABLE_MIGRATION_STMT

    @staticmethod
    def delete_missing_version_stmt() -> TextClause:
        """
        Get statement to delete a versioned migration record.

        Returns:
            TextClause: SQLAlchemy text clause with :version parameter.
        """
        return default_queries.DELETE_MISSING_VERSION_STMT

    @staticmethod
    def delete_missing_repeatable_stmt() -> TextClause:
        """
        Get statement to delete a repeatable migration record by filename.

        Returns:
            TextClause: SQLAlchemy text clause with :filename parameter.
        """
        return default_queries.DELETE_MISSING_REPEATABLE_STMT


def detect_db(sqlalchemy_url: str) -> DatabaseType:
    """
    Detect the database type from a SQLAlchemy connection URL.

    Parses the URL to determine the database backend and returns
    the corresponding DatabaseType enum value.

    Args:
        sqlalchemy_url (str): A SQLAlchemy database connection URL.

    Returns:
        DatabaseType: The detected database type (postgresql or sqlite).

    Raises:
        ValueError: If the database type is not supported by Jetbase.
    """
    url = make_url(sqlalchemy_url)
    backend_name = url.get_backend_name()

    try:
        database_type: DatabaseType = DatabaseType(backend_name)
    except ValueError:
        raise ValueError(
            f"Unsupported database: {backend_name}. "
            f"Supported databases are: {', '.join(db.value for db in DatabaseType)}"
        )

    return database_type


class QueryMethod(Enum):
    """Enum for all available query methods in BaseQueries"""

    LATEST_VERSION_QUERY = "latest_version_query"
    CREATE_MIGRATIONS_TABLE_STMT = "create_migrations_table_stmt"
    INSERT_VERSION_STMT = "insert_version_stmt"
    DELETE_VERSION_STMT = "delete_version_stmt"
    LATEST_VERSIONS_QUERY = "latest_versions_query"
    LATEST_VERSIONS_BY_STARTING_VERSION_QUERY = (
        "latest_versions_by_starting_version_query"
    )
    CHECK_IF_VERSION_EXISTS_QUERY = "check_if_version_exists_query"
    CHECK_IF_MIGRATIONS_TABLE_EXISTS_QUERY = "check_if_migrations_table_exists_query"
    CHECK_IF_LOCK_TABLE_EXISTS_QUERY = "check_if_lock_table_exists_query"
    MIGRATION_RECORDS_QUERY = "migration_records_query"
    CREATE_LOCK_TABLE_STMT = "create_lock_table_stmt"
    INITIALIZE_LOCK_RECORD_STMT = "initialize_lock_record_stmt"
    CHECK_LOCK_STATUS_STMT = "check_lock_status_stmt"
    ACQUIRE_LOCK_STMT = "acquire_lock_stmt"
    RELEASE_LOCK_STMT = "release_lock_stmt"
    FORCE_UNLOCK_STMT = "force_unlock_stmt"
    GET_VERSION_CHECKSUMS_QUERY = "get_version_checksums_query"
    REPAIR_MIGRATION_CHECKSUM_STMT = "repair_migration_checksum_stmt"
    GET_RUNS_ON_CHANGE_MIGRATIONS_QUERY = "get_runs_on_change_migrations_query"
    GET_RUNS_ALWAYS_MIGRATIONS_QUERY = "get_repeatable_always_migrations_query"
    GET_REPEATABLE_MIGRATIONS_QUERY = "get_repeatable_migrations_query"
    UPDATE_REPEATABLE_MIGRATION_STMT = "update_repeatable_migration_stmt"
    DELETE_MISSING_VERSION_STMT = "delete_missing_version_stmt"
    DELETE_MISSING_REPEATABLE_STMT = "delete_missing_repeatable_stmt"
