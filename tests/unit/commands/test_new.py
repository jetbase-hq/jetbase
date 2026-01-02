import tempfile
from unittest.mock import patch

import pytest

from jetbase.commands.new import generate_new_migration_file_cmd
from jetbase.constants import MIGRATIONS_DIR
from jetbase.exceptions import DirectoryNotFoundError


def test_generate_new_migration_file_cmd_success(tmp_path, capsys):
    """Test successful generation of a new migration file."""
    # Create migrations directory
    migrations_dir = tmp_path / MIGRATIONS_DIR
    migrations_dir.mkdir(parents=True)

    # Mock os.getcwd to return tmp_path
    with patch("os.getcwd", return_value=str(tmp_path)):
        # Mock datetime to get predictable timestamp
        with patch("jetbase.commands.new.dt") as mock_dt:
            mock_dt.datetime.now.return_value.strftime.return_value = "20251214.153000"

            # Generate migration file
            generate_new_migration_file_cmd("create users table")

            # Check file was created with correct name
            expected_filename = "V20251214.153000__create_users_table.sql"
            expected_filepath = migrations_dir / expected_filename
            assert expected_filepath.exists()
            assert expected_filepath.is_file()

            # Check console output
            captured = capsys.readouterr()
            assert f"Created migration file: {expected_filename}" in captured.out


def test_generate_new_migration_file_cmd_directory_not_found():
    """Test that DirectoryNotFoundError is raised when migrations directory doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock os.getcwd to return directory without migrations folder
        with patch("os.getcwd", return_value=tmpdir):
            with pytest.raises(DirectoryNotFoundError) as exc_info:
                generate_new_migration_file_cmd("create users table")

            # Check error message
            assert "Migrations directory not found" in str(exc_info.value)
            assert "jetbase initialize" in str(exc_info.value)
