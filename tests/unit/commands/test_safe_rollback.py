from contextlib import contextmanager
from unittest.mock import Mock, patch

from jetbase.commands.safe_rollback import attempt_safe_rollback
from jetbase.enums import MigrationDirectionType
from jetbase.models import AppliedVersionedMigration


@contextmanager
def _noop_lock():
    yield


def _applied(*specs: tuple[str, str, str | None]) -> list[AppliedVersionedMigration]:
    """Build a newest-first list of applied versioned migrations."""
    return [
        AppliedVersionedMigration(version=v, filename=f, git_commit_hash=h)
        for v, f, h in specs
    ]


class TestAttemptSafeRollback:
    """Tests for attempt_safe_rollback."""

    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_returns_false_when_no_applied_migrations(self, mock_applied: Mock) -> None:
        """Nothing applied -> nothing to roll back."""
        mock_applied.return_value = []

        assert attempt_safe_rollback() is False

    @patch("jetbase.commands.safe_rollback.get_repo_root", return_value="/repo")
    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_returns_false_when_latest_hash_missing(
        self, mock_applied: Mock, _mock_root: Mock
    ) -> None:
        """Requirement 4: NULL hash on the latest applied migration -> fall back."""
        mock_applied.return_value = _applied(
            ("2", "V2__b.sql", None), ("1", "V1__a.sql", "abc")
        )

        assert attempt_safe_rollback() is False

    @patch("jetbase.commands.safe_rollback.get_repo_root", return_value=None)
    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_returns_false_when_not_in_git_repo(
        self, mock_applied: Mock, _mock_root: Mock
    ) -> None:
        """Requirement 4: outside a git repo -> fall back."""
        mock_applied.return_value = _applied(("1", "V1__a.sql", "abc"))

        assert attempt_safe_rollback() is False

    @patch("jetbase.commands.safe_rollback.get_migration_filepaths_by_version")
    @patch("jetbase.commands.safe_rollback.get_repo_root", return_value="/repo")
    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_returns_false_when_all_files_present(
        self, mock_applied: Mock, _mock_root: Mock, mock_files: Mock
    ) -> None:
        """No missing trailing files -> nothing to roll back."""
        mock_applied.return_value = _applied(
            ("2", "V2__b.sql", "abc"), ("1", "V1__a.sql", "abc")
        )
        mock_files.return_value = {"1": "/p/V1__a.sql", "2": "/p/V2__b.sql"}

        assert attempt_safe_rollback() is False

    @patch("jetbase.commands.safe_rollback.run_migration")
    @patch("jetbase.commands.safe_rollback._get_rollback_statements")
    @patch("jetbase.commands.safe_rollback.migration_lock", _noop_lock)
    @patch("jetbase.commands.safe_rollback.get_migration_filepaths_by_version")
    @patch("jetbase.commands.safe_rollback.get_repo_root", return_value="/repo")
    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_rolls_back_trailing_missing_to_baseline(
        self,
        mock_applied: Mock,
        _mock_root: Mock,
        mock_files: Mock,
        mock_stmts: Mock,
        mock_run: Mock,
    ) -> None:
        """V3, V2 missing while V1 exists -> roll back V3 then V2, keep V1."""
        mock_applied.return_value = _applied(
            ("3", "V3__c.sql", "head"),
            ("2", "V2__b.sql", "head"),
            ("1", "V1__a.sql", "head"),
        )
        mock_files.return_value = {"1": "/p/V1__a.sql"}
        mock_stmts.return_value = ["DROP TABLE x"]

        assert attempt_safe_rollback() is True

        rolled_back_versions = [
            call.kwargs["version"] for call in mock_run.call_args_list
        ]
        assert rolled_back_versions == ["3", "2"]
        assert all(
            call.kwargs["migration_operation"] == MigrationDirectionType.ROLLBACK
            for call in mock_run.call_args_list
        )

    @patch("jetbase.commands.safe_rollback.run_migration")
    @patch("jetbase.commands.safe_rollback._get_rollback_statements", return_value=None)
    @patch("jetbase.commands.safe_rollback.migration_lock", _noop_lock)
    @patch("jetbase.commands.safe_rollback.get_migration_filepaths_by_version")
    @patch("jetbase.commands.safe_rollback.get_repo_root", return_value="/repo")
    @patch("jetbase.commands.safe_rollback.get_versioned_migrations_desc")
    def test_returns_false_when_recovery_fails(
        self,
        mock_applied: Mock,
        _mock_root: Mock,
        mock_files: Mock,
        _mock_stmts: Mock,
        mock_run: Mock,
    ) -> None:
        """If a missing file cannot be recovered from git, abort safely."""
        mock_applied.return_value = _applied(
            ("2", "V2__b.sql", "head"), ("1", "V1__a.sql", "head")
        )
        mock_files.return_value = {"1": "/p/V1__a.sql"}

        assert attempt_safe_rollback() is False
        mock_run.assert_not_called()
