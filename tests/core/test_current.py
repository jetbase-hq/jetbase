import datetime as dt
from unittest.mock import Mock, patch

import pytest

from jetbase.commands.current import current_cmd
from jetbase.models import MigrationRecord


@pytest.mark.parametrize(
    "version, expected_output",
    [
        ("1.2.3", "Latest migration version: 1.2.3"),
        (None, "No migrations have been applied yet."),
    ],
)
@patch("jetbase.commands.current.fetch_latest_versioned_migration")
def test_current_cmd(
    mock_fetch_latest_versioned_migration: Mock,
    capsys: pytest.CaptureFixture,
    version: str | None,
    expected_output: str,
) -> None:
    """Test current_cmd with different version scenarios."""
    if version:
        mock_fetch_latest_versioned_migration.return_value = MigrationRecord(
            order_executed=1,
            version=version,
            description="test",
            filename="V1.2.3__test.sql",
            migration_type="VERSIONED",
            applied_at=dt.datetime.now(),
            checksum="abc123",
        )
    else:
        mock_fetch_latest_versioned_migration.return_value = None

    current_cmd()

    captured = capsys.readouterr()
    assert expected_output in captured.out
    mock_fetch_latest_versioned_migration.assert_called_once()
