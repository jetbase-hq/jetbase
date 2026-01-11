import tempfile
from unittest.mock import patch

import pytest

from jetbase.commands.new import generate_new_migration_file_cmd, _generate_new_filename
from jetbase.constants import MIGRATIONS_DIR
from jetbase.exceptions import (
    DirectoryNotFoundError,
    InvalidVersionError,
    MigrationFilenameTooLongError,
)


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


def test_generate_new_migration_file_cmd_with_custom_version(tmp_path, capsys):
    """Test successful generation of a migration file with a custom version."""
    # Create migrations directory
    migrations_dir = tmp_path / MIGRATIONS_DIR
    migrations_dir.mkdir(parents=True)

    # Mock os.getcwd to return tmp_path
    with patch("os.getcwd", return_value=str(tmp_path)):
        # Generate migration file with custom version
        generate_new_migration_file_cmd("create users table", version="1.5")

        # Check file was created with correct name using the custom version
        expected_filename = "V1.5__create_users_table.sql"
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


def test_generate_new_filename_with_timestamp():
    """Test filename generation with default timestamp-based version."""
    with patch("jetbase.commands.new.dt") as mock_dt:
        mock_dt.datetime.now.return_value.strftime.return_value = "20260110.120000"

        result = _generate_new_filename("add users")

        assert result == "V20260110.120000__add_users.sql"


def test_generate_new_filename_with_custom_version():
    """Test filename generation with a custom version."""
    result = _generate_new_filename("add users", version="1")
    assert result == "V1__add_users.sql"


def test_generate_new_filename_with_dotted_version():
    """Test filename generation with a dotted version number."""
    result = _generate_new_filename("create orders table", version="2.5")
    assert result == "V2.5__create_orders_table.sql"


def test_generate_new_filename_with_underscore_version():
    """Test filename generation with an underscore-separated version."""
    result = _generate_new_filename("drop temp table", version="3_1")
    assert result == "V3_1__drop_temp_table.sql"


def test_generate_new_filename_invalid_version_raises_error():
    """Test that invalid version raises InvalidVersionError."""
    with pytest.raises(InvalidVersionError) as exc_info:
        _generate_new_filename("add users", version="invalid")

    assert "Invalid version" in str(exc_info.value)
    assert "invalid" in str(exc_info.value)


def test_generate_new_filename_too_long_raises_error():
    """Test that filename exceeding 512 characters raises MigrationFilenameTooLongError."""
    # Create a description that will make the filename exceed 512 characters
    long_description = "a" * 510

    with pytest.raises(MigrationFilenameTooLongError) as exc_info:
        _generate_new_filename(long_description, version="1")

    assert "Migration filename too long" in str(exc_info.value)
