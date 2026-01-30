"""Integration tests for Snowflake database connections."""

import os

import pytest
from sqlalchemy import text

from jetbase.database.connection import _get_engine, get_db_connection


class TestSnowflakePasswordAuth:
    """Tests for Snowflake username/password authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment for password auth."""
        _get_engine.cache_clear()
        url = os.environ.get("TEST_SF_USER_PASS_URL")
        assert url is not None

        os.environ["JETBASE_SQLALCHEMY_URL"] = url
        yield

        _get_engine.cache_clear()

    def test_get_db_connection_with_password_auth(self):
        """Test that get_db_connection works with Snowflake password authentication."""
        with get_db_connection() as connection:
            result = connection.execute(text("SELECT CURRENT_USER()"))
            user = result.scalar()

            assert user is not None
            assert isinstance(user, str)

    def test_can_execute_queries_with_password_auth(self):
        """Test that we can execute queries on the Snowflake connection."""
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
            )
            row = result.fetchone()

            assert row is not None
            assert row[0] is not None  # Database
            assert row[1] is not None  # Schema


class TestSnowflakeKeyPairAuth:
    """Tests for Snowflake key pair authentication."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment for key pair auth."""
        _get_engine.cache_clear()
        url = os.environ.get("TEST_SF_KEY_AUTH_URL")
        private_key = os.environ.get("JETBASE_SNOWFLAKE_PRIVATE_KEY")

        assert url is not None
        assert private_key is not None

        os.environ["JETBASE_SQLALCHEMY_URL"] = url
        yield

        _get_engine.cache_clear()

    def test_get_db_connection_with_keypair_auth(self):
        """Test that get_db_connection works with Snowflake key pair authentication."""
        with get_db_connection() as connection:
            result = connection.execute(text("SELECT CURRENT_USER()"))
            user = result.scalar()

            assert user is not None
            assert isinstance(user, str)

    def test_can_execute_queries_with_keypair_auth(self):
        """Test that we can execute queries on the Snowflake connection."""
        with get_db_connection() as connection:
            result = connection.execute(
                text("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
            )
            row = result.fetchone()

            assert row is not None
            assert row[0] is not None  # Database
            assert row[1] is not None  # Schema


class TestSnowflakeEncryptedKeyPairAuth:
    """Tests for Snowflake key pair authentication with encrypted private key."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment for encrypted key pair auth."""
        _get_engine.cache_clear()
        url = os.environ.get("TEST_SF_KEY_AUTH_URL")
        private_key = os.environ.get("TEST_SF_ENCRYPTED_PRIVATE_KEY")

        assert url is not None
        assert private_key is not None

        os.environ["JETBASE_SQLALCHEMY_URL"] = url
        os.environ["JETBASE_SNOWFLAKE_PRIVATE_KEY"] = private_key

        # Clear password before each test
        if "JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD" in os.environ:
            del os.environ["JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD"]

        yield

        _get_engine.cache_clear()

    def test_get_db_connection_with_encrypted_keypair_auth(self):
        """Test that get_db_connection works with encrypted private key."""
        password = os.environ.get("TEST_SF_PRIVATE_KEY_PASSWORD")
        assert password is not None

        os.environ["JETBASE_SNOWFLAKE_PRIVATE_KEY_PASSWORD"] = password

        with get_db_connection() as connection:
            result = connection.execute(text("SELECT CURRENT_USER()"))
            user = result.scalar()

            assert user is not None
            assert isinstance(user, str)

    def test_connection_fails_without_password_for_encrypted_key(self):
        """Test that connection fails with TypeError when password not provided for encrypted key."""
        with pytest.raises(TypeError):
            with get_db_connection() as connection:
                connection.execute(text("SELECT 1"))
