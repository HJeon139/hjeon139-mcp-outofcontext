"""Configuration management for MCP server."""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for MCP server."""

    storage_path: str = "out_of_context"
    log_level: str = "INFO"

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "storage_path": self.storage_path,
            "log_level": self.log_level,
        }


Converter = Callable[[str], Any]
EnvMapping = dict[str, str | tuple[str, Converter]]


def migrate_old_storage_directory() -> None:
    """Migrate old .out_of_context directory to new out_of_context directory.

    This function checks if the old hidden directory exists and migrates it
    to the new non-hidden directory. This prevents permission issues when
    agents try to edit context files directly.

    The migration is idempotent - it only runs once per installation.
    """
    # Use absolute paths to avoid issues with working directory
    old_path = Path.cwd() / ".out_of_context"
    new_path = Path.cwd() / "out_of_context"
    migration_marker = new_path / ".migration_complete"

    # Check if migration already completed
    if migration_marker.exists():
        return

    # Only migrate if old path exists and new path doesn't
    if old_path.exists() and not new_path.exists():
        try:
            import shutil

            # Move the entire directory
            shutil.move(str(old_path), str(new_path))

            # Verify migration succeeded
            if new_path.exists() and (new_path / "contexts").exists():
                # Create marker file to indicate migration completed
                migration_marker.touch()
                logger.info(f"Migrated storage directory from {old_path} to {new_path}")
            else:
                logger.error(f"Migration verification failed: {new_path} or contexts/ not found")
        except Exception as e:
            logger.warning(f"Failed to migrate storage directory: {e}")
    elif old_path.exists() and new_path.exists() and not migration_marker.exists():
        # Both exist - log warning but use new one
        # Create marker to prevent repeated warnings
        logger.warning(
            f"Both {old_path} and {new_path} exist. "
            f"Using {new_path}. Please manually merge if needed."
        )
        migration_marker.touch()


def load_config() -> Config:  # noqa: C901
    """Load configuration from environment variables, config file, and defaults.

    Priority:
    1. Environment variables (highest priority)
    2. Config file (out_of_context/config.json or ~/out_of_context/config.json)
    3. Default values (lowest priority)

    Returns:
        Config instance with loaded values
    """
    # Start with defaults
    config_dict: dict[str, Any] = {}

    # Load from config file if it exists (check project directory first, then home)
    config_file = Path("out_of_context") / "config.json"
    if not config_file.exists():
        config_file = Path.home() / "out_of_context" / "config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
                config_dict.update(file_config)
        except (OSError, json.JSONDecodeError) as e:
            # Log warning but continue with defaults/env vars
            logger.warning(f"Could not load config file {config_file}: {e}")

    # Override with environment variables (highest priority)
    env_mappings: EnvMapping = {
        "OUT_OF_CONTEXT_STORAGE_PATH": "storage_path",
        "OUT_OF_CONTEXT_LOG_LEVEL": "log_level",
    }

    for env_var, mapping in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            if isinstance(mapping, tuple):
                key, converter = mapping
                try:
                    config_dict[key] = converter(value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for {env_var}: {value}")
            else:
                config_dict[mapping] = value

    # Expand ~ in storage_path
    if "storage_path" in config_dict:
        config_dict["storage_path"] = os.path.expanduser(config_dict["storage_path"])

    # Warn if using old hidden directory path
    storage_path = config_dict.get("storage_path", "out_of_context")
    # Use Path to handle all path formats (relative, absolute, Windows, Unix)
    try:
        storage_path_obj = Path(storage_path).resolve()
        if storage_path_obj.name == ".out_of_context":
            logger.warning(
                "⚠️  WARNING: You are using the old hidden directory path '.out_of_context'.\n"
                "   This may cause permission issues when agents try to edit context files.\n"
                "   Please update your configuration to use 'out_of_context' instead.\n"
                "   See CHANGELOG.md for migration instructions."
            )
    except (OSError, ValueError):
        # Path resolution failed, fall back to string comparison
        if (
            storage_path == ".out_of_context"
            or storage_path.endswith("/.out_of_context")
            or storage_path.endswith("\\.out_of_context")
        ):
            logger.warning(
                "⚠️  WARNING: You are using the old hidden directory path '.out_of_context'.\n"
                "   This may cause permission issues when agents try to edit context files.\n"
                "   Please update your configuration to use 'out_of_context' instead.\n"
                "   See CHANGELOG.md for migration instructions."
            )

    # Create Config instance with defaults and overrides
    return Config(**config_dict)
