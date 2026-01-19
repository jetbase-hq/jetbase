import pytest

from jetbase.database.queries.base import detect_db
from jetbase.enums import DatabaseType


class TestDetectDb:
    """Tests for the detect_db function."""

    def test_detects_postgresql(self) -> None:
        """Test that PostgreSQL URLs are detected correctly."""
        result = detect_db("postgresql://user:pass@localhost/db")
        assert result == DatabaseType.POSTGRESQL

    def test_detects_sqlite(self) -> None:
        """Test that SQLite URLs are detected correctly."""
        result = detect_db("sqlite:///path/to/db.sqlite")
        assert result == DatabaseType.SQLITE

    def test_detects_snowflake(self) -> None:
        """Test that Snowflake URLs are detected correctly."""
        result = detect_db("snowflake://user:pass@account/db/schema")
        assert result == DatabaseType.SNOWFLAKE

    def test_detects_mysql(self) -> None:
        """Test that MySQL URLs are detected correctly."""
        result = detect_db("mysql://user:pass@localhost/db")
        assert result == DatabaseType.MYSQL

    def test_raises_for_unsupported_database(self) -> None:
        """Test that unsupported databases raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported database"):
            detect_db("baddb://user:pass@localhost/db")
