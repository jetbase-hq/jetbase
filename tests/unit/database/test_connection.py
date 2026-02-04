"""Unit tests for database connection module."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import text

from jetbase.database.connection import (
    _get_engine,
    get_async_db_connection,
    get_connection,
    get_db_connection,
    is_async_enabled,
)


class TestIsAsyncEnabled:
    """Tests for the is_async_enabled function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Clear ASYNC env var before each test."""
        if "ASYNC" in os.environ:
            original = os.environ["ASYNC"]
            del os.environ["ASYNC"]
            yield
            os.environ["ASYNC"] = original
        else:
            yield
        _get_engine.cache_clear()

    def test_defaults_to_false(self):
        """Test that ASYNC defaults to False when not set."""
        assert is_async_enabled() is False

    def test_false_values(self):
        """Test that common false values return False."""
        false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", ""]
        for val in false_values:
            os.environ["ASYNC"] = val
            assert is_async_enabled() is False, f"Failed for value: {val}"

    def test_true_values(self):
        """Test that common true values return True."""
        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]
        for val in true_values:
            os.environ["ASYNC"] = val
            assert is_async_enabled() is True, f"Failed for value: {val}"


class TestSyncConnection:
    """Tests for sync database connection."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test database for sync tests."""
        _get_engine.cache_clear()
        db_file = tmp_path / "test_sync.db"
        url = f"sqlite:///{db_file}"
        os.environ["ASYNC"] = "false"
        os.environ["JETBASE_SQLALCHEMY_URL"] = url
        yield
        _get_engine.cache_clear()
        if "ASYNC" in os.environ:
            del os.environ["ASYNC"]
        if "JETBASE_SQLALCHEMY_URL" in os.environ:
            del os.environ["JETBASE_SQLALCHEMY_URL"]

    def test_get_db_connection_returns_connection(self):
        """Test that get_db_connection returns a working sync connection."""
        with get_db_connection() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)

    def test_get_db_connection_can_create_table(self):
        """Test that we can create and query a table with sync connection."""
        with get_db_connection() as connection:
            connection.execute(
                text("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            )
            connection.execute(text("INSERT INTO test_table (name) VALUES ('test')"))
            result = connection.execute(text("SELECT name FROM test_table"))
            assert result.fetchone() == ("test",)

    def test_get_db_connection_multiple_queries(self):
        """Test multiple queries in a single connection."""
        with get_db_connection() as connection:
            connection.execute(
                text("CREATE TABLE multi_test (id INTEGER PRIMARY KEY, value INTEGER)")
            )
            connection.execute(text("INSERT INTO multi_test (value) VALUES (10)"))
            connection.execute(text("INSERT INTO multi_test (value) VALUES (20)"))
            result = connection.execute(text("SELECT SUM(value) FROM multi_test"))
            assert result.fetchone() == (30,)

    def test_get_connection_sync_mode(self):
        """Test that get_connection works in sync mode."""
        with get_connection() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)


class TestAsyncConnection:
    """Tests for async database connection."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test database for async tests."""
        _get_engine.cache_clear()
        db_file = tmp_path / "test_async.db"
        url = f"sqlite+aiosqlite:///{db_file}"
        os.environ["ASYNC"] = "true"
        os.environ["JETBASE_SQLALCHEMY_URL"] = url
        yield
        _get_engine.cache_clear()
        if "ASYNC" in os.environ:
            del os.environ["ASYNC"]
        if "JETBASE_SQLALCHEMY_URL" in os.environ:
            del os.environ["JETBASE_SQLALCHEMY_URL"]

    @pytest.mark.asyncio
    async def test_get_async_db_connection_returns_connection(self):
        """Test that get_async_db_connection returns a working async connection."""
        async with get_async_db_connection() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)

    @pytest.mark.asyncio
    async def test_get_async_db_connection_can_create_table(self):
        """Test that we can create and query a table with async connection."""
        async with get_async_db_connection() as connection:
            await connection.execute(
                text("CREATE TABLE async_test (id INTEGER PRIMARY KEY, name TEXT)")
            )
            await connection.execute(
                text("INSERT INTO async_test (name) VALUES ('async')")
            )
            result = await connection.execute(text("SELECT name FROM async_test"))
            assert result.fetchone() == ("async",)

    @pytest.mark.asyncio
    async def test_get_async_db_connection_multiple_queries(self):
        """Test multiple queries in a single async connection."""
        async with get_async_db_connection() as connection:
            await connection.execute(
                text("CREATE TABLE async_multi (id INTEGER PRIMARY KEY, value INTEGER)")
            )
            await connection.execute(
                text("INSERT INTO async_multi (value) VALUES (100)")
            )
            await connection.execute(
                text("INSERT INTO async_multi (value) VALUES (200)")
            )
            result = await connection.execute(
                text("SELECT SUM(value) FROM async_multi")
            )
            assert result.fetchone() == (300,)

    @pytest.mark.asyncio
    async def test_get_connection_async_mode(self):
        """Test that get_connection works in async mode."""
        async with get_connection() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)


class TestConnectionWrapper:
    """Tests for the get_connection wrapper that handles both modes."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test database for wrapper tests."""
        _get_engine.cache_clear()
        self.sync_db = tmp_path / "wrapper_sync.db"
        self.async_db = tmp_path / "wrapper_async.db"
        yield
        _get_engine.cache_clear()
        if "ASYNC" in os.environ:
            del os.environ["ASYNC"]
        if "JETBASE_SQLALCHEMY_URL" in os.environ:
            del os.environ["JETBASE_SQLALCHEMY_URL"]

    def test_wrapper_sync_mode(self):
        """Test get_connection in sync mode."""
        os.environ["ASYNC"] = "false"
        os.environ["JETBASE_SQLALCHEMY_URL"] = f"sqlite:///{self.sync_db}"

        with get_connection() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)

    @pytest.mark.asyncio
    async def test_wrapper_async_mode(self):
        """Test get_connection in async mode."""
        os.environ["ASYNC"] = "true"
        os.environ["JETBASE_SQLALCHEMY_URL"] = f"sqlite+aiosqlite:///{self.async_db}"

        async with get_connection() as connection:
            result = await connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)

    def test_wrapper_works_with_sync_syntax_even_when_async_true(self):
        """Test that using 'with' works even when ASYNC=true by stripping async suffix."""
        os.environ["ASYNC"] = "true"
        os.environ["JETBASE_SQLALCHEMY_URL"] = f"sqlite+aiosqlite:///{self.async_db}"

        with get_connection() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone() == (1,)
