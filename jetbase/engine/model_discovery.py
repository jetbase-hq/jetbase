import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from jetbase.config import get_config
from jetbase.engine.jetbase_locator import find_jetbase_directory


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


def _add_project_root_to_path(model_path: str) -> None:
    """
    Add the project root to sys.path if needed for imports to work.

    Finds the project root (where pyproject.toml or jetbase/ is located)
    and adds it to sys.path so that imports like 'from app.core.database import Base'
    work correctly.

    Args:
        model_path: Path to the model file being imported.
    """
    model_file = Path(model_path).resolve()

    candidates = []

    jetbase_dir = find_jetbase_directory()
    if jetbase_dir:
        candidates.append(jetbase_dir.parent)

    candidates.append(model_file.parent)

    for candidate in candidates:
        if candidate.exists():
            str_path = str(candidate)
            if str_path not in sys.path:
                sys.path.insert(0, str_path)


def discover_model_paths_auto() -> list[str]:
    """
    Automatically discover model paths by searching for model/models directories.

    Searches the entire project tree recursively for any directory named
    'models' or 'model' and collects all Python files from them.

    Excludes common virtual environment directories (.venv, venv, node_modules, etc.)

    Returns:
        list[str]: List of paths to discovered Python model files.

    Raises:
        ModelDiscoveryError: If no model directories are found.
    """
    discovered_paths: list[str] = []
    model_file_extensions = (".py",)

    jetbase_dir = find_jetbase_directory()

    if jetbase_dir:
        project_root = jetbase_dir.parent
    else:
        project_root = Path.cwd()

    current = project_root.resolve()
    while current != current.parent:
        if current.exists():
            break
        current = current.parent

    seen_files: set[str] = set()

    exclude_dirs = {
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".git",
        ".tox",
        ".nox",
        "build",
        "dist",
    }

    for root, dirs, files in os.walk(current):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        dirname = os.path.basename(root)
        if dirname == "models" or dirname == "model":
            for file in files:
                if file.endswith(model_file_extensions) and not file.startswith("_"):
                    full_path = os.path.join(root, file)
                    if full_path not in seen_files:
                        seen_files.add(full_path)
                        discovered_paths.append(full_path)

    return discovered_paths


def get_model_paths_from_config() -> list[str] | None:
    """
    Get model paths from Jetbase configuration.

    Checks config.model_paths first, then falls back to JETBASE_MODELS env var.
    Resolves paths relative to the jetbase directory.

    Returns:
        list[str] | None: List of model paths from config, or None if not set.
    """
    jetbase_dir = find_jetbase_directory()

    try:
        config = get_config()
        if config.model_paths:
            if jetbase_dir:
                return [
                    os.path.normpath(os.path.join(jetbase_dir, p))
                    for p in config.model_paths
                ]
            return config.model_paths
    except ValueError:
        pass

    model_paths_str = os.getenv("JETBASE_MODELS", "")
    if model_paths_str:
        paths = [p.strip() for p in model_paths_str.split(",") if p.strip()]
        if jetbase_dir:
            return [os.path.normpath(os.path.join(jetbase_dir, p)) for p in paths]
        return paths

    return None


def get_model_paths_from_env() -> list[str]:
    """
    Get model paths from JETBASE_MODELS environment variable.

    Returns:
        list[str]: List of model file paths from the environment variable.

    Raises:
        ModelPathsNotSetError: If JETBASE_MODELS is not set.
    """
    model_paths = get_model_paths_from_config()
    if model_paths:
        return model_paths

    raise ModelPathsNotSetError(
        "Model paths not configured. Please set one of the following:\n"
        "1. model_paths in jetbase/env.py\n"
        "2. JETBASE_MODELS environment variable\n"
        "3. Place your models in a 'models/' or 'model/' directory\n"
        "   relative to your project or jetbase directory"
    )


def validate_model_paths(model_paths: list[str]) -> None:
    """
    Validate that all model paths exist.

    Checks paths as absolute first, then tries resolving relative to jetbase directory.

    Args:
        model_paths (list[str]): List of paths to model files.

    Raises:
        ModelFileNotFoundError: If any model file path does not exist.
    """
    for path in model_paths:
        resolved_path = Path(path)

        if resolved_path.exists():
            continue

        if resolved_path.is_absolute():
            raise ModelFileNotFoundError(
                f"Model file not found: {path}\n"
                f"Please check that the path exists and is correct."
            )

        jetbase_dir = find_jetbase_directory()
        if jetbase_dir:
            alt_path = Path(jetbase_dir) / path
            if alt_path.exists():
                continue

        raise ModelFileNotFoundError(
            f"Model file not found: {path}\n"
            f"Please check that the path exists and is correct."
        )


def import_model_file(model_path: str) -> ModuleType:
    """
    Dynamically import a Python model file.

    Automatically adds the project root to sys.path so that relative imports
    (like 'from app.core.database import Base') work correctly.

    Args:
        model_path (str): Path to the Python model file.

    Returns:
        ModuleType: The imported module.

    Raises:
        ModelImportError: If the file cannot be imported.
    """
    try:
        _add_project_root_to_path(model_path)

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
            If None, first tries config/env var, then auto-discovers from
            model/models directories.

    Returns:
        tuple: A tuple containing:
            - The discovered DeclarativeBase class
            - Dictionary mapping table names to model classes

    Raises:
        ModelFileNotFoundError: If any model file path does not exist.
        ModelImportError: If a model file cannot be imported.
        NoModelsFoundError: If no SQLAlchemy models are found.
    """
    if model_paths is None:
        model_paths = get_model_paths_from_config()
        if model_paths is None:
            model_paths = discover_model_paths_auto()
            if not model_paths:
                raise NoModelsFoundError(
                    "No SQLAlchemy models found.\n"
                    "Please either:\n"
                    "  1. Set model_paths in jetbase/env.py\n"
                    "  2. Set JETBASE_MODELS environment variable\n"
                    "  3. Place your models in a 'models/' or 'model/' directory"
                )

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

    return discovered_base or type("DeclarativeBase", (), {}), all_models


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
