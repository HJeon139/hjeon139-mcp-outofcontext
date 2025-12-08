"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from hjeon139_mcp_outofcontext.config import Config, load_config


@pytest.mark.unit
class TestConfig:
    """Test Config dataclass."""

    def test_config_defaults(self) -> None:
        """Test config with default values."""
        config = Config()
        assert config.storage_path == ".out_of_context"
        assert config.token_limit == 1000000
        assert config.model == "gpt-4"
        assert config.log_level == "INFO"
        assert config.max_active_segments == 10000
        assert config.enable_indexing is True
        assert config.enable_file_sharding is True

    def test_config_to_dict(self) -> None:
        """Test config to_dict conversion."""
        config = Config(storage_path="/test/path", model="gpt-3.5-turbo")
        config_dict = config.to_dict()
        assert config_dict["storage_path"] == "/test/path"
        assert config_dict["model"] == "gpt-3.5-turbo"
        assert isinstance(config_dict, dict)


@pytest.mark.unit
class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_defaults(self) -> None:
        """Test loading config with defaults."""
        # Clear environment variables
        env_vars = [
            "OUT_OF_CONTEXT_STORAGE_PATH",
            "OUT_OF_CONTEXT_TOKEN_LIMIT",
            "OUT_OF_CONTEXT_MODEL",
            "OUT_OF_CONTEXT_LOG_LEVEL",
        ]
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            config = load_config()
            # Default storage path is .out_of_context in project directory
            assert config.storage_path == ".out_of_context"
            assert config.model == "gpt-4"
            assert config.log_level == "INFO"
        finally:
            # Restore environment variables
            for var, value in original_values.items():
                if value is not None:
                    os.environ[var] = value

    def test_load_config_from_env(self) -> None:
        """Test loading config from environment variables."""
        # Save original values
        original_storage = os.environ.get("OUT_OF_CONTEXT_STORAGE_PATH")
        original_model = os.environ.get("OUT_OF_CONTEXT_MODEL")

        try:
            # Set environment variables
            os.environ["OUT_OF_CONTEXT_STORAGE_PATH"] = "/test/storage"
            os.environ["OUT_OF_CONTEXT_MODEL"] = "gpt-3.5-turbo"

            config = load_config()
            # Storage path should be expanded
            assert "/test/storage" in config.storage_path
            assert config.model == "gpt-3.5-turbo"
        finally:
            # Restore original values
            if original_storage:
                os.environ["OUT_OF_CONTEXT_STORAGE_PATH"] = original_storage
            elif "OUT_OF_CONTEXT_STORAGE_PATH" in os.environ:
                del os.environ["OUT_OF_CONTEXT_STORAGE_PATH"]

            if original_model:
                os.environ["OUT_OF_CONTEXT_MODEL"] = original_model
            elif "OUT_OF_CONTEXT_MODEL" in os.environ:
                del os.environ["OUT_OF_CONTEXT_MODEL"]

    def test_load_config_from_file(self) -> None:
        """Test loading config from config file."""
        # Create temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".out_of_context"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            config_data = {
                "storage_path": str(config_dir),
                "model": "gpt-3.5-turbo",
                "log_level": "DEBUG",
            }

            import json

            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Save original HOME
            original_home = os.environ.get("HOME")
            original_storage = os.environ.get("OUT_OF_CONTEXT_STORAGE_PATH")

            try:
                # Temporarily set HOME to tmpdir
                os.environ["HOME"] = tmpdir
                if "OUT_OF_CONTEXT_STORAGE_PATH" in os.environ:
                    del os.environ["OUT_OF_CONTEXT_STORAGE_PATH"]

                config = load_config()
                assert config.model == "gpt-3.5-turbo"
                assert config.log_level == "DEBUG"
            finally:
                # Restore original values
                if original_home:
                    os.environ["HOME"] = original_home
                if original_storage:
                    os.environ["OUT_OF_CONTEXT_STORAGE_PATH"] = original_storage

    def test_load_config_env_overrides_file(self) -> None:
        """Test that environment variables override config file."""
        # Create temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".out_of_context"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            config_data = {"model": "gpt-3.5-turbo"}

            import json

            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Save original values
            original_home = os.environ.get("HOME")
            original_model = os.environ.get("OUT_OF_CONTEXT_MODEL")

            try:
                # Set environment variable
                os.environ["HOME"] = tmpdir
                os.environ["OUT_OF_CONTEXT_MODEL"] = "gpt-4"

                config = load_config()
                # Environment variable should override config file
                assert config.model == "gpt-4"
            finally:
                # Restore original values
                if original_home:
                    os.environ["HOME"] = original_home
                if original_model:
                    os.environ["OUT_OF_CONTEXT_MODEL"] = original_model
                elif "OUT_OF_CONTEXT_MODEL" in os.environ:
                    del os.environ["OUT_OF_CONTEXT_MODEL"]
