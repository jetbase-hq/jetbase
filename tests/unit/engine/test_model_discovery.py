import os
import tempfile
from unittest.mock import patch

import pytest

from jetbase.engine.model_discovery import (
    ModelDiscoveryError,
    ModelFileNotFoundError,
    ModelImportError,
    ModelPathsNotSetError,
    NoModelsFoundError,
    discover_all_models,
    discover_models_from_path,
    find_declarative_base_in_module,
    get_model_paths_from_env,
    import_model_file,
    validate_model_paths,
)


def test_get_model_paths_from_env_set():
    """Test getting model paths from environment variable."""
    with patch.dict(
        os.environ, {"JETBASE_MODELS": "./models/user.py,./models/product.py"}
    ):
        paths = get_model_paths_from_env()
        assert paths == ["./models/user.py", "./models/product.py"]


def test_get_model_paths_from_env_not_set():
    """Test error when JETBASE_MODELS is not set."""
    with patch.dict(os.environ, {"JETBASE_MODELS": ""}, clear=True):
        with pytest.raises(ModelPathsNotSetError) as exc_info:
            get_model_paths_from_env()

        assert "JETBASE_MODELS" in str(exc_info.value)


def test_get_model_paths_from_env_with_spaces():
    """Test getting model paths with spaces around paths."""
    with patch.dict(
        os.environ, {"JETBASE_MODELS": " ./models/user.py , ./models/product.py "}
    ):
        paths = get_model_paths_from_env()
        assert paths == ["./models/user.py", "./models/product.py"]


def test_validate_model_paths_valid():
    """Test validation passes with valid paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("# test model")

        validate_model_paths([model_file])


def test_validate_model_paths_invalid():
    """Test validation fails with invalid paths."""
    with pytest.raises(ModelFileNotFoundError) as exc_info:
        validate_model_paths(["./nonexistent/path.py"])

    assert "not found" in str(exc_info.value).lower()


def test_import_model_file():
    """Test importing a valid Python model file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("x = 1")

        module = import_model_file(model_file)
        assert module.x == 1


def test_import_model_file_syntax_error():
    """Test import fails with syntax error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("def invalid syntax here")

        with pytest.raises(ModelImportError) as exc_info:
            import_model_file(model_file)

        assert "Syntax error" in str(exc_info.value)


def test_find_declarative_base_in_module():
    """Test finding DeclarativeBase in a module."""
    from sqlalchemy.orm import DeclarativeBase

    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
""")

        module = import_model_file(model_file)
        base = find_declarative_base_in_module(module)

        assert base is not None
        assert issubclass(base, DeclarativeBase)


def test_find_declarative_base_in_module_not_found():
    """Test finding DeclarativeBase returns None when not present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("x = 1")

        module = import_model_file(model_file)
        base = find_declarative_base_in_module(module)

        assert base is None


def test_discover_models_from_path_with_models():
    """Test discovering models from a file with SQLAlchemy models."""
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy import Column, Integer, String

    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
""")

        models = discover_models_from_path(model_file)

        assert len(models) == 1
        assert models[0].__tablename__ == "users"


def test_discover_models_from_path_no_models():
    """Test discovering models returns empty list when no models present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("x = 1")

        models = discover_models_from_path(model_file)

        assert models == []


def test_discover_all_models():
    """Test discovering all models from multiple paths."""
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy import Column, Integer, String

    with tempfile.TemporaryDirectory() as tmpdir:
        user_file = os.path.join(tmpdir, "user.py")
        with open(user_file, "w") as f:
            f.write("""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
""")

        product_file = os.path.join(tmpdir, "product.py")
        with open(product_file, "w") as f:
            f.write("""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
""")

        with patch.dict(os.environ, {"JETBASE_MODELS": f"{user_file},{product_file}"}):
            base, models = discover_all_models()

            assert len(models) == 2
            assert "users" in models
            assert "products" in models


def test_discover_all_models_no_models_found():
    """Test error when no models are found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("x = 1")

        with patch.dict(os.environ, {"JETBASE_MODELS": model_file}):
            with pytest.raises(NoModelsFoundError) as exc_info:
                discover_all_models()

            assert "No SQLAlchemy models found" in str(exc_info.value)


def test_discover_all_models_with_relative_paths():
    """Test discovering models with relative paths."""
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy import Column, Integer

    with tempfile.TemporaryDirectory() as tmpdir:
        model_file = os.path.join(tmpdir, "models.py")
        with open(model_file, "w") as f:
            f.write("""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer

class Base(DeclarativeBase):
    pass

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True)
""")

        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            with patch.dict(os.environ, {"JETBASE_MODELS": "./models.py"}):
                base, models = discover_all_models()

                assert len(models) == 1
                assert "tests" in models
        finally:
            os.chdir(original_dir)
