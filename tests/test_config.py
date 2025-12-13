# import os
# import tempfile
# from pathlib import Path
# from unittest.mock import patch

# import pytest

# from jetbase.config import (
#     _find_pyproject_toml,
#     _get_sqlalchemy_url_from_config_py,
#     _get_sqlalchemy_url_from_env_var,
#     _get_sqlalchemy_url_from_jetbase_toml,
#     _get_sqlalchemy_url_from_pyproject_toml,
#     _get_sqlalchemy_url_help_message,
#     get_sqlalchemy_url,
# )


# class TestGetSqlalchemyUrlFromEnvVar:
#     """Tests for _get_sqlalchemy_url_from_env_var function."""

#     def test_get_url_from_env_var_exists(self):
#         """Test retrieving URL from environment variable when it exists."""
#         expected_url = "postgresql://user:pass@localhost/dbname"
#         with patch.dict(os.environ, {"JETBASE_SQLALCHEMY_URL": expected_url}):
#             result = _get_sqlalchemy_url_from_env_var()
#             assert result == expected_url

#     def test_get_url_from_env_var_not_exists(self):
#         """Test retrieving URL from environment variable when it doesn't exist."""
#         with patch.dict(os.environ, {}, clear=True):
#             result = _get_sqlalchemy_url_from_env_var()
#             assert result is None


# class TestGetSqlalchemyUrlFromConfigPy:
#     """Tests for _get_sqlalchemy_url_from_config_py function."""

#     def test_get_url_from_config_py_success(self):
#         """Test loading URL from config.py file."""
#         expected_url = "sqlite:///mydb.sqlite"

#         # Create a temporary config.py file
#         with tempfile.TemporaryDirectory() as tmpdir:
#             ENV_FILE = Path(tmpdir) / "config.py"
#             ENV_FILE.write_text(f'sqlalchemy_url = "{expected_url}"')

#             with patch("os.getcwd", return_value=tmpdir):
#                 with patch("jetbase.constants.ENV_FILE", "config.py"):
#                     result = _get_sqlalchemy_url_from_config_py()
#                     assert result == expected_url

#     def test_get_url_from_config_py_no_url(self):
#         """Test loading from config.py when sqlalchemy_url is not defined."""
#         with tempfile.TemporaryDirectory() as tmpdir:
#             ENV_FILE = Path(tmpdir) / "config.py"
#             ENV_FILE.write_text("# No sqlalchemy_url defined")

#             with patch("os.getcwd", return_value=tmpdir):
#                 with patch("jetbase.constants.ENV_FILE", "config.py"):
#                     result = _get_sqlalchemy_url_from_config_py()
#                     assert result is None


# class TestGetSqlalchemyUrlFromJetbaseToml:
#     """Tests for _get_sqlalchemy_url_from_jetbase_toml function."""

#     def test_get_url_from_jetbase_toml_success(self):
#         """Test loading URL from jetbase.toml file."""
#         expected_url = "mysql://user:pass@localhost/dbname"
#         toml_content = f'sqlalchemy_url = "{expected_url}"\n'

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "jetbase.toml"
#             toml_file.write_text(toml_content)

#             with patch("os.getcwd", return_value=tmpdir):
#                 result = _get_sqlalchemy_url_from_jetbase_toml(filepath=str(toml_file))
#                 assert result == expected_url

#     def test_get_url_from_jetbase_toml_no_url(self):
#         """Test loading from jetbase.toml when sqlalchemy_url is not defined."""
#         toml_content = "[other_config]\nkey = 'value'\n"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "jetbase.toml"
#             toml_file.write_text(toml_content)

#             with patch("os.getcwd", return_value=tmpdir):
#                 result = _get_sqlalchemy_url_from_jetbase_toml(filepath=str(toml_file))
#                 assert result is None


# class TestGetSqlalchemyUrlFromPyprojectToml:
#     """Tests for _get_sqlalchemy_url_from_pyproject_toml function."""

#     def test_get_url_from_pyproject_toml_success(self):
#         """Test loading URL from pyproject.toml file."""
#         expected_url = "postgresql://user:pass@localhost/dbname"
#         toml_content = f'[tool.jetbase]\nsqlalchemy_url = "{expected_url}"\n'

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "pyproject.toml"
#             toml_file.write_text(toml_content)

