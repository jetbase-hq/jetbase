import tempfile
from pathlib import Path
from typing import Generator

import pytest

from jetbase.engine.file_parser import (
    _get_raw_description_from_filename,
    _get_version_from_filename,
    is_valid_version,
    get_description_from_filename,
    is_filename_format_valid,
    is_filename_length_valid,
    parse_rollback_statements,
    parse_upgrade_statements,
    _extract_delimiter_from_file,
)


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

    def test_parse_upgrade_statements_with_custom_delimiter(
        self, temp_dir: str
    ) -> None:
        """Test parsing statements with custom delimiter."""
        sql_content = """-- jetbase: delimiter=~

        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            updated_at TIMESTAMP
        );~
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;~

        CREATE TRIGGER users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();~
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_upgrade_statements(str(sql_file))

        assert len(result) == 3
        assert "CREATE TABLE users" in result[0]
        assert "CREATE OR REPLACE FUNCTION set_updated_at()" in result[1]
        assert "NEW.updated_at = NOW();" in result[1]  # Internal semicolon preserved
        assert "CREATE TRIGGER users_updated_at" in result[2]


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

    def test_parse_rollback_statements_with_custom_delimiter(
        self, temp_dir: str
    ) -> None:
        """Test parsing rollback statements with custom delimiter for functions containing semicolons."""
        sql_content = """-- jetbase: delimiter=~

        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            updated_at TIMESTAMP
        );~
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;~

        CREATE TRIGGER users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();~

        -- rollback
        DROP TRIGGER IF EXISTS users_updated_at ON users;~
        DROP FUNCTION IF EXISTS set_updated_at();~
        DROP TABLE IF EXISTS users;~
        """
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = parse_rollback_statements(str(sql_file))

        assert len(result) == 3
        assert result[0] == "DROP TRIGGER IF EXISTS users_updated_at ON users;"
        assert result[1] == "DROP FUNCTION IF EXISTS set_updated_at();"
        assert result[2] == "DROP TABLE IF EXISTS users;"

    def test_is_filename_format_valid(self) -> None:
        """Test validation of migration filenames."""
        assert is_filename_format_valid("V1__initial_setup.sql") is True
        assert is_filename_format_valid("V1_2__add_feature.sql") is True
        assert is_filename_format_valid("V1.2.3__fix_bug.sql") is True
        assert is_filename_format_valid("1__missing_v_prefix.sql") is False
        assert is_filename_format_valid("V1-add_feature.sql") is False
        assert is_filename_format_valid("V1__no_sql_extension.txt") is False
        assert is_filename_format_valid("V__no_version.sql") is False
        assert is_filename_format_valid("V1..2__description.sql") is False
        assert is_filename_format_valid("V1._2__description.sql") is False
        assert is_filename_format_valid("V1.__description.sql") is False
        assert is_filename_format_valid("V1_2_3__description.SQL") is False
        assert is_filename_format_valid("V1_.2__ .sql") is False
        assert is_filename_format_valid("V__description.sql") is False
        assert is_filename_format_valid("V.sql") is False
        assert is_filename_format_valid("V1_2_3__.sql") is False
        assert is_filename_format_valid("V1_2_3__   .sql") is False

    def test_is_filename_length_valid(self) -> None:
        """Test validation of filename length."""
        valid_filename = "V1_0_0__initial_setup.sql"
        long_filename = "V" + "1_" * 300 + "__description.sql"

        assert is_filename_length_valid(valid_filename) is True
        assert is_filename_length_valid(long_filename) is False

    def testis_valid_version(self) -> None:
        """Test validation of version strings."""
        assert is_valid_version("1") is True
        assert is_valid_version("1.0") is True
        assert is_valid_version("1.0.0") is True
        assert is_valid_version("10.2.3") is True
        assert is_valid_version("0.1") is True
        assert is_valid_version("0.0.1") is True
        assert is_valid_version("1..2") is False
        assert is_valid_version("1.2.") is False
        assert is_valid_version(".1.2") is False
        assert is_valid_version("1.2.a") is False
        assert is_valid_version("a.b.c") is False
        assert is_valid_version("") is False
        assert is_valid_version("1_2_3") is True

    def test_get_version_from_filename(self) -> None:
        """Test extraction of version from migration filenames."""
        assert _get_version_from_filename("V1__initial_setup.sql") == "1"
        assert _get_version_from_filename("V1_2__add_feature.sql") == "1_2"
        assert _get_version_from_filename("V1.2.3__fix_bug.sql") == "1.2.3"
        assert (
            _get_version_from_filename("V10_20_30__complex_version.sql") == "10_20_30"
        )
        assert _get_version_from_filename("Vhello__leading_zero.sql") == "hello"
        assert _get_version_from_filename("V0_1__.sql") == "0_1"

    def test_get_raw_description_from_filename(self) -> None:
        """Test extraction of description from migration filenames."""
        assert (
            _get_raw_description_from_filename("V1__initial_setup.sql")
            == "initial_setup"
        )
        assert (
            _get_raw_description_from_filename("V1_2__add_feature.sql") == "add_feature"
        )
        assert _get_raw_description_from_filename("V1.2.3__fix_bug.sql") == "fix_bug"
        assert (
            _get_raw_description_from_filename("V10_20_30__complex_version.sql")
            == "complex_version"
        )
        assert (
            _get_raw_description_from_filename("Vhello__leading_zero.sql")
            == "leading_zero"
        )
        assert _get_raw_description_from_filename("V0_1__.sql") == ""
        assert _get_raw_description_from_filename("V0_1__    .sql") == ""

    def test_get_description_from_filename(self) -> None:
        """Test formatting of description from migration filenames."""
        assert get_description_from_filename("V1__initial_setup.sql") == "initial setup"
        assert get_description_from_filename("V1_2__add_feature.sql") == "add feature"
        assert get_description_from_filename("V1.2.3__fix_bug.sql") == "fix bug"
        assert (
            get_description_from_filename("V10_20_30__complex_version.sql")
            == "complex version"
        )
        assert (
            get_description_from_filename("Vhello__leading_zero.sql") == "leading zero"
        )
        assert get_description_from_filename("V0_1__.sql") == ""
        assert get_description_from_filename("V0_1__    .sql") == ""


class TestExtractDelimiterFromFile:
    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_extract_delimiter_default_when_not_specified(self, temp_dir: str) -> None:
        """Test that default delimiter (;) is returned when not specified."""
        sql_content = "CREATE TABLE users (id INT PRIMARY KEY);"
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = _extract_delimiter_from_file(str(sql_file))

        assert result == ";"

    def test_extract_delimiter_custom_single_char(self, temp_dir: str) -> None:
        """Test extraction of a single character custom delimiter."""
        sql_content = """-- jetbase: delimiter=~
