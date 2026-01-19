from unittest.mock import Mock, patch

import pytest

from jetbase.database.queries.base import QueryMethod
from jetbase.database.queries.postgres import PostgresQueries
from jetbase.database.queries.query_loader import (
    get_database_type,
    get_queries,
    get_query,
)
from jetbase.database.queries.sqlite import SQLiteQueries
from jetbase.enums import DatabaseType


class TestGetDatabaseType:
    """Tests for the get_database_type function."""

    @patch("jetbase.database.queries.query_loader.create_engine")
    @patch("jetbase.database.queries.query_loader.get_config")
    def test_returns_postgresql(self, mock_config: Mock, mock_engine: Mock) -> None:
        """Test that PostgreSQL dialect is detected correctly."""
        mock_config.return_value.sqlalchemy_url = "postgresql://localhost/db"
        mock_engine.return_value.dialect.name = "postgresql"

        result = get_database_type()

        assert result == DatabaseType.POSTGRESQL

    @patch("jetbase.database.queries.query_loader.create_engine")
    @patch("jetbase.database.queries.query_loader.get_config")
    def test_returns_sqlite(self, mock_config: Mock, mock_engine: Mock) -> None:
        """Test that SQLite dialect is detected correctly."""
        mock_config.return_value.sqlalchemy_url = "sqlite:///db.sqlite"
        mock_engine.return_value.dialect.name = "sqlite"

        result = get_database_type()

        assert result == DatabaseType.SQLITE

    @patch("jetbase.database.queries.query_loader.create_engine")
    @patch("jetbase.database.queries.query_loader.get_config")
    def test_returns_snowflake(self, mock_config: Mock, mock_engine: Mock) -> None:
        """Test that Snowflake dialect is detected correctly."""
        mock_config.return_value.sqlalchemy_url = (
            "snowflake://user:pass@account/db/schema"
        )
        mock_engine.return_value.dialect.name = "snowflake"

        result = get_database_type()

        assert result == DatabaseType.SNOWFLAKE

    @patch("jetbase.database.queries.query_loader.create_engine")
    @patch("jetbase.database.queries.query_loader.get_config")
    def test_returns_mysql(self, mock_config: Mock, mock_engine: Mock) -> None:
        """Test that MySQL dialect is detected correctly."""
        mock_config.return_value.sqlalchemy_url = "mysql://user:pass@localhost/db"
        mock_engine.return_value.dialect.name = "mysql"

        result = get_database_type()
        assert result == DatabaseType.MYSQL

    @patch("jetbase.database.queries.query_loader.create_engine")
    @patch("jetbase.database.queries.query_loader.get_config")
    def test_raises_for_unsupported(self, mock_config: Mock, mock_engine: Mock) -> None:
        """Test that unsupported dialects raise ValueError."""
        mock_config.return_value.sqlalchemy_url = "baddb://localhost/db"
        mock_engine.return_value.dialect.name = "baddb"

        with pytest.raises(ValueError, match="Unsupported database type"):
            get_database_type()


class TestGetQueries:
    """Tests for the get_queries function."""

    @patch("jetbase.database.queries.query_loader.get_database_type")
    def test_returns_postgres_queries(self, mock_db_type: Mock) -> None:
        """Test that PostgresQueries is returned for PostgreSQL."""
        mock_db_type.return_value = DatabaseType.POSTGRESQL

        result = get_queries()

        assert result == PostgresQueries

    @patch("jetbase.database.queries.query_loader.get_database_type")
    def test_returns_sqlite_queries(self, mock_db_type: Mock) -> None:
        """Test that SQLiteQueries is returned for SQLite."""
        mock_db_type.return_value = DatabaseType.SQLITE

        result = get_queries()

        assert result == SQLiteQueries


class TestGetQuery:
    """Tests for the get_query function."""

    @patch("jetbase.database.queries.query_loader.get_queries")
    def test_calls_correct_query_method(self, mock_get_queries: Mock) -> None:
        """Test that get_query calls the correct method on the query class."""
        mock_queries = Mock()
        mock_get_queries.return_value = mock_queries

        get_query(QueryMethod.LATEST_VERSION_QUERY)

        mock_queries.latest_version_query.assert_called_once()

    @patch("jetbase.database.queries.query_loader.get_queries")
    def test_passes_kwargs_to_method(self, mock_get_queries: Mock) -> None:
        """Test that kwargs are passed to the query method."""
        mock_queries = Mock()
        mock_get_queries.return_value = mock_queries

        get_query(QueryMethod.MIGRATION_RECORDS_QUERY, ascending=False)

        mock_queries.migration_records_query.assert_called_once_with(ascending=False)
