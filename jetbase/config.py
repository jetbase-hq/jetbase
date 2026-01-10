import importlib.machinery
import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import tomli

from jetbase.constants import ENV_FILE


@dataclass
class JetbaseConfig:
    """
    Configuration settings for Jetbase migrations.

    This dataclass holds all configuration values loaded from env.py,
    environment variables, or TOML configuration files.

    Attributes:
        sqlalchemy_url (str): The SQLAlchemy database connection URL.
        postgres_schema (str | None): Optional PostgreSQL schema to use.
            Defaults to None.
        skip_checksum_validation (bool): If True, skips validation that
            migration files haven't been modified. Defaults to False.
        skip_file_validation (bool): If True, skips validation that all
            migration files exist. Defaults to False.
        skip_validation (bool): If True, skips all validations.
            Defaults to False.

    Raises:
        TypeError: If any boolean field receives a non-boolean value.
    """

    sqlalchemy_url: str
    postgres_schema: str | None = None
    skip_checksum_validation: bool = False
    skip_file_validation: bool = False
    skip_validation: bool = False
    snowflake_private_key: str | None = None
    snowflake_private_key_password: str | None = None

    def __post_init__(self):
        # Validate skip_checksum_validation
        if not isinstance(self.skip_checksum_validation, bool):
            raise TypeError(
                f"skip_checksum_validation must be bool, got {type(self.skip_checksum_validation).__name__}. "
                f"Value: {self.skip_checksum_validation!r}"
            )

        # Validate skip_file_validation
        if not isinstance(self.skip_file_validation, bool):
            raise TypeError(
                f"skip_file_validation must be bool, got {type(self.skip_file_validation).__name__}. "
                f"Value: {self.skip_file_validation!r}"
            )

        # Validate skip_validation
        if not isinstance(self.skip_validation, bool):
            raise TypeError(
                f"skip_validation must be bool, got {type(self.skip_validation).__name__}. "
                f"Value: {self.skip_validation!r}"
            )


ALL_KEYS: list[str] = [
    field.name for field in JetbaseConfig.__dataclass_fields__.values()
]


DEFAULT_VALUES: dict[str, Any] = {
    "skip_checksum_validation": False,
    "skip_file_validation": False,
    "skip_validation": False,
    "postgres_schema": None,
    "snowflake_private_key": None,
    "snowflake_private_key_password": None,
}

REQUIRED_KEYS: set[str] = {
    "sqlalchemy_url",
}


def get_config(
    keys: list[str] = ALL_KEYS,
    defaults: dict[str, Any] | None = DEFAULT_VALUES,
    required: set[str] | None = None,
) -> JetbaseConfig:
    """
    Load configuration from env.py, environment variables, or TOML files.

    Searches for configuration values in the following priority order:
    1. env.py file in the current directory
    2. Environment variables (JETBASE_{KEY_IN_UPPERCASE})
    3. jetbase.toml file
    4. pyproject.toml [tool.jetbase] section

    Args:
        keys (list[str]): List of configuration keys to retrieve.
            Defaults to ALL_KEYS.
        defaults (dict[str, Any] | None): Dictionary of default values
            for optional configuration keys. Defaults to DEFAULT_VALUES.
        required (set[str] | None): Set of keys that must be found.
            Defaults to None.

    Returns:
        JetbaseConfig: Configuration dataclass with all requested values.

    Raises:
        ValueError: If a required key is not found in any configuration source.

    Example:
        >>> config = get_config(required={"sqlalchemy_url"})
        >>> config.sqlalchemy_url
        'postgresql://localhost/mydb'
    """
    defaults = defaults or {}
    required = required or set()
    result: dict[str, Any] = {}

    for key in keys:
        value = _get_config_value(key)

        if value is not None:
            result[key] = value
        elif key in defaults:
            result[key] = defaults[key]
        elif key in required:
            raise ValueError(_get_config_help_message(key))
        else:
            result[key] = None

    config = JetbaseConfig(**result)
    return config


