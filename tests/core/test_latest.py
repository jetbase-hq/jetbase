from unittest.mock import Mock, patch

import pytest

from jetbase.core.latest import latest_cmd


@pytest.mark.parametrize(
    "version, expected_output",
    [
        ("1.2.3", "Latest migration version: 1.2.3"),
        (None, "No migrations have been applied yet."),
    ],
)
@patch("jetbase.core.latest.get_last_updated_version")
def test_latest_cmd(
    mock_get_last_updated_version: Mock,
    capsys: pytest.CaptureFixture,
    version: str | None,
    expected_output: str,
) -> None:
    """Test latest_cmd with different version scenarios."""
    mock_get_last_updated_version.return_value = version

    latest_cmd()

    captured = capsys.readouterr()
    assert expected_output in captured.out
    mock_get_last_updated_version.assert_called_once()