#             result = _get_sqlalchemy_url_from_pyproject_toml(toml_file)
#             assert result == expected_url

#     def test_get_url_from_pyproject_toml_no_tool_section(self):
#         """Test loading from pyproject.toml without tool.jetbase section."""
#         toml_content = '[project]\nname = "myproject"\n'

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "pyproject.toml"
#             toml_file.write_text(toml_content)

#             result = _get_sqlalchemy_url_from_pyproject_toml(toml_file)
#             assert result is None

#     def test_get_url_from_pyproject_toml_no_jetbase_section(self):
#         """Test loading from pyproject.toml without jetbase section."""
#         toml_content = '[tool.other]\nkey = "value"\n'

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "pyproject.toml"
#             toml_file.write_text(toml_content)

#             result = _get_sqlalchemy_url_from_pyproject_toml(toml_file)
#             assert result is None

#     def test_get_url_from_pyproject_toml_no_sqlalchemy_url(self):
#         """Test loading from pyproject.toml without sqlalchemy_url."""
#         toml_content = '[tool.jetbase]\nother_key = "value"\n'

#         with tempfile.TemporaryDirectory() as tmpdir:
#             toml_file = Path(tmpdir) / "pyproject.toml"
#             toml_file.write_text(toml_content)

#             result = _get_sqlalchemy_url_from_pyproject_toml(toml_file)
#             assert result is None


# class TestFindPyprojectToml:
#     """Tests for _find_pyproject_toml function."""

#     def test_find_pyproject_toml_in_current_dir(self):
#         """Test finding pyproject.toml in current directory."""
#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmppath = Path(tmpdir).resolve()  # resolve needed for macOS
#             pyproject_file = tmppath / "pyproject.toml"
#             pyproject_file.write_text("[project]\n")

#             result = _find_pyproject_toml(start=tmppath)
#             assert result == tmppath

#     def test_find_pyproject_toml_in_parent_dir(self):
#         """Test finding pyproject.toml in parent directory."""
#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmppath = Path(tmpdir).resolve()  # resolve needed for macOS
#             pyproject_file = tmppath / "pyproject.toml"
#             pyproject_file.write_text("[project]\n")

#             # Create subdirectory
#             subdir = tmppath / "subdir" / "nested"
#             subdir.mkdir(parents=True)

#             result = _find_pyproject_toml(start=subdir)
#             assert result == tmppath

#     def test_find_pyproject_toml_not_found(self):
#         """Test when pyproject.toml is not found."""
#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmppath = Path(tmpdir).resolve()  # resolve needed for macOS
#             subdir = tmppath / "subdir"
#             subdir.mkdir()

#             result = _find_pyproject_toml(start=subdir)
#             assert result is None

#     def test_find_pyproject_toml_default_start(self):
#         """Test finding pyproject.toml with default start directory."""
#         with patch("pathlib.Path.cwd") as mock_cwd:
#             with tempfile.TemporaryDirectory() as tmpdir:
#                 tmppath = Path(tmpdir).resolve()  # resolve needed for macOS
#                 mock_cwd.return_value = tmppath
#                 pyproject_file = tmppath / "pyproject.toml"
#                 pyproject_file.write_text("[project]\n")

#                 result = _find_pyproject_toml()
#                 assert result == tmppath


# class TestGetSqlalchemyUrlHelpMessage:
#     """Tests for _get_sqlalchemy_url_help_message function."""

#     def test_help_message_contains_all_methods(self):
#         """Test that help message contains all configuration methods."""
#         message = _get_sqlalchemy_url_help_message()

#         assert "config.py" in message
#         assert "Environment variable" in message
#         assert "jetbase.toml" in message
#         assert "pyproject.toml" in message
#         assert "JETBASE_SQLALCHEMY_URL" in message

#     def test_help_message_is_string(self):
#         """Test that help message returns a string."""
#         message = _get_sqlalchemy_url_help_message()
#         assert isinstance(message, str)


# class TestGetSqlalchemyUrl:
#     """Tests for get_sqlalchemy_url function (priority order tests)."""

