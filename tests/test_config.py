"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from hjeon139_mcp_outofcontext.config import Config, load_config


@pytest.mark.unit
class TestConfig:
    """Test Config dataclass."""

    def test_config_defaults(self) -> None:
        """Test config with default values."""
        config = Config()
        assert config.storage_path == "out_of_context"
        assert config.log_level == "INFO"

    def test_config_to_dict(self) -> None:
        """Test config to_dict conversion."""
        config = Config(storage_path="/test/path", log_level="DEBUG")
        config_dict = config.to_dict()
        assert config_dict["storage_path"] == "/test/path"
        assert config_dict["log_level"] == "DEBUG"
        assert isinstance(config_dict, dict)


@pytest.mark.unit
class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_defaults(self) -> None:
        """Test loading config with defaults."""
        # Clear environment variables
        env_vars = [
            "OUT_OF_CONTEXT_STORAGE_PATH",
            "OUT_OF_CONTEXT_LOG_LEVEL",
        ]
        original_values = {}
        for var in env_vars:
            original_values[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        try:
            config = load_config()
            # Default storage path is out_of_context in project directory
            assert config.storage_path == "out_of_context"
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
        original_log_level = os.environ.get("OUT_OF_CONTEXT_LOG_LEVEL")

        try:
            # Set environment variables
            os.environ["OUT_OF_CONTEXT_STORAGE_PATH"] = "/test/storage"
            os.environ["OUT_OF_CONTEXT_LOG_LEVEL"] = "DEBUG"

            config = load_config()
            # Storage path should be expanded
            assert "/test/storage" in config.storage_path
            assert config.log_level == "DEBUG"
        finally:
            # Restore original values
            if original_storage:
                os.environ["OUT_OF_CONTEXT_STORAGE_PATH"] = original_storage
            elif "OUT_OF_CONTEXT_STORAGE_PATH" in os.environ:
                del os.environ["OUT_OF_CONTEXT_STORAGE_PATH"]

            if original_log_level:
                os.environ["OUT_OF_CONTEXT_LOG_LEVEL"] = original_log_level
            elif "OUT_OF_CONTEXT_LOG_LEVEL" in os.environ:
                del os.environ["OUT_OF_CONTEXT_LOG_LEVEL"]

    def test_load_config_from_file(self) -> None:
        """Test loading config from config file."""
        # Create temporary config file
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "out_of_context"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            config_data = {
                "storage_path": str(config_dir),
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
            config_dir = Path(tmpdir) / "out_of_context"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            config_data = {"log_level": "WARNING"}

            import json

            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Save original values
            original_home = os.environ.get("HOME")
            original_log_level = os.environ.get("OUT_OF_CONTEXT_LOG_LEVEL")

            try:
                # Set environment variable
                os.environ["HOME"] = tmpdir
                os.environ["OUT_OF_CONTEXT_LOG_LEVEL"] = "DEBUG"

                config = load_config()
                # Environment variable should override config file
                assert config.log_level == "DEBUG"
            finally:
                # Restore original values
                if original_home:
                    os.environ["HOME"] = original_home
                if original_log_level:
                    os.environ["OUT_OF_CONTEXT_LOG_LEVEL"] = original_log_level
                elif "OUT_OF_CONTEXT_LOG_LEVEL" in os.environ:
                    del os.environ["OUT_OF_CONTEXT_LOG_LEVEL"]

    def test_load_config_file_error_handling(self, tmp_path) -> None:
        """Test that invalid config file is handled gracefully."""

        # Create invalid JSON config file
        config_dir = Path(tmp_path) / "out_of_context"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"

        with open(config_file, "w") as f:
            f.write("{ invalid json }")

        # Save original HOME and CWD
        original_home = os.environ.get("HOME")
        original_cwd = os.getcwd()

        try:
            os.environ["HOME"] = str(tmp_path)
            os.chdir(tmp_path)

            # Should not raise, just print warning and continue with defaults
            config = load_config()
            assert config.storage_path == "out_of_context"
            assert config.log_level == "INFO"
        finally:
            if original_home:
                os.environ["HOME"] = original_home
            os.chdir(original_cwd)

    def test_load_config_file_os_error_handling(self, tmp_path) -> None:
        """Test that OS errors when reading config file are handled gracefully."""

        config_dir = Path(tmp_path) / "out_of_context"
        config_dir.mkdir(exist_ok=True)

        # Save original HOME and CWD
        original_home = os.environ.get("HOME")
        original_cwd = os.getcwd()

        try:
            os.environ["HOME"] = str(tmp_path)
            os.chdir(tmp_path)

            # Mock open to raise OSError
            with patch("builtins.open", side_effect=OSError("Permission denied")):
                # Should not raise, just print warning and continue with defaults
                config = load_config()
                assert config.storage_path == "out_of_context"
                assert config.log_level == "INFO"
        finally:
            if original_home:
                os.environ["HOME"] = original_home
            os.chdir(original_cwd)

    def test_migrate_old_storage_directory(self, tmp_path) -> None:
        """Test migration from .out_of_context to out_of_context."""
        from hjeon139_mcp_outofcontext.config import migrate_old_storage_directory

        original_cwd = os.getcwd()

        try:
            os.chdir(tmp_path)

            # Create old directory with some content
            old_path = Path(".out_of_context")
            old_path.mkdir()
            (old_path / "contexts").mkdir()
            (old_path / "contexts" / "test.mdc").write_text("test content")
            (old_path / "config.json").write_text('{"storage_path": ".out_of_context"}')

            # Run migration
            migrate_old_storage_directory()

            # Verify new directory exists with content
            new_path = Path("out_of_context")
            assert new_path.exists()
            assert (new_path / "contexts" / "test.mdc").exists()
            assert (new_path / "config.json").exists()
            assert not old_path.exists()  # Old directory should be gone
            assert (new_path / ".migration_complete").exists()  # Marker file created

            # Run migration again - should be idempotent
            migrate_old_storage_directory()
            # Should still have same state
            assert new_path.exists()
            assert not old_path.exists()

        finally:
            os.chdir(original_cwd)

    def test_migrate_old_storage_directory_no_old_dir(self, tmp_path) -> None:
        """Test migration when old directory doesn't exist."""
        from hjeon139_mcp_outofcontext.config import migrate_old_storage_directory

        original_cwd = os.getcwd()

        try:
            os.chdir(tmp_path)

            # Run migration when old directory doesn't exist
            migrate_old_storage_directory()

            # Should not create new directory if old doesn't exist
            new_path = Path("out_of_context")
            assert not new_path.exists()

        finally:
            os.chdir(original_cwd)

    def test_migrate_old_storage_directory_both_exist(self, tmp_path) -> None:
        """Test migration when both old and new directories exist."""
        from hjeon139_mcp_outofcontext.config import migrate_old_storage_directory

        original_cwd = os.getcwd()

        try:
            os.chdir(tmp_path)

            # Create both directories
            old_path = Path(".out_of_context")
            old_path.mkdir()
            (old_path / "contexts").mkdir()
            (old_path / "contexts" / "old.mdc").write_text("old content")

            new_path = Path("out_of_context")
            new_path.mkdir()
            (new_path / "contexts").mkdir()
            (new_path / "contexts" / "new.mdc").write_text("new content")

            # Run migration
            migrate_old_storage_directory()

            # Both should still exist (no migration)
            assert old_path.exists()
            assert new_path.exists()
            assert (old_path / "contexts" / "old.mdc").exists()
            assert (new_path / "contexts" / "new.mdc").exists()
            # Marker should be created to prevent repeated warnings
            assert (new_path / ".migration_complete").exists()

        finally:
            os.chdir(original_cwd)
