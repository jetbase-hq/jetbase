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
    sqlalchemy_url: str
    postgres_schema: str | None = None
    skip_checksum_validation: bool = False
    skip_file_validation: bool = False

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


ALL_KEYS: list[str] = [
    field.name for field in JetbaseConfig.__dataclass_fields__.values()
]


DEFAULT_VALUES: dict[str, Any] = {
    "skip_checksum_validation": False,
    "skip_file_validation": False,
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
    Load configuration values from various sources in priority order.

    Searches for values in the following order:
    1. config.py file
    2. Environment variables (JETBASE_{KEY_IN_UPPERCASE})
    3. jetbase.toml file
    4. pyproject.toml file

    Args:
        keys: List of configuration keys to retrieve
        defaults: Optional dict of default values for keys
        required: Optional set of keys that must be found (raises ValueError if missing)

    Returns:
        dict: Dictionary with all requested configuration values

    Raises:
        ValueError: If a required key is not found in any source

    Example:
        config = get_config(
            keys=["sqlalchemy_url", "postgres_schema", "enforce_checksum_validation"],
            defaults={"enforce_checksum_validation": True},
            required={"sqlalchemy_url"}
        )
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
    # print(config)
    return config


def _get_config_value(key: str) -> Any | None:
    """
    Get a single configuration value from all sources in priority order.

    Args:
        key: The configuration key to retrieve

    Returns:
        The configuration value from the first available source, or None
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

    Args:
        key: The configuration key to retrieve
        filepath: Path to the config file

    Returns:
        Any | None: The configuration value if found, otherwise None
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
        key: The configuration key to retrieve
        filepath: Path to the jetbase.toml file

    Returns:
        Any | None: The configuration value if found, otherwise None
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath, "rb") as f:
        jetbase_data = tomli.load(f)

    config_value: Any = jetbase_data.get(key, None)

    return config_value


def _get_config_from_pyproject_toml(key: str, filepath: Path) -> Any | None:
    """
    Load a configuration value from the pyproject.toml file.

    Args:
        key: The configuration key to retrieve
        filepath: Path to the pyproject.toml file

    Returns:
        Any | None: The configuration value if found, otherwise None
    """
    with open(filepath, "rb") as f:
        pyproject_data = tomli.load(f)

        config_value: Any = pyproject_data.get("tool", {}).get("jetbase", {}).get(key)
        if config_value is None:
            return None

    return config_value


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


def _get_config_from_env_var(key: str) -> Any | None:
    """
    Load a configuration value from an environment variable.

    The environment variable name is constructed as JETBASE_{KEY_IN_UPPERCASE}.

    Args:
        key: The configuration key to retrieve

    Returns:
        Any | None: The configuration value if found, otherwise None
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
    Return a formatted help message for configuring a specific key.

    Args:
        key: The configuration key that was not found

    Returns:
        str: A multi-line help message describing the different methods
            to configure the specified key.
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
