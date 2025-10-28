import importlib.machinery
import importlib.util
import os

# from importlib import ModuleType
from types import ModuleType
from typing import Any

from jetbase.constants import CONFIG_FILE


def get_sqlalchemy_url(filename: str = CONFIG_FILE) -> str:
    """
    Load a config file and extract the sqlalchemy_url.

    Args:
        config_filename: Name of the config file (e.g., "config.py")

    Returns:
        The sqlalchemy_url from the config file, or None if not found
    """
    config_path: str = os.path.join(os.getcwd(), filename)
    spec: importlib.machinery.ModuleSpec | None = (
        importlib.util.spec_from_file_location("config", config_path)
    )

    assert spec is not None
    assert spec.loader is not None

    config: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module=config)

    raw_sqlalchemy_url: Any | None = getattr(config, "sqlalchemy_url", None)

    if raw_sqlalchemy_url is None:
        raise AttributeError(
            f"'sqlalchemy_url' not found or is set to None. Please define it in {config_path}."
        )

    sqlalchemy_url: str = _validate_sqlalchemy_url(url=raw_sqlalchemy_url)

    return sqlalchemy_url


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