CREATE TABLE users (id INT PRIMARY KEY)~
"""
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = _extract_delimiter_from_file(str(sql_file))

        assert result == "~"

    def test_extract_delimiter_custom_multi_char(self, temp_dir: str) -> None:
        """Test extraction of a multi-character custom delimiter."""
        sql_content = """-- jetbase: delimiter=$$
CREATE FUNCTION test() RETURNS void$$
"""
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = _extract_delimiter_from_file(str(sql_file))

        assert result == "$$"

    def test_extract_delimiter_case_insensitive(self, temp_dir: str) -> None:
        """Test that the jetbase directive is case insensitive."""
        sql_content = """-- JETBASE: DELIMITER=|
CREATE TABLE users (id INT PRIMARY KEY)|
"""
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = _extract_delimiter_from_file(str(sql_file))

        assert result == "|"

    def test_extract_delimiter_stops_at_non_comment_line(self, temp_dir: str) -> None:
        """Test that delimiter search stops after first non-comment line."""
        sql_content = """CREATE TABLE users (id INT PRIMARY KEY);
-- jetbase: delimiter=~
"""
        sql_file = Path(temp_dir) / "test.sql"
        sql_file.write_text(sql_content)
        result = _extract_delimiter_from_file(str(sql_file))

        assert result == ";"

        def test_extract_delimiter_random_case(self, temp_dir: str) -> None:
            """Test extraction where the delimiter directive uses random upper/lowercase letters."""
            sql_content = """-- JeTbAsE: DelImItEr=~
CREATE TABLE users (id INT PRIMARY KEY)~
"""
            sql_file = Path(temp_dir) / "test.sql"
            sql_file.write_text(sql_content)
            result = _extract_delimiter_from_file(str(sql_file))

            assert result == "~"
