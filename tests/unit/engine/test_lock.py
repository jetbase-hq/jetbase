from unittest.mock import Mock, patch

import pytest

from jetbase.engine.lock import acquire_lock, migration_lock


class TestAcquireLock:
    """Tests for the acquire_lock function."""

    @patch("jetbase.engine.lock.lock_database")
    def test_returns_process_id_on_success(self, mock_lock_database: Mock) -> None:
        """Test that acquire_lock returns a UUID process ID when lock is acquired."""
        mock_lock_database.return_value.rowcount = 1

        result = acquire_lock()

        assert result is not None
        mock_lock_database.assert_called_once()

    @patch("jetbase.engine.lock.lock_database")
    def test_raises_runtime_error_when_already_locked(
        self, mock_lock_database: Mock
    ) -> None:
        """Test that RuntimeError is raised when lock is already held."""
        mock_lock_database.return_value.rowcount = 0

        with pytest.raises(RuntimeError, match="Migration lock is already held"):
            acquire_lock()


class TestMigrationLock:
    """Tests for the migration_lock context manager."""

    @patch("jetbase.engine.lock.release_lock")
    @patch("jetbase.engine.lock.acquire_lock", return_value="test-id")
    def test_acquires_and_releases_lock(
        self, mock_acquire: Mock, mock_release: Mock
    ) -> None:
        """Test that lock is acquired on entry and released on exit."""
        with migration_lock():
            pass

        mock_acquire.assert_called_once()
        mock_release.assert_called_once()

    @patch("jetbase.engine.lock.release_lock")
    @patch("jetbase.engine.lock.acquire_lock", return_value="test-id")
    def test_releases_lock_on_exception(
        self, mock_acquire: Mock, mock_release: Mock
    ) -> None:
        """Test that lock is released even when an exception occurs."""
        with pytest.raises(ValueError):
            with migration_lock():
                raise ValueError("test error")

        mock_release.assert_called_once()
