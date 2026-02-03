import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jetbase.commands.make_migrations import (
    MakeMigrationsError,
    make_migrations_cmd,
)
from jetbase.constants import MIGRATIONS_DIR


@pytest.fixture
def sample_model_file(tmp_path):
    """Create a temporary model file with SQLAlchemy models."""
    model_content = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
"""
    model_path = tmp_path / "models.py"
    model_path.write_text(model_content)
    return str(model_path)


@pytest.fixture
def migrations_dir(tmp_path):
    """Create a temporary migrations directory."""
    migrations_dir = tmp_path / MIGRATIONS_DIR
    migrations_dir.mkdir()
    return migrations_dir


class TestMakeMigrationsCmd:
    """Tests for make_migrations_cmd function."""

    def test_make_migrations_model_paths_not_set(self, tmp_path, migrations_dir):
        """Test error when JETBASE_MODELS is not set."""
        os.chdir(tmp_path)

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MakeMigrationsError) as exc_info:
                make_migrations_cmd()

            assert "JETBASE_MODELS" in str(exc_info.value)

    def test_make_migrations_model_file_not_found(self, tmp_path, migrations_dir):
        """Test error when model file path doesn't exist."""
        os.chdir(tmp_path)

        with patch.dict(os.environ, {"JETBASE_MODELS": "./nonexistent/models.py"}):
            with pytest.raises(MakeMigrationsError) as exc_info:
                make_migrations_cmd()

            assert "not found" in str(exc_info.value).lower()


class TestMakeMigrationsError:
    """Tests for MakeMigrationsError exception."""

    def test_make_migrations_error(self):
        """Test MakeMigrationsError can be raised."""
        with pytest.raises(MakeMigrationsError):
            raise MakeMigrationsError("Test error message")
