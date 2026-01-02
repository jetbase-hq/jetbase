from pathlib import Path
from unittest.mock import patch

import pytest

from jetbase.commands.validators import validate_jetbase_directory
from jetbase.engine.validation import (
    validate_current_migration_files_match_checksums,
    validate_migrated_repeatable_versions_in_migration_files,
    validate_migrated_versions_in_current_migration_files,
    validate_no_new_migration_files_with_lower_version_than_latest_migration,
)
from jetbase.exceptions import (
    ChecksumMismatchError,
    DirectoryNotFoundError,
    OutOfOrderMigrationError,
)


class TestValidateJetbaseDirectory:
    def test_success(self, tmp_path: Path) -> None:
        """Test validation succeeds when in jetbase directory with migrations folder."""
        jetbase_dir = tmp_path / "jetbase"
        jetbase_dir.mkdir()
        (jetbase_dir / "migrations").mkdir()

        with patch("jetbase.commands.validators.Path.cwd", return_value=jetbase_dir):
            validate_jetbase_directory()

    def test_wrong_directory_name(self, tmp_path: Path) -> None:
        """Test validation fails when not in a directory named 'jetbase'."""
        wrong_dir = tmp_path / "wrong_name"
        wrong_dir.mkdir()
        (wrong_dir / "migrations").mkdir()

        with patch("jetbase.commands.validators.Path.cwd", return_value=wrong_dir):
            with pytest.raises(DirectoryNotFoundError):
                validate_jetbase_directory()


class TestValidateMigratedVersionsInCurrentMigrationFiles:
    def test_passes_when_all_files_exist(self) -> None:
        """Test validation passes when all migrated versions have files."""
        migrated_versions = ["1", "2"]
        filepaths = {"1": "/path/V1__test.sql", "2": "/path/V2__test.sql"}

        validate_migrated_versions_in_current_migration_files(
            migrated_versions, filepaths
        )

    def test_raises_when_file_missing(self) -> None:
        """Test validation fails when a migrated version is missing its file."""
        migrated_versions = ["1", "2"]
        filepaths = {"1": "/path/V1__test.sql"}

        with pytest.raises(FileNotFoundError):
            validate_migrated_versions_in_current_migration_files(
                migrated_versions, filepaths
            )


class TestValidateNoNewMigrationFilesWithLowerVersion:
    def test_passes_when_new_version_is_higher(self) -> None:
        """Test validation passes when new migrations have higher versions."""
        filepaths = {"1": "/path/V1__test.sql", "2": "/path/V2__test.sql"}
        migrated_versions = ["1"]
        latest_version = "1"

        validate_no_new_migration_files_with_lower_version_than_latest_migration(
            filepaths, migrated_versions, latest_version
        )

    def test_raises_when_new_version_is_lower(self) -> None:
        """Test validation fails when new migration has lower version."""
        filepaths = {"1": "/path/V1__test.sql", "3": "/path/V3__test.sql"}
        migrated_versions = ["3"]
        latest_version = "3"

        with pytest.raises(OutOfOrderMigrationError):
            validate_no_new_migration_files_with_lower_version_than_latest_migration(
                filepaths, migrated_versions, latest_version
            )


class TestValidateMigratedRepeatableVersionsInMigrationFiles:
    def test_passes_when_all_files_exist(self) -> None:
        """Test validation passes when all repeatable files exist."""
        migrated = ["RA__test.sql", "ROC__test.sql"]
        all_files = ["RA__test.sql", "ROC__test.sql", "RA__other.sql"]

        validate_migrated_repeatable_versions_in_migration_files(migrated, all_files)

    def test_raises_when_file_missing(self) -> None:
        """Test validation fails when a migrated repeatable file is missing."""
        migrated = ["RA__test.sql", "ROC__missing.sql"]
        all_files = ["RA__test.sql"]

        with pytest.raises(FileNotFoundError):
            validate_migrated_repeatable_versions_in_migration_files(
                migrated, all_files
            )


class TestValidateCurrentMigrationFilesMatchChecksums:
    @patch("jetbase.engine.validation.calculate_checksum", return_value="abc123")
    @patch("jetbase.engine.validation.parse_upgrade_statements", return_value=[])
    def test_passes_when_checksums_match(self, mock_parse, mock_checksum) -> None:
        """Test validation passes when all checksums match."""
        filepaths = {"1": "/path/V1__test.sql"}
        checksums = [("1", "abc123")]

        validate_current_migration_files_match_checksums(filepaths, checksums)

    @patch("jetbase.engine.validation.calculate_checksum", return_value="different")
    @patch("jetbase.engine.validation.parse_upgrade_statements", return_value=[])
    def test_raises_when_checksum_mismatch(self, mock_parse, mock_checksum) -> None:
        """Test validation fails when checksums don't match."""
        filepaths = {"1": "/path/V1__test.sql"}
        checksums = [("1", "abc123")]

        with pytest.raises(ChecksumMismatchError):
            validate_current_migration_files_match_checksums(filepaths, checksums)
