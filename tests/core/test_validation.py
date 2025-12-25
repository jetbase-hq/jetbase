from pathlib import Path
from unittest.mock import patch

import pytest

from jetbase.commands.helpers import validate_jetbase_directory
from jetbase.exceptions import DirectoryNotFoundError


class TestValidateJetbaseDirectory:
    def test_validate_jetbase_directory_success(self, tmp_path: Path) -> None:
        """Test validation succeeds when in jetbase directory with migrations folder."""
        jetbase_dir = tmp_path / "jetbase"
        jetbase_dir.mkdir()
        migrations_dir = jetbase_dir / "migrations"
        migrations_dir.mkdir()

        with patch("jetbase.core.validation.Path.cwd", return_value=jetbase_dir):
            validate_jetbase_directory()  # Should not raise

    def test_validate_jetbase_directory_wrong_directory_name(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails when not in a directory named 'jetbase'."""
        wrong_dir = tmp_path / "wrong_name"
        wrong_dir.mkdir()
        migrations_dir = wrong_dir / "migrations"
        migrations_dir.mkdir()

        with patch("jetbase.core.validation.Path.cwd", return_value=wrong_dir):
            with pytest.raises(DirectoryNotFoundError) as exc_info:
                validate_jetbase_directory()

    def test_validate_jetbase_directory_missing_migrations_folder(
        self, tmp_path: Path
    ) -> None:
        """Test validation fails when migrations directory doesn't exist."""
        jetbase_dir = tmp_path / "jetbase"
        jetbase_dir.mkdir()

        with patch("jetbase.core.validation.Path.cwd", return_value=jetbase_dir):
            with pytest.raises(DirectoryNotFoundError) as exc_info:
                validate_jetbase_directory()
