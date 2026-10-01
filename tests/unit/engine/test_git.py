import subprocess
from unittest.mock import Mock, patch

from jetbase.engine.git import (
    get_current_commit_hash,
    get_repo_root,
    read_file_at_commit,
)


class TestGetCurrentCommitHash:
    """Tests for the get_current_commit_hash function."""

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_hash(self, mock_run: Mock) -> None:
        """Test the stripped HEAD hash is returned on success."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        assert get_current_commit_hash() == "abc123"

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_none_when_not_a_repo(self, mock_run: Mock) -> None:
        """Test None is returned when git exits non-zero (not a repo)."""
        mock_run.side_effect = subprocess.CalledProcessError(128, ["git"])

        assert get_current_commit_hash() is None

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_none_when_git_missing(self, mock_run: Mock) -> None:
        """Test None is returned when the git executable is unavailable."""
        mock_run.side_effect = FileNotFoundError()

        assert get_current_commit_hash() is None


class TestGetRepoRoot:
    """Tests for the get_repo_root function."""

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_root(self, mock_run: Mock) -> None:
        """Test the repository root path is returned on success."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/repo/root\n", stderr=""
        )

        assert get_repo_root() == "/repo/root"

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_none_outside_repo(self, mock_run: Mock) -> None:
        """Test None is returned when outside a git repository."""
        mock_run.side_effect = subprocess.CalledProcessError(128, ["git"])

        assert get_repo_root() is None


class TestReadFileAtCommit:
    """Tests for the read_file_at_commit function."""

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_content(self, mock_run: Mock) -> None:
        """Test file content at a commit is returned."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="-- upgrade\nSELECT 1;\n", stderr=""
        )

        content = read_file_at_commit("abc123", "jetbase/migrations/V1__a.sql")

        assert content == "-- upgrade\nSELECT 1;"
        called_args = mock_run.call_args.args[0]
        assert called_args == [
            "git",
            "show",
            "abc123:jetbase/migrations/V1__a.sql",
        ]

    @patch("jetbase.engine.git.subprocess.run")
    def test_returns_none_when_file_absent(self, mock_run: Mock) -> None:
        """Test None is returned when the file is absent at that commit."""
        mock_run.side_effect = subprocess.CalledProcessError(128, ["git"])

        assert read_file_at_commit("abc123", "missing.sql") is None