def _get_config_value(key: str) -> Any | None:
    """
    Get a configuration value from all sources in priority order.

    Checks env.py, environment variables, jetbase.toml, and pyproject.toml
    in that order, returning the first value found.

    Args:
        key (str): The configuration key to retrieve.

    Returns:
        Any | None: The configuration value from the first available source,
            or None if not found in any source.
    """
    # Try env.py
    value = _get_config_from_env_py(key)
    if value is not None:
        return value

    # Try environment variable
    value = _get_config_from_env_var(key)
    if value is not None:
        return value

    # Try jetbase.toml
    value = _get_config_from_jetbase_toml(key)
    if value is not None:
        return value

    # Try pyproject.toml
    pyproject_dir = _find_pyproject_toml()
    if pyproject_dir:
        value = _get_config_from_pyproject_toml(
            key=key, filepath=pyproject_dir / "pyproject.toml"
        )
        if value is not None:
            return value

    return None


def _get_config_from_env_py(key: str, filepath: str = ENV_FILE) -> Any | None:
    """
    Load a configuration value from the env.py file.

    Dynamically imports the env.py file and retrieves the specified attribute.

    Args:
        key (str): The configuration key to retrieve.
        filepath (str): Path to the env.py file relative to current directory.
            Defaults to ENV_FILE.

    Returns:
        Any | None: The configuration value if the attribute exists,
            otherwise None.
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

    config_value: Any | None = getattr(config, key, None)

    return config_value


def _get_config_from_jetbase_toml(
    key: str, filepath: str = "jetbase.toml"
) -> Any | None:
    """
    Load a configuration value from the jetbase.toml file.

    Args:
        key (str): The configuration key to retrieve.
        filepath (str): Path to the jetbase.toml file. Defaults to "jetbase.toml".

    Returns:
        Any | None: The configuration value if found, otherwise None.
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as f:
        jetbase_data = tomli.load(f)

    config_value: Any = jetbase_data.get(key, None)

    return config_value


def _get_config_from_pyproject_toml(key: str, filepath: Path) -> Any | None:
    """
    Load a configuration value from the pyproject.toml [tool.jetbase] section.

    Args:
        key (str): The configuration key to retrieve.
        filepath (Path): Path to the pyproject.toml file.

    Returns:
        Any | None: The configuration value if found in the [tool.jetbase]
            section, otherwise None.
    """
    with open(filepath, "rb") as f:
        pyproject_data = tomli.load(f)

        config_value: Any = pyproject_data.get("tool", {}).get("jetbase", {}).get(key)
        if config_value is None:
            return None

    return config_value


def _find_pyproject_toml(start: Path | None = None) -> Path | None:
    """
    Find pyproject.toml by traversing up from the starting directory.

    Walks up the directory tree from the specified starting point until
    it finds a pyproject.toml file or reaches the filesystem root.

    Args:
        start (Path | None): The directory to start searching from.
            Defaults to None, which uses the current working directory.

    Returns:
        Path | None: The directory containing pyproject.toml if found,
            otherwise None.
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


def _get_config_from_env_var(key: str) -> Any | None:
    """
    Load a configuration value from a JETBASE_{KEY} environment variable.

    Converts "true" and "false" string values to boolean True and False.

    Args:
        key (str): The configuration key to retrieve. Will be converted
            to uppercase and prefixed with "JETBASE_".

    Returns:
        Any | None: The environment variable value if set, otherwise None.
            Boolean strings are converted to Python booleans.
    """
    env_var_name = f"JETBASE_{key.upper()}"
    config_value: str | None = os.getenv(env_var_name, None)
    if config_value:
        if config_value.lower() == "true":
            return True
        if config_value.lower() == "false":
            return False
    return config_value


def _get_config_help_message(key: str) -> str:
    """
    Return a formatted help message for configuring a missing key.

    Provides examples showing all the different methods available to
    configure the specified key.

    Args:
        key (str): The configuration key that was not found.

    Returns:
        str: Multi-line help message with examples for env.py, environment
            variables, jetbase.toml, and pyproject.toml configuration.
    """
    env_var_name = f"JETBASE_{key.upper()}"
    return (
        f"Configuration '{key}' not found. Please configure it using one of these methods:\n\n"
        f"1. jetbase/env.py file:\n"
        f'   {key} = "your_value"\n\n'
        f"2. Environment variable:\n"
        f'   export {env_var_name}="your_value"\n\n'
        f"3. jetbase.toml file:\n"
        f'   {key} = "your_value"\n\n'
        f"4. pyproject.toml file:\n"
        f"   [tool.jetbase]\n"
        f'   {key} = "your_value"\n\n'
    )
