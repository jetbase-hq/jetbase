import datetime as dt

import pytest

from jetbase.engine.formatters import format_applied_at, get_display_version


class TestGetDisplayVersion:
    """Tests for the get_display_version function."""

    def test_returns_version_when_provided(self) -> None:
        """Test that version is returned when explicitly provided."""
        result = get_display_version("versioned", "1.0.0")
        assert result == "1.0.0"

    def test_returns_runs_always_label(self) -> None:
        """Test that RUNS_ALWAYS is returned for runs_always migrations."""
        result = get_display_version("runs_always")
        assert result == "RUNS_ALWAYS"

    def test_returns_runs_on_change_label(self) -> None:
        """Test that RUNS_ON_CHANGE is returned for runs_on_change migrations."""
        result = get_display_version("runs_on_change")
        assert result == "RUNS_ON_CHANGE"

    def test_raises_value_error_for_invalid_type(self) -> None:
        """Test that ValueError is raised for invalid migration types without version."""
        with pytest.raises(ValueError):
            get_display_version("invalid")


class TestFormatAppliedAt:
    """Tests for the format_applied_at function."""

    def test_returns_empty_string_for_none(self) -> None:
        """Test that empty string is returned when applied_at is None."""
        result = format_applied_at(None)
        assert result == ""

    def test_formats_datetime_object(self) -> None:
        """Test formatting of datetime objects (PostgreSQL)."""
        timestamp = dt.datetime(2024, 6, 15, 14, 30, 45, 123456)
        result = format_applied_at(timestamp)
        assert result == "2024-06-15 14:30:45.12"

    def test_truncates_string_timestamp(self) -> None:
        """Test truncation of string timestamps (SQLite)."""
        timestamp_str = "2024-06-15 14:30:45.123456789"
        result = format_applied_at(timestamp_str)
        assert result == "2024-06-15 14:30:45.12"
