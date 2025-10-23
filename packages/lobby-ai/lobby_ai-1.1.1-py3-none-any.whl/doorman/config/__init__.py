"""Configuration management for Doorman."""

from pathlib import Path

from .manager import (
    ConfigManager,
    ConfigScope,
    DoormanConfig,
    get_config,
    get_config_manager,
)

__all__ = [
    "ConfigManager",
    "ConfigScope",
    "DoormanConfig",
    "get_config_manager",
    "get_config",
    "get_config_dir",
]


def get_config_dir() -> Path:
    """Get the configuration directory."""
    return Path.home() / ".config" / "doorman"