#     def test_priority_config_py_first(self):
#         """Test that config.py has highest priority."""
#         config_url = "sqlite:///config.sqlite"
#         env_url = "sqlite:///env.sqlite"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             # Create config.py
#             ENV_FILE = Path(tmpdir) / "config.py"
#             ENV_FILE.write_text(f'sqlalchemy_url = "{config_url}"')

#             with patch("os.getcwd", return_value=tmpdir):
#                 with patch("jetbase.constants.ENV_FILE", "config.py"):
#                     with patch.dict(os.environ, {"JETBASE_SQLALCHEMY_URL": env_url}):
#                         result = get_sqlalchemy_url()
#                         assert result == config_url

#     def test_priority_env_var_second(self):
#         """Test that environment variable has second priority."""
#         env_url = "sqlite:///env.sqlite"
#         jetbase_toml_url = "sqlite:///jetbase.sqlite"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             # Create jetbase.toml
#             toml_file = Path(tmpdir) / "jetbase.toml"
#             toml_file.write_text(f'sqlalchemy_url = "{jetbase_toml_url}"\n')

#             # No config.py, but env var set
#             with patch("os.getcwd", return_value=tmpdir):
#                 with patch("jetbase.constants.ENV_FILE", "nonexistent_config.py"):
#                     with patch.dict(os.environ, {"JETBASE_SQLALCHEMY_URL": env_url}):
#                         result = get_sqlalchemy_url()
#                         assert result == env_url

#     def test_priority_jetbase_toml_third(self):
#         """Test that jetbase.toml has third priority."""
#         jetbase_toml_url = "sqlite:///jetbase.sqlite"
#         pyproject_url = "sqlite:///pyproject.sqlite"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmppath = Path(tmpdir).resolve()  # resolve needed for macOS

#             # Create jetbase.toml
#             jetbase_file = tmppath / "jetbase.toml"
#             jetbase_file.write_text(f'sqlalchemy_url = "{jetbase_toml_url}"\n')

#             # Create pyproject.toml
#             pyproject_file = tmppath / "pyproject.toml"
#             pyproject_file.write_text(
#                 f'[tool.jetbase]\nsqlalchemy_url = "{pyproject_url}"\n'
#             )

#             # Change to the temp directory
#             original_cwd = os.getcwd()
#             try:
#                 os.chdir(str(tmppath))
#                 with patch("jetbase.constants.ENV_FILE", "nonexistent_config.py"):
#                     with patch.dict(os.environ, {}, clear=True):
#                         result = get_sqlalchemy_url()
#                         assert result == jetbase_toml_url
#             finally:
#                 os.chdir(original_cwd)

#     def test_priority_pyproject_toml_fourth(self):
#         """Test that pyproject.toml has fourth priority."""
#         pyproject_url = "sqlite:///pyproject.sqlite"

#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmppath = Path(tmpdir).resolve()  # resolve needed for macOS

#             # Create pyproject.toml
#             pyproject_file = tmppath / "pyproject.toml"
#             pyproject_file.write_text(
#                 f'[tool.jetbase]\nsqlalchemy_url = "{pyproject_url}"\n'
#             )

#             # Change to the temp directory
#             original_cwd = os.getcwd()
#             try:
#                 os.chdir(str(tmppath))
#                 with patch("jetbase.constants.ENV_FILE", "nonexistent_config.py"):
#                     with patch.dict(os.environ, {}, clear=True):
#                         result = get_sqlalchemy_url()
#                         assert result == pyproject_url
#             finally:
#                 os.chdir(original_cwd)

#     def test_no_config_raises_value_error(self):
#         """Test that ValueError is raised when no configuration is found."""
#         with tempfile.TemporaryDirectory() as tmpdir:
#             with patch("os.getcwd", return_value=tmpdir):
#                 with patch("jetbase.constants.ENV_FILE", "nonexistent_config.py"):
#                     with patch.dict(os.environ, {}, clear=True):
#                         with patch("os.path.exists", return_value=False):
#                             with patch(
#                                 "jetbase.config._find_pyproject_toml", return_value=None
#                             ):
#                                 with pytest.raises(
#                                     ValueError, match="SQLAlchemy URL not found"
#                                 ):
#                                     get_sqlalchemy_url()
