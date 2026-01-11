import os
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from jetbase.cli.main import app
from jetbase.constants import NEW_MIGRATION_FILE_CONTENT

runner = CliRunner()


def test_new_command_missing_description():
    """Test the 'new' command fails when description is not provided."""
    # Run command without description
    result = runner.invoke(app, ["new"])

    # Check command failed
    assert result.exit_code == 2
    assert "Missing argument 'DESCRIPTION'" in result.output


def test_new_command_success(tmp_path):
    """Test the 'new' command successfully creates a migration file."""
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    os.chdir("jetbase")

    with patch("jetbase.commands.new.dt") as mock_dt:
        mock_dt.datetime.now.return_value.strftime.return_value = "20251214.160000"

        # Run the command
        result = runner.invoke(app, ["new", "create users table"])

        # Check command succeeded
        assert result.exit_code == 0

        # Check file was created with correct name
        expected_filename = "V20251214.160000__create_users_table.sql"
        expected_filepath = Path("migrations") / expected_filename
        assert expected_filepath.exists()


def test_new_success_file_content(tmp_path):
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    os.chdir("jetbase")

    with patch("jetbase.commands.new.dt") as mock_dt:
        mock_dt.datetime.now.return_value.strftime.return_value = "20251214.160000"

        # Run the command
        result = runner.invoke(app, ["new", "create users table"])

        # Check command succeeded
        assert result.exit_code == 0

        expected_filename = "V20251214.160000__create_users_table.sql"
        expected_filepath = Path("migrations") / expected_filename
        assert expected_filepath.exists()

        with open(expected_filepath, "r") as f:
            content = f.read()
        assert content == NEW_MIGRATION_FILE_CONTENT


def test_new_command_with_custom_version(tmp_path):
    """Test the 'new' command successfully creates a migration file with a custom version."""
    os.chdir(tmp_path)
    result = runner.invoke(app, ["init"])
    os.chdir("jetbase")

    with patch("jetbase.commands.new.dt") as mock_dt:
        mock_dt.datetime.now.return_value.strftime.return_value = "20251214.160000"

        # Run the command
        result = runner.invoke(app, ["new", "create users table", "--version", "1.5"])

        # Check command succeeded
        assert result.exit_code == 0

        # Check file was created with correct name
        expected_filename = "V1.5__create_users_table.sql"
        expected_filepath = Path("migrations") / expected_filename
        assert expected_filepath.exists()
