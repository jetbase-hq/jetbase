from unittest.mock import Mock, patch

import pytest

from jetbase.commands.rollback import (
    _get_latest_migration_versions,
    _get_versions_to_rollback,
    _validate_rollback_files_exist,
)
from jetbase.exceptions import VersionNotFoundError


class TestGetLatestMigrationVersions:
    """Tests for the _get_latest_migration_versions function."""

    @patch("jetbase.commands.rollback.get_latest_versions")
    def test_with_count(self, mock_get_latest: Mock) -> None:
        """Test that count is passed as limit."""
        mock_get_latest.return_value = ["3", "2", "1"]

        result = _get_latest_migration_versions(count=3)

        assert result == ["3", "2", "1"]
        mock_get_latest.assert_called_once_with(limit=3)

    @patch("jetbase.commands.rollback.get_latest_versions")
    def test_with_to_version(self, mock_get_latest: Mock) -> None:
        """Test that to_version is passed as starting_version."""
        mock_get_latest.return_value = ["3", "2"]

        result = _get_latest_migration_versions(to_version="1")

        assert result == ["3", "2"]
        mock_get_latest.assert_called_once_with(starting_version="1")

    @patch("jetbase.commands.rollback.get_latest_versions")
    def test_defaults_to_one(self, mock_get_latest: Mock) -> None:
        """Test that it defaults to limit=1 when no args provided."""
        mock_get_latest.return_value = ["3"]

        result = _get_latest_migration_versions()

        assert result == ["3"]
        mock_get_latest.assert_called_once_with(limit=1)


class TestGetVersionsToRollback:
    """Tests for the _get_versions_to_rollback function."""

    @patch("jetbase.commands.rollback.get_migration_filepaths_by_version")
    def test_returns_reversed_dict(self, mock_get_filepaths: Mock) -> None:
        """Test that versions are returned in reverse order."""
        mock_get_filepaths.return_value = {
            "1": "/path/V1__test.sql",
            "2": "/path/V2__test.sql",
        }

        result = _get_versions_to_rollback(["1", "2"])

        assert list(result.keys()) == ["2", "1"]


class TestValidateRollbackFilesExist:
    """Tests for the _validate_rollback_files_exist function."""

    def test_passes_when_all_files_exist(self) -> None:
        """Test validation passes when all files exist."""
        versions = ["1", "2"]
        files = {"1": "/path/V1.sql", "2": "/path/V2.sql"}

        _validate_rollback_files_exist(versions, files)

    def test_raises_when_file_missing(self) -> None:
        """Test raises VersionNotFoundError when file is missing."""
        versions = ["1", "2"]
        files = {"1": "/path/V1.sql"}

        with pytest.raises(VersionNotFoundError):
            _validate_rollback_files_exist(versions, files)
