import tempfile
from pathlib import Path
from typing import Generator

import pytest

from jetbase.core.file_parser import parse_rollback_statements, parse_upgrade_statements


class TestParseUpgradeStatements:
    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_parse_upgrade_statements_single_statement(self, temp_dir: str) -> None:
        """Test parsing a file with a single upgrade statement."""
        sql_content = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"

    def test_parse_upgrade_statements_multiple_statements(self, temp_dir: str) -> None:
        """Test parsing a file with multiple upgrade statements."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        INSERT INTO users (id, name) VALUES (2, 'Bob');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 3
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        assert result[2] == "INSERT INTO users (id, name) VALUES (2, 'Bob')"

    def test_parse_upgrade_statements_multi_line(self, temp_dir: str) -> None:
        """Test parsing multi-line SQL statements."""
        sql_content = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255)
        );
        
        INSERT INTO users 
            (id, name, email) 
        VALUES 
            (1, 'Alice', 'alice@example.com');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 2
        assert (
            result[0]
            == "CREATE TABLE users ( id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(255) )"
        )
        assert (
            result[1]
            == "INSERT INTO users (id, name, email) VALUES (1, 'Alice', 'alice@example.com')"
        )

    def test_parse_upgrade_statements_with_comments(self, temp_dir: str) -> None:
        """Test parsing upgrade statements with comments."""
        sql_content = """
        -- Create users table
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- Insert test data
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        -- Another comment
        INSERT INTO users (id, name) VALUES (2, 'Bob');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 3
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        assert result[2] == "INSERT INTO users (id, name) VALUES (2, 'Bob')"

    def test_parse_upgrade_statements_stops_at_rollback(self, temp_dir: str) -> None:
        """Test that parsing stops when encountering rollback marker."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        -- rollback
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"

    def test_parse_upgrade_statements_with_rollback_statements(
        self, temp_dir: str
    ) -> None:
        """Test that upgrade parsing ignores statements under rollback marker."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        -- rollback
        DELETE FROM users WHERE id = 1;
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        # Rollback statements should not be included

    def test_parse_upgrade_statements_rollback_case_insensitive(
        self, temp_dir: str
    ) -> None:
        """Test that rollback marker is case insensitive."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- ROLLBACK
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"

    def test_parse_upgrade_statements_rollback_with_spaces(self, temp_dir: str) -> None:
        """Test rollback marker with extra spaces."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        --   rollback   
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"

    def test_parse_upgrade_statements_empty_file(self, temp_dir: str) -> None:
        """Test parsing an empty file."""
        sql_file = Path(temp_dir) / "empty.sql"
        sql_file.write_text("")
        result = parse_upgrade_statements(str(sql_file))

        assert result == []

    def test_parse_upgrade_statements_only_comments(self, temp_dir: str) -> None:
        """Test parsing a file with only comments."""
        sql_content = """
        -- This is a comment
        -- Another comment
        -- Yet another comment
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert result == []

    def test_parse_upgrade_statements_no_semicolon(self, temp_dir: str) -> None:
        """Test parsing statements without semicolons (should be ignored)."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 1
        assert (
            result[0]
            == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100)) INSERT INTO users (id, name) VALUES (1, 'Alice')"
        )

    def test_parse_upgrade_statements_mixed_empty_lines(self, temp_dir: str) -> None:
        """Test parsing with mixed empty lines and statements."""
        sql_content = """
        
        
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"

    def test_parse_upgrade_statements_only_rollback_marker(self, temp_dir: str) -> None:
        """Test parsing a file with only rollback marker."""
        sql_content = "-- rollback"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert result == []


class TestParseRollbackStatements:
    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_parse_rollback_statements_basic(self, temp_dir: str) -> None:
        """Test parsing basic rollback statements."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        -- rollback
        DELETE FROM users WHERE id = 1;
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "DELETE FROM users WHERE id = 1"
        assert result[1] == "DROP TABLE users"

    def test_parse_rollback_statements_multi_line(self, temp_dir: str) -> None:
        """Test parsing multi-line rollback statements."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- rollback
        DELETE FROM users 
            WHERE id = 1;
        DROP TABLE IF EXISTS 
            users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "DELETE FROM users WHERE id = 1"
        assert result[1] == "DROP TABLE IF EXISTS users"

    def test_parse_rollback_statements_with_comments(self, temp_dir: str) -> None:
        """Test parsing rollback statements with comments."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- rollback
        -- First, delete the data
        DELETE FROM users WHERE id = 1;
        -- Then drop the table
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "DELETE FROM users WHERE id = 1"
        assert result[1] == "DROP TABLE users"

    def test_parse_rollback_statements_case_insensitive(self, temp_dir: str) -> None:
        """Test rollback marker is case insensitive."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- ROLLBACK
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "DROP TABLE users"

    def test_parse_rollback_statements_with_spaces(self, temp_dir: str) -> None:
        """Test rollback marker with extra spaces."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        --   rollback   
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "DROP TABLE users"

    def test_parse_rollback_statements_no_rollback_section(self, temp_dir: str) -> None:
        """Test parsing file with no rollback section."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert result == []

    def test_parse_rollback_statements_empty_rollback(self, temp_dir: str) -> None:
        """Test parsing file with empty rollback section."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- rollback
        -- No actual statements here
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert result == []

    def test_parse_rollback_statements_only_rollback_marker(
        self, temp_dir: str
    ) -> None:
        """Test parsing file with only rollback marker."""
        sql_content = "-- rollback"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert result == []

    def test_parse_rollback_statements_no_semicolon(self, temp_dir: str) -> None:
        """Test rollback statements without semicolons are ignored."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- rollback
        DROP TABLE users
        DELETE FROM another_table;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 1
        assert result[0] == "DROP TABLE users DELETE FROM another_table"

    def test_parse_rollback_statements_mixed_empty_lines(self, temp_dir: str) -> None:
        """Test rollback parsing with mixed empty lines."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- rollback
        
        
        DELETE FROM users WHERE id = 1;
        
        
        DROP TABLE users;
        
        
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 2
        assert result[0] == "DELETE FROM users WHERE id = 1"
        assert result[1] == "DROP TABLE users"

    def test_parse_rollback_statements_empty_file(self, temp_dir: str) -> None:
        """Test parsing an empty file for rollback statements."""
        sql_file = Path(temp_dir) / "empty.sql"
        sql_file.write_text("")
        result = parse_rollback_statements(str(sql_file))

        assert result == []

    def test_parse_rollback_statements_complex_scenario(self, temp_dir: str) -> None:
        """Test complex scenario with multiple upgrade and rollback statements."""
        sql_content = """
        -- Create initial schema
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        CREATE INDEX idx_users_name ON users(name);
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        INSERT INTO users (id, name) VALUES (2, 'Bob');
        
        -- rollback
        -- Remove test data first
        DELETE FROM users WHERE id IN (1, 2);
        -- Drop index
        DROP INDEX idx_users_name;
        -- Finally drop table
        DROP TABLE users;
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 3
        assert result[0] == "DELETE FROM users WHERE id IN (1, 2)"
        assert result[1] == "DROP INDEX idx_users_name"
        assert result[2] == "DROP TABLE users"
