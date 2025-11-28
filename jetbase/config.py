import importlib.machinery
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any

import tomli

from jetbase.constants import CONFIG_FILE


def get_sqlalchemy_url() -> str:
    """
    Load SQLAlchemy URL from various configuration sources in priority order.

    Searches for the URL in the following order:
    1. config.py file
    2. JETBASE_SQLALCHEMY_URL environment variable
    3. jetbase.toml file
    4. pyproject.toml file

    Returns:
        str: The sqlalchemy_url from the first available source

    Raises:
        ValueError: If no valid SQLAlchemy URL is found in any source
    """
    sqlalchemy_url: str | None = None

    sqlalchemy_url = _get_sqlalchemy_url_from_config_py()
    if sqlalchemy_url:
        return sqlalchemy_url

    sqlalchemy_url = _get_sqlalchemy_url_from_env_var()
    if sqlalchemy_url:
        return sqlalchemy_url

    sqlalchemy_url = _get_sqlalchemy_url_from_jetbase_toml()
    if sqlalchemy_url:
        return sqlalchemy_url

    pyproject_dir: Path | None = _find_pyproject_toml()
    if pyproject_dir:
        sqlalchemy_url = _get_sqlalchemy_url_from_pyproject_toml(
            filepath=pyproject_dir / "pyproject.toml"
        )
        if sqlalchemy_url:
            return sqlalchemy_url

    raise ValueError(_get_sqlalchemy_url_help_message())


def _validate_sqlalchemy_url(url: Any) -> str:
    """
    Validates a SQLAlchemy URL string.
    This function checks if the provided URL is a valid string.
    Args:
        url (Any): The SQLAlchemy URL to validate (could be any type from user config).
    Returns:
        str: The validated SQLAlchemy URL string.
    Raises:
        TypeError: If the provided URL is not a string.
    """

    if not isinstance(url, str):
        raise TypeError(f"sqlalchemy_url must be a string, got {type(url).__name__}")

    return url


def _get_sqlalchemy_url_from_config_py(filepath: str = CONFIG_FILE) -> str | None:
    """
    Load the SQLAlchemy URL from the config.py file.

    Returns:
        str: The SQLAlchemy URL.
    """

    config_path: str = os.path.join(os.getcwd(), filepath)

    if not os.path.exists(config_path):
        return None

    spec: importlib.machinery.ModuleSpec | None = (
        importlib.util.spec_from_file_location("config", config_path)
    )

    assert spec is not None
    assert spec.loader is not None

    config: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module=config)

    sqlalchemy_url: Any | None = getattr(config, "sqlalchemy_url", None)

    return sqlalchemy_url


def _get_sqlalchemy_url_from_jetbase_toml(filepath: str = "jetbase.toml") -> str | None:
    """
    Load the SQLAlchemy URL from the jetbase.toml file.

    Returns:
        str: The SQLAlchemy URL.
    """

    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as f:
        jetbase_data = tomli.load(f)

    sqlalchemy_url: Any = jetbase_data.get("sqlalchemy_url", None)

    return sqlalchemy_url


def _get_sqlalchemy_url_from_pyproject_toml(filepath: Path) -> str | None:
    """
    Load the SQLAlchemy URL from the pyproject.toml file.

    Returns:
        str: The SQLAlchemy URL.
    """

    with open(filepath, "rb") as f:
        pyproject_data = tomli.load(f)

        sqlalchemy_url: Any = (
            pyproject_data.get("tool", {}).get("jetbase", {}).get("sqlalchemy_url")
        )
        if sqlalchemy_url is None:
            return None

    return sqlalchemy_url


def _find_pyproject_toml(start: Path | None = None) -> Path | None:
    """
    Locate the directory containing pyproject.toml by traversing upward from a starting directory.

    This function walks up the directory tree from the specified starting point (or current
    working directory if not specified) until it finds a pyproject.toml file or reaches the
    filesystem root.

    Args:
        start (Path | None, optional): The directory to start searching from. If None,
            uses the current working directory. Defaults to None.

    Returns:
        Path | None: The Path object pointing to the directory containing pyproject.toml
            if found, otherwise None if the file is not found before reaching the root.
    """

    if start is None:
        start = Path.cwd()

    current = start.resolve()

    while True:
        candidate = current / "pyproject.toml"
        if candidate.exists():
            return current

        if current.parent == current:  # reached root
            return None

        current = current.parent


def _get_sqlalchemy_url_from_env_var() -> str | None:
    """
    Load the SQLAlchemy URL from the JETBASE_SQLALCHEMY_URL environment variable.

    Returns:
        str: The SQLAlchemy URL.
    """
    sqlalchemy_url: str | None = os.getenv("JETBASE_SQLALCHEMY_URL", None)
    return sqlalchemy_url


def _get_sqlalchemy_url_help_message() -> str:
    """
    Return a formatted help message for configuring SQLAlchemy URL.

    Returns:
        str: A multi-line help message describing the different methods
            to configure the SQLAlchemy URL.
    """
    return (
        "SQLAlchemy URL not found. Please configure it using one of these methods:\n\n"
        "1. jetbase/config.py file:\n"
        '   sqlalchemy_url = "sqlite:///mydb.sqlite"\n\n'
        "2. Environment variable:\n"
        '   export JETBASE_SQLALCHEMY_URL="postgresql://user:pass@localhost/dbname"\n\n'
        "3. pyproject.toml file:\n"
        "   [tool.jetbase]\n"
        '   sqlalchemy_url = "postgresql://user:pass@localhost/dbname"\n\n'
    )
