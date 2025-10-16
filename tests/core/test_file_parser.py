import tempfile
from pathlib import Path

import pytest

from jetbase.core.file_parser import parse_sql_file


class TestParseSqlFile:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_parse_sql_file_single_statement(self, temp_dir):
        """Test parsing a file with a single SQL statement."""
        sql_content = "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 1
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"

    def test_parse_sql_file_single_statement_multi_line(self, temp_dir):
        """Test parsing a file with a single SQL statement."""
        sql_content = "CREATE TABLE users \n (id INT PRIMARY KEY, name VARCHAR(100));"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 1
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"

    def test_parse_sql_file_multiple_statements(self, temp_dir):
        """Test parsing a file with multiple SQL statements."""
        sql_content = """
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        INSERT INTO users (id, name) VALUES (2, 'Bob');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 3
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        assert result[2] == "INSERT INTO users (id, name) VALUES (2, 'Bob')"

    def test_parse_sql_file_empty(self, temp_dir):
        """Test parsing an empty SQL file."""
        sql_file = Path(temp_dir) / "empty.sql"
        sql_file.write_text("")
        result = parse_sql_file(str(sql_file))

        assert result == []

    def test_parse_sql_file_with_comments(self, temp_dir):
        """Test parsing SQL file with comments."""
        sql_content = """
        -- This is a comment
        CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
        
        -- Another comment
        INSERT INTO users (id, name) VALUES (1, 'Alice');
        
        -- Single line comments instead of multi-line
        -- Second line of comment
        INSERT INTO users (id, name) VALUES (2, 'Bob');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 3
        assert result[0] == "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))"
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        assert result[2] == "INSERT INTO users (id, name) VALUES (2, 'Bob')"

    def test_parse_sql_file_with_comments_in_stmts(self, temp_dir):
        """Test parsing SQL file with comments within statements."""
        sql_content = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(100) 
        );
        --first comment
        
        INSERT INTO users (id, name) 
        -- Insert first user
        VALUES (1, 'Alice'); 
        
        INSERT INTO users (id, name) 
        -- Insert second user
        VALUES (2, 'Bob');
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 3
        assert (
            result[0] == "CREATE TABLE users ( id INT PRIMARY KEY, name VARCHAR(100) )"
        )
        assert result[1] == "INSERT INTO users (id, name) VALUES (1, 'Alice')"
        assert result[2] == "INSERT INTO users (id, name) VALUES (2, 'Bob')"

    def test_parse_sql_file_with_inline_comments(self, temp_dir):
        """Test parsing SQL file with inline comments within statements."""
        """The last 2 stmts won't show up because they don't end with semicolon."""
        sql_content = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(100) -- User's name
        );
        
        INSERT INTO users (id, name) VALUES (1, 'Alice'); -- Insert first user
        
        INSERT INTO users (id, name) VALUES (2, 'Bob'); -- Insert second user
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_sql_file(str(sql_file))

        assert len(result) == 1
        assert (
            result[0]
            == "CREATE TABLE users ( id INT PRIMARY KEY, name VARCHAR(100) -- User's name )"
        )
