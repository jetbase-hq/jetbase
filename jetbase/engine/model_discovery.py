import importlib.machinery
import importlib.util
import os
from pathlib import Path
from types import ModuleType
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class ModelDiscoveryError(Exception):
    """Base exception for model discovery errors."""

    pass


class ModelPathsNotSetError(ModelDiscoveryError):
    """Raised when JETBASE_MODELS environment variable is not set."""

    pass


class ModelFileNotFoundError(ModelDiscoveryError):
    """Raised when a model file path does not exist."""

    pass


class ModelImportError(ModelDiscoveryError):
    """Raised when a model file cannot be imported."""

    pass


class NoModelsFoundError(ModelDiscoveryError):
    """Raised when no SQLAlchemy models are found in the provided paths."""

    pass


def get_model_paths_from_env() -> list[str]:
    """
    Get model paths from JETBASE_MODELS environment variable.

    Returns:
        list[str]: List of model file paths from the environment variable.

    Raises:
        ModelPathsNotSetError: If JETBASE_MODELS is not set.
    """
    model_paths_str = os.getenv("JETBASE_MODELS", "")
    if not model_paths_str:
        raise ModelPathsNotSetError(
            "JETBASE_MODELS environment variable is not set. "
            "Please set it to the path(s) of your SQLAlchemy model files.\n"
            "Example: export JETBASE_MODELS='./models/user.py,./models/product.py'"
        )

    paths = [p.strip() for p in model_paths_str.split(",") if p.strip()]
    return paths


def validate_model_paths(model_paths: list[str]) -> None:
    """
    Validate that all model paths exist.

    Args:
        model_paths (list[str]): List of paths to model files.

    Raises:
        ModelFileNotFoundError: If any model file path does not exist.
    """
    for path in model_paths:
        resolved_path = Path(path)
        if not resolved_path.exists():
            raise ModelFileNotFoundError(
                f"Model file not found: {path}\n"
                f"Please check that the path exists and is correct."
            )


def import_model_file(model_path: str) -> ModuleType:
    """
    Dynamically import a Python model file.

    Args:
        model_path (str): Path to the Python model file.

    Returns:
        ModuleType: The imported module.

    Raises:
        ModelImportError: If the file cannot be imported.
    """
    try:
        spec = importlib.util.spec_from_file_location(
            name=Path(model_path).stem, location=model_path
        )
        if spec is None or spec.loader is None:
            raise ModelImportError(f"Cannot load spec for model file: {model_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except SyntaxError as e:
        raise ModelImportError(f"Syntax error in model file {model_path}: {e}")
    except Exception as e:
        raise ModelImportError(f"Error importing model file {model_path}: {e}")


def find_declarative_base_in_module(module: ModuleType) -> type | None:
    """
    Find a SQLAlchemy DeclarativeBase class in a module.

    Args:
        module (ModuleType): The module to search.

    Returns:
        type | None: The found DeclarativeBase class, or None.
    """
    for attr_name in dir(module):
        try:
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and hasattr(attr, "registry")
                and attr is not type(attr)  # Exclude the registry class itself
            ):
                return attr
        except TypeError:
            continue
    return None


def discover_models_from_path(model_path: str) -> list[type[Any]]:
    """
    Discover SQLAlchemy models from a single model file.

    Args:
        model_path (str): Path to the Python model file.

    Returns:
        list[type[Any]]: List of discovered model classes.
    """
    module = import_model_file(model_path)
    base = find_declarative_base_in_module(module)

    if base is None:
        return []

    models = []
    for attr_name in dir(module):
        try:
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, base)
                and attr is not base
                and hasattr(attr, "__tablename__")
            ):
                models.append(attr)
        except TypeError:
            continue

    return models


def discover_all_models(
    model_paths: list[str] | None = None,
) -> tuple[type, dict[str, type[Any]]]:
    """
    Discover all SQLAlchemy models from provided paths.

    Args:
        model_paths (list[str] | None): List of paths to model files.
            If None, reads from JETBASE_MODELS environment variable.

    Returns:
        tuple: A tuple containing:
            - The discovered DeclarativeBase class
            - Dictionary mapping table names to model classes

    Raises:
        ModelPathsNotSetError: If model_paths is None and JETBASE_MODELS is not set.
        ModelFileNotFoundError: If any model file path does not exist.
        ModelImportError: If a model file cannot be imported.
        NoModelsFoundError: If no SQLAlchemy models are found.
    """
    if model_paths is None:
        model_paths = get_model_paths_from_env()

    validate_model_paths(model_paths)

    all_models: dict[str, type[Any]] = {}
    discovered_base: type[DeclarativeBase] | None = None

    for path in model_paths:
        module = import_model_file(path)
        base = find_declarative_base_in_module(module)

        if base is not None:
            if discovered_base is None:
                discovered_base = base
            elif discovered_base is not base:
                pass

        for attr_name in dir(module):
            try:
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, "__tablename__"):
                    if discovered_base is not None and issubclass(
                        attr, discovered_base
                    ):
                        if attr is not discovered_base:
                            table_name = attr.__tablename__
                            if table_name not in all_models:
                                all_models[table_name] = attr
                    elif base is not None and issubclass(attr, base):
                        if attr is not base:
                            table_name = attr.__tablename__
                            if table_name not in all_models:
                                all_models[table_name] = attr
            except TypeError:
                continue

    if discovered_base is None and all_models:
        pass

    if not all_models:
        raise NoModelsFoundError(
            "No SQLAlchemy models found in the provided model paths.\n"
            "Make sure your model files define classes that inherit from "
            "a SQLAlchemy DeclarativeBase and have __tablename__ defined."
        )

    return discovered_base, all_models


def get_model_metadata(models: dict[str, type[Any]]) -> MetaData:
    """
    Extract metadata from discovered models.

    Args:
        models (dict[str, type[Any]]): Dictionary mapping table names to model classes.

    Returns:
        MetaData: SQLAlchemy MetaData object containing all table definitions.
    """
    metadata = MetaData()

    for table_name, model_class in models.items():
        if hasattr(model_class, "__table__"):
            metadata._add_table(model_class.__table__)

    return metadata
