"""Configuration management system for Doorman CLI."""

import json
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


class ConfigScope(Enum):
    """Configuration scope levels."""

    GLOBAL = "global"
    PROJECT = "project"
    SESSION = "session"


@dataclass
class DoormanConfig:
    """Main configuration structure."""

    # API Settings
    openrouter_api_key: Optional[str] = None
    api_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-3.5-turbo"
    fallback_model: str = "openai/gpt-3.5-turbo"

    # CLI Behavior
    auto_confirm_safe: bool = True
    auto_confirm_moderate: bool = False
    auto_confirm_dangerous: bool = False
    interactive_mode: bool = True
    verbose: bool = False
    debug: bool = False

    # Output Settings
    theme: str = "cyberpunk"
    output_format: str = "rich"  # rich, json, plain
    show_token_usage: bool = True
    show_cost_estimates: bool = True

    # Safety & Permissions
    allowed_tools: List[str] = None
    disallowed_tools: List[str] = None
    max_cost_per_plan: float = 1.0  # USD
    require_confirmation_over: float = 0.10  # USD

    # Session Management
    save_sessions: bool = True
    max_saved_sessions: int = 50
    session_timeout_hours: int = 24

    # Billing
    subscription_tier: str = "free"
    usage_tracking: bool = True
    cost_alerts: bool = True

    def __post_init__(self):
        if self.allowed_tools is None:
            self.allowed_tools = []
        if self.disallowed_tools is None:
            self.disallowed_tools = []


