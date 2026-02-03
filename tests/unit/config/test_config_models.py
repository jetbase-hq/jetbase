import os
from unittest.mock import patch

import pytest

from jetbase.config import (
    JetbaseConfig,
    _get_config_from_env_var,
    get_config,
)


class TestJetbaseConfigModelPaths:
    """Tests for model_paths configuration."""

    def test_jetbase_config_with_model_paths(self):
        """Test JetbaseConfig with model_paths."""
        config = JetbaseConfig(
            sqlalchemy_url="postgresql://localhost/testdb",
            model_paths=["./models/user.py", "./models/product.py"],
        )

        assert config.model_paths == ["./models/user.py", "./models/product.py"]

    def test_jetbase_config_without_model_paths(self):
        """Test JetbaseConfig without model_paths defaults to None."""
        config = JetbaseConfig(
            sqlalchemy_url="postgresql://localhost/testdb",
        )

        assert config.model_paths is None

    def test_jetbase_config_with_empty_model_paths(self):
        """Test JetbaseConfig with empty model_paths list."""
        config = JetbaseConfig(
            sqlalchemy_url="postgresql://localhost/testdb",
            model_paths=[],
        )

        assert config.model_paths == []


class TestGetConfigFromEnvVar:
    """Tests for _get_config_from_env_var with model_paths."""

    def test_model_paths_env_var_single_path(self):
        """Test parsing single model path from env var."""
        with patch.dict(os.environ, {"JETBASE_MODEL_PATHS": "./models.py"}):
            result = _get_config_from_env_var("model_paths")

            assert result == ["./models.py"]

    def test_model_paths_env_var_multiple_paths(self):
        """Test parsing multiple model paths from env var."""
        with patch.dict(
            os.environ,
            {
                "JETBASE_MODEL_PATHS": "./models/user.py,./models/product.py,./models/order.py"
            },
        ):
            result = _get_config_from_env_var("model_paths")

            assert result == [
                "./models/user.py",
                "./models/product.py",
                "./models/order.py",
            ]

    def test_model_paths_env_var_with_spaces(self):
        """Test parsing model paths with spaces around paths."""
        with patch.dict(
            os.environ,
            {"JETBASE_MODEL_PATHS": " ./models/user.py , ./models/product.py "},
        ):
            result = _get_config_from_env_var("model_paths")

            assert result == ["./models/user.py", "./models/product.py"]

    def test_model_paths_env_var_empty(self):
        """Test parsing empty model paths from env var."""
        with patch.dict(os.environ, {"JETBASE_MODEL_PATHS": ""}):
            result = _get_config_from_env_var("model_paths")

            assert result is None

    def test_model_paths_env_var_whitespace_only(self):
        """Test parsing whitespace-only model paths from env var."""
        with patch.dict(os.environ, {"JETBASE_MODEL_PATHS": "   ,   "}):
            result = _get_config_from_env_var("model_paths")

            assert result is None

    def test_model_paths_env_var_not_set(self):
        """Test model_paths returns None when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_config_from_env_var("model_paths")

            assert result is None


class TestGetConfig:
    """Tests for get_config with model_paths."""

    def test_get_config_with_model_paths(self):
        """Test get_config loads model_paths from env var."""
        with patch.dict(
            os.environ, {"JETBASE_MODEL_PATHS": "./models/user.py,./models/product.py"}
        ):
            config = get_config()

            assert config.model_paths == ["./models/user.py", "./models/product.py"]

    def test_get_config_model_paths_not_in_env(self):
        """Test get_config returns None for model_paths when not in env."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()

            assert config.model_paths is None

    def test_get_config_boolean_still_works(self):
        """Test that boolean config values still work."""
        with patch.dict(os.environ, {"JETBASE_SKIP_VALIDATION": "true"}):
            config = get_config()

            assert config.skip_validation is True

    def test_get_config_boolean_false(self):
        """Test that boolean false config values work."""
        with patch.dict(os.environ, {"JETBASE_SKIP_VALIDATION": "false"}):
            config = get_config()

            assert config.skip_validation is False
