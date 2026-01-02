from pathlib import Path
from unittest.mock import patch

from jetbase.engine.repeatable import (
    get_ra_filenames,
    get_repeatable_always_filepaths,
    get_repeatable_filenames,
    get_runs_on_change_filepaths,
)


class TestGetRepeatableAlwaysFilepaths:
    """Tests for the get_repeatable_always_filepaths function."""

    def test_returns_ra_files(self, tmp_path: Path) -> None:
        """Test that RA__ files are returned."""
        (tmp_path / "RA__test.sql").touch()
        (tmp_path / "V1__other.sql").touch()

        result = get_repeatable_always_filepaths(str(tmp_path))

        assert len(result) == 1
        assert "RA__test.sql" in result[0]
        assert "V1__other.sql" not in result

    def test_returns_empty_when_no_ra_files(self, tmp_path: Path) -> None:
        """Test that empty list is returned when no RA__ files exist."""
        (tmp_path / "V1__test.sql").touch()

        result = get_repeatable_always_filepaths(str(tmp_path))

        assert result == []


class TestGetRunsOnChangeFilepaths:
    """Tests for the get_runs_on_change_filepaths function."""

    def test_returns_roc_files(self, tmp_path: Path) -> None:
        """Test that ROC__ files are returned."""
        (tmp_path / "ROC__test.sql").touch()
        (tmp_path / "V1__other.sql").touch()

        result = get_runs_on_change_filepaths(str(tmp_path))

        assert len(result) == 1
        assert "ROC__test.sql" in result[0]
        assert "V1__other.sql" not in result

    @patch("jetbase.engine.repeatable.validate_filename_format")
    def test_returns_empty_when_no_roc_files(
        self, mock_validate, tmp_path: Path
    ) -> None:
        """Test that empty list is returned when no ROC__ files exist."""
        (tmp_path / "V1__test.sql").touch()

        result = get_runs_on_change_filepaths(str(tmp_path))

        assert result == []


class TestGetRaFilenames:
    """Tests for the get_ra_filenames function."""

    def test_returns_ra_filenames(self, tmp_path: Path) -> None:
        """Test that RA__ filenames are returned."""
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "RA__test.sql").touch()
        (migrations_dir / "V1__other.sql").touch()

        with patch("jetbase.engine.repeatable.os.getcwd", return_value=str(tmp_path)):
            result = get_ra_filenames()

        assert result == ["RA__test.sql"]


class TestGetRepeatableFilenames:
    """Tests for the get_repeatable_filenames function."""

    def test_returns_all_repeatable_filenames(self, tmp_path: Path) -> None:
        """Test that both RA__ and ROC__ filenames are returned."""
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "RA__test.sql").touch()
        (migrations_dir / "ROC__test.sql").touch()
        (migrations_dir / "V1__other.sql").touch()

        with patch("jetbase.engine.repeatable.os.getcwd", return_value=str(tmp_path)):
            result = get_repeatable_filenames()

        assert len(result) == 2
        assert "RA__test.sql" in result
        assert "ROC__test.sql" in result
        assert "V1__other.sql" not in result