class ConfigManager:
    """Manages Doorman configuration with multiple scopes and persistence."""

    def __init__(self):
        self.global_config_dir = Path.home() / ".config" / "doorman"
        self.global_config_file = self.global_config_dir / "config.json"
        self.project_config_file = Path.cwd() / ".doorman" / "config.json"
        self.session_dir = self.global_config_dir / "sessions"

        # Ensure directories exist
        self.global_config_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(exist_ok=True)

        # Load configuration
        self._config_cache = {}
        self.reload()

    def reload(self):
        """Reload configuration from all sources."""
        self._config_cache = {
            ConfigScope.GLOBAL: self._load_config(self.global_config_file),
            ConfigScope.PROJECT: self._load_config(self.project_config_file),
            ConfigScope.SESSION: {},  # Loaded dynamically
        }

    def _load_config(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a JSON file."""
        if not file_path.exists():
            return {}

        try:
            with open(file_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            console.print(
                f"[yellow]Warning: Failed to load config from {file_path}: {e}[/yellow]"
            )
            return {}

    def _save_config(self, file_path: Path, config: Dict[str, Any]):
        """Save configuration to a JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2, sort_keys=True)
        except OSError as e:
            console.print(
                f"[red]Error: Failed to save config to {file_path}: {e}[/red]"
            )
            raise

    def get_merged_config(self) -> DoormanConfig:
        """Get merged configuration from all scopes (global < project < session < env)."""
        # Start with defaults
        config_dict = {}

        # Merge global config
        config_dict.update(self._config_cache[ConfigScope.GLOBAL])

        # Merge project config (overrides global)
        config_dict.update(self._config_cache[ConfigScope.PROJECT])

        # Environment variables override everything
        env_overrides = self._get_env_overrides()
        config_dict.update(env_overrides)

        # Create DoormanConfig instance
        return DoormanConfig(
            **{
                k: v
                for k, v in config_dict.items()
                if k in DoormanConfig.__dataclass_fields__
            }
        )

    def _get_env_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        env_map = {
            "OPENROUTER_API_KEY": "openrouter_api_key",
            "DOORMAN_MODEL": "default_model",
            "DOORMAN_VERBOSE": "verbose",
            "DOORMAN_DEBUG": "debug",
            "DOORMAN_THEME": "theme",
            "DOORMAN_AUTO_CONFIRM": "auto_confirm_safe",
        }

        overrides = {}
        for env_key, config_key in env_map.items():
            value = os.getenv(env_key)
            if value is not None:
                # Type conversion
                if config_key in ["verbose", "debug", "auto_confirm_safe"]:
                    overrides[config_key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    overrides[config_key] = value

        return overrides

    def get(self, key: str, scope: Optional[ConfigScope] = None) -> Any:
        """Get a configuration value."""
        if scope:
            return self._config_cache[scope].get(key)
        else:
            # Return from merged config
            config = self.get_merged_config()
            return getattr(config, key, None)

    def set(
        self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL
    ) -> None:
        """Set a configuration value."""
        # Validate key exists in DoormanConfig
        if key not in DoormanConfig.__dataclass_fields__:
            raise ValueError(f"Unknown configuration key: {key}")

        # Update cache
        self._config_cache[scope][key] = value

        # Save to appropriate file
        if scope == ConfigScope.GLOBAL:
            self._save_config(self.global_config_file, self._config_cache[scope])
        elif scope == ConfigScope.PROJECT:
            self._save_config(self.project_config_file, self._config_cache[scope])

        console.print(f"[green]✓[/green] Set {key} = {value} ({scope.value} scope)")

    def remove(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL) -> None:
        """Remove a configuration value."""
        if key in self._config_cache[scope]:
            del self._config_cache[scope][key]

            # Save updated config
            if scope == ConfigScope.GLOBAL:
                self._save_config(self.global_config_file, self._config_cache[scope])
            elif scope == ConfigScope.PROJECT:
                self._save_config(self.project_config_file, self._config_cache[scope])

            console.print(f"[green]✓[/green] Removed {key} from {scope.value} scope")
        else:
            console.print(
                f"[yellow]Key '{key}' not found in {scope.value} scope[/yellow]"
            )

    def list_config(
        self, scope: Optional[ConfigScope] = None, show_all: bool = False
    ) -> None:
        """Display configuration values."""
        if scope:
            config_dict = self._config_cache[scope]
            title = f"{scope.value.title()} Configuration"
        else:
            config = self.get_merged_config()
            config_dict = asdict(config)
            title = "Merged Configuration"

        if not config_dict and not show_all:
            console.print(
                f"[yellow]No configuration set for {scope.value if scope else 'merged'} scope[/yellow]"
            )
            return

        table = Table(title=title)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Source", style="dim")

        # Show all possible keys if show_all is True
        if show_all and not scope:
            config = self.get_merged_config()
            for key in DoormanConfig.__dataclass_fields__:
                value = getattr(config, key)
                source = self._get_value_source(key)
                table.add_row(key, str(value), source)
        else:
            for key, value in sorted(config_dict.items()):
                source = scope.value if scope else self._get_value_source(key)
                table.add_row(key, str(value), source)

        console.print(table)

    def _get_value_source(self, key: str) -> str:
        """Determine where a configuration value comes from."""
        if os.getenv(f"DOORMAN_{key.upper()}") or os.getenv(
            f"OPENROUTER_{key.upper()}"
        ):
            return "environment"
        elif key in self._config_cache[ConfigScope.PROJECT]:
            return "project"
        elif key in self._config_cache[ConfigScope.GLOBAL]:
            return "global"
        else:
            return "default"

    def validate_config(self) -> List[str]:
        """Validate current configuration and return any issues."""
        issues = []
        config = self.get_merged_config()

        # Check API key
        if not config.openrouter_api_key:
            issues.append(
                "No OpenRouter API key configured. Set with: doorman config set openrouter_api_key YOUR_KEY"
            )

        # Check model availability
        if not config.default_model.startswith(
            ("openai/", "anthropic/", "meta-llama/", "google/")
        ):
            issues.append(
                f"Default model '{config.default_model}' may not be available on OpenRouter"
            )

        # Check cost limits
        if config.max_cost_per_plan <= 0:
            issues.append("Max cost per plan must be positive")

        # Check directories exist and are writable
        try:
            test_file = self.global_config_dir / ".test"
            test_file.touch()
            test_file.unlink()
        except OSError:
            issues.append(f"Cannot write to config directory: {self.global_config_dir}")

        return issues

    def reset_to_defaults(self, scope: ConfigScope = ConfigScope.GLOBAL) -> None:
        """Reset configuration to defaults."""
        if scope == ConfigScope.GLOBAL:
            if self.global_config_file.exists():
                self.global_config_file.unlink()
            console.print("[green]✓[/green] Reset global configuration to defaults")
        elif scope == ConfigScope.PROJECT:
            if self.project_config_file.exists():
                self.project_config_file.unlink()
            console.print("[green]✓[/green] Reset project configuration to defaults")

        self.reload()

    def export_config(
        self, file_path: Path, scope: Optional[ConfigScope] = None
    ) -> None:
        """Export configuration to a file."""
        if scope:
            config_data = self._config_cache[scope]
        else:
            config = self.get_merged_config()
            config_data = asdict(config)

        try:
            with open(file_path, "w") as f:
                json.dump(config_data, f, indent=2, sort_keys=True)
            console.print(f"[green]✓[/green] Exported configuration to {file_path}")
        except OSError as e:
            console.print(f"[red]Error exporting config: {e}[/red]")

    def import_config(
        self, file_path: Path, scope: ConfigScope = ConfigScope.GLOBAL
    ) -> None:
        """Import configuration from a file."""
        try:
            with open(file_path) as f:
                config_data = json.load(f)

            # Validate keys
            valid_keys = set(DoormanConfig.__dataclass_fields__.keys())
            invalid_keys = set(config_data.keys()) - valid_keys

            if invalid_keys:
                console.print(
                    f"[yellow]Warning: Ignoring invalid keys: {', '.join(invalid_keys)}[/yellow]"
                )
                config_data = {k: v for k, v in config_data.items() if k in valid_keys}

            # Update cache and save
            self._config_cache[scope].update(config_data)

            if scope == ConfigScope.GLOBAL:
                self._save_config(self.global_config_file, self._config_cache[scope])
            elif scope == ConfigScope.PROJECT:
                self._save_config(self.project_config_file, self._config_cache[scope])

            console.print(f"[green]✓[/green] Imported configuration from {file_path}")

        except (OSError, json.JSONDecodeError) as e:
            console.print(f"[red]Error importing config: {e}[/red]")


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> DoormanConfig:
    """Get the current merged configuration."""
    return get_config_manager().get_merged_config()
