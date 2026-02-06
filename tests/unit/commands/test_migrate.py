from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from jetbase.cli.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


class TestMigrateCommand:
    """Tests for the migrate CLI command (alias to upgrade)."""

    def test_migrate_with_count_option(self, runner):
        """Test migrate with --count option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--count", "1"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["count"] == 1

    def test_migrate_with_to_version_option(self, runner):
        """Test migrate with --to-version option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--to-version", "1_5"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["to_version"] == "1.5"

    def test_migrate_with_dry_run_option(self, runner):
        """Test migrate with --dry-run option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--dry-run"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["dry_run"] is True

    def test_migrate_with_skip_validation(self, runner):
        """Test migrate with --skip-validation option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--skip-validation"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["skip_validation"] is True

    def test_migrate_with_skip_checksum_validation(self, runner):
        """Test migrate with --skip-checksum-validation option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--skip-checksum-validation"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["skip_checksum_validation"] is True

    def test_migrate_with_skip_file_validation(self, runner):
        """Test migrate with --skip-file-validation option."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["migrate", "--skip-file-validation"])

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["skip_file_validation"] is True

    def test_migrate_with_multiple_options(self, runner):
        """Test migrate with multiple options."""
        with patch("jetbase.cli.main.upgrade_cmd") as mock_upgrade:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(
                    app,
                    [
                        "migrate",
                        "--count",
                        "5",
                        "--dry-run",
                        "--skip-validation",
                    ],
                )

                mock_upgrade.assert_called_once()
                call_kwargs = mock_upgrade.call_args[1]
                assert call_kwargs["count"] == 5
                assert call_kwargs["dry_run"] is True
                assert call_kwargs["skip_validation"] is True


class TestMakeMigrationsCommand:
    """Tests for the make-migrations CLI command."""

    def test_make_migrations_command_exists(self, runner):
        """Test that make-migrations command is registered."""
        result = runner.invoke(app, ["make-migrations", "--help"])
        assert result.exit_code == 0
        assert "Automatically generate SQL migration files" in result.output

    def test_make_migrations_with_description(self, runner):
        """Test make-migrations with --description option."""
        with patch("jetbase.cli.main.make_migrations_cmd") as mock_make:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(
                    app, ["make-migrations", "--description", "create users"]
                )

                mock_make.assert_called_once_with(description="create users")

    def test_make_migrations_without_description(self, runner):
        """Test make-migrations without --description option."""
        with patch("jetbase.cli.main.make_migrations_cmd") as mock_make:
            with patch("jetbase.cli.main.validate_jetbase_directory"):
                result = runner.invoke(app, ["make-migrations"])

                mock_make.assert_called_once_with(description=None)
