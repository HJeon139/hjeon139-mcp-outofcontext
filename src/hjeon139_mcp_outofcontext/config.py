"""Configuration management for MCP server."""

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Config:
    """Configuration for MCP server."""

    storage_path: str = ".out_of_context"
    token_limit: int = 1000000  # Millions of tokens
    model: str = "gpt-4"
    log_level: str = "INFO"
    max_active_segments: int = 10000  # LRU cache size
    enable_indexing: bool = True  # Enable inverted index
    enable_file_sharding: bool = True  # Enable file sharding
    recent_messages_count: int = 10
    recent_decision_hours: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "storage_path": self.storage_path,
            "token_limit": self.token_limit,
            "model": self.model,
            "log_level": self.log_level,
            "max_active_segments": self.max_active_segments,
            "enable_indexing": self.enable_indexing,
            "enable_file_sharding": self.enable_file_sharding,
            "recent_messages_count": self.recent_messages_count,
            "recent_decision_hours": self.recent_decision_hours,
        }


Converter = Callable[[str], Any]
EnvMapping = dict[str, str | tuple[str, Converter]]


def load_config() -> Config:
    """Load configuration from environment variables, config file, and defaults.

    Priority:
    1. Environment variables (highest priority)
    2. Config file (.out_of_context/config.json or ~/.out_of_context/config.json)
    3. Default values (lowest priority)

    Returns:
        Config instance with loaded values
    """
    # Start with defaults
    config_dict: dict[str, Any] = {}

    # Load from config file if it exists (check project directory first, then home)
    config_file = Path(".out_of_context") / "config.json"
    if not config_file.exists():
        config_file = Path.home() / ".out_of_context" / "config.json"
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
                config_dict.update(file_config)
        except (OSError, json.JSONDecodeError) as e:
            # Log warning but continue with defaults/env vars
            print(f"Warning: Could not load config file {config_file}: {e}")

    # Override with environment variables (highest priority)
    env_mappings: EnvMapping = {
        "OUT_OF_CONTEXT_STORAGE_PATH": "storage_path",
        "OUT_OF_CONTEXT_TOKEN_LIMIT": ("token_limit", int),
        "OUT_OF_CONTEXT_MODEL": "model",
        "OUT_OF_CONTEXT_LOG_LEVEL": "log_level",
        "OUT_OF_CONTEXT_MAX_ACTIVE_SEGMENTS": ("max_active_segments", int),
        "OUT_OF_CONTEXT_ENABLE_INDEXING": ("enable_indexing", lambda x: x.lower() == "true"),
        "OUT_OF_CONTEXT_ENABLE_FILE_SHARDING": (
            "enable_file_sharding",
            lambda x: x.lower() == "true",
        ),
        "OUT_OF_CONTEXT_RECENT_MESSAGES_COUNT": ("recent_messages_count", int),
        "OUT_OF_CONTEXT_RECENT_DECISION_HOURS": ("recent_decision_hours", int),
    }

    for env_var, mapping in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            if isinstance(mapping, tuple):
                key, converter = mapping
                try:
                    config_dict[key] = converter(value)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid value for {env_var}: {value}")
            else:
                config_dict[mapping] = value

    # Expand ~ in storage_path
    if "storage_path" in config_dict:
        config_dict["storage_path"] = os.path.expanduser(config_dict["storage_path"])

    # Create Config instance with defaults and overrides
    return Config(**config_dict)
