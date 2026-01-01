import os
import tempfile
from typing import Generator
from unittest.mock import patch

import pytest

from jetbase.engine.dry_run import process_dry_run
from jetbase.enums import MigrationDirectionType


class TestProcessDryRunStatementCount:
    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_num_sql_statements_zero(self, capsys, temp_dir: str) -> None:
        """Test that num_sql_statements is 0 when no statements are returned."""
        file_path = os.path.join(temp_dir, "V1__empty.sql")
        version_to_filepath = {"1": file_path}

        with patch("jetbase.engine.dry_run.parse_upgrade_statements") as mock_parse:
            mock_parse.return_value = []

            migration_operation: MigrationDirectionType = MigrationDirectionType.UPGRADE

            process_dry_run(version_to_filepath, migration_operation)

            captured = capsys.readouterr()
            assert "(0 statements)" in captured.out

    def test_num_sql_statements_one(self, capsys, temp_dir: str) -> None:
        """Test that num_sql_statements is 1 when one statement is returned."""
        file_path = os.path.join(temp_dir, "V1__single.sql")
        version_to_filepath = {"1": file_path}

        with patch("jetbase.engine.dry_run.parse_upgrade_statements") as mock_parse:
            mock_parse.return_value = ["CREATE TABLE users (id INT PRIMARY KEY)"]

            process_dry_run(
                version_to_filepath=version_to_filepath,
                migration_operation=MigrationDirectionType.UPGRADE,
            )

            captured = capsys.readouterr()
            assert "(1 statement)" in captured.out

    def test_num_sql_statements_multiple(self, capsys, temp_dir: str) -> None:
        """Test that num_sql_statements correctly counts multiple statements."""
        file_path = os.path.join(temp_dir, "V1__multiple.sql")
        version_to_filepath = {"1": file_path}

        statements = [
            "CREATE TABLE users (id INT PRIMARY KEY)",
            "CREATE TABLE posts (id INT PRIMARY KEY)",
            "INSERT INTO users VALUES (1)",
            "INSERT INTO posts VALUES (1)",
        ]

        with patch("jetbase.engine.dry_run.parse_upgrade_statements") as mock_parse:
            mock_parse.return_value = statements

            process_dry_run(version_to_filepath, MigrationDirectionType.UPGRADE)

            captured = capsys.readouterr()
            assert "(4 statements)" in captured.out

    def test_num_sql_statements_rollback_operation(self, capsys, temp_dir: str) -> None:
        """Test that num_sql_statements is correct for rollback operations."""
        file_path = os.path.join(temp_dir, "V1__rollback.sql")
        version_to_filepath = {"1": file_path}

        rollback_statements = ["DROP TABLE posts", "DROP TABLE users"]

        with patch("jetbase.engine.dry_run.parse_rollback_statements") as mock_parse:
            mock_parse.return_value = rollback_statements

            process_dry_run(version_to_filepath, MigrationDirectionType.ROLLBACK)

            captured = capsys.readouterr()
            assert "(2 statements)" in captured.out

    def test_num_sql_statements_multiple_files_different_counts(
        self, capsys, temp_dir: str
    ) -> None:
        """Test that num_sql_statements is correct for each file when processing multiple files."""
        file_path1 = os.path.join(temp_dir, "V1__one_statement.sql")
        file_path2 = os.path.join(temp_dir, "V2__three_statements.sql")
        file_path3 = os.path.join(temp_dir, "V3__no_statements.sql")

        version_to_filepath = {"1": file_path1, "2": file_path2, "3": file_path3}

        def mock_parse_side_effect(file_path, dry_run):
            if file_path == file_path1:
                return ["CREATE TABLE users (id INT)"]
            elif file_path == file_path2:
                return [
                    "CREATE TABLE posts (id INT)",
                    "CREATE TABLE comments (id INT)",
                    "CREATE INDEX idx_posts ON posts(id)",
                ]
            elif file_path == file_path3:
                return []
            return []

        with patch("jetbase.engine.dry_run.parse_upgrade_statements") as mock_parse:
            mock_parse.side_effect = mock_parse_side_effect

            process_dry_run(version_to_filepath, MigrationDirectionType.UPGRADE)

            captured = capsys.readouterr()
            assert "(1 statement)" in captured.out  # V1 file
            assert "(3 statements)" in captured.out  # V2 file
            assert "(0 statements)" in captured.out  # V3 file

    def test_num_sql_statements_large_count(self, capsys, temp_dir: str) -> None:
        """Test that num_sql_statements handles larger numbers correctly."""
        file_path = os.path.join(temp_dir, "V1__many_statements.sql")
        version_to_filepath = {"1": file_path}

        # Create a list with 15 statements
        statements = [f"INSERT INTO test VALUES ({i})" for i in range(15)]

        with patch("jetbase.engine.dry_run.parse_upgrade_statements") as mock_parse:
            mock_parse.return_value = statements

            process_dry_run(version_to_filepath, MigrationDirectionType.UPGRADE)

            captured = capsys.readouterr()
            assert "(15 statements)" in captured.out
