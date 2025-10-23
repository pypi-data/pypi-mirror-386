"""Plugin architecture and management system for Doorman."""

import asyncio
import importlib
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import toml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    """Plugin manifest from plugin.toml file."""

    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # "agent", "tool", "billing_provider"
    entry_point: str
    permissions: List[str] = None
    sprite_config: Dict[str, Any] = None
    dependencies: List[str] = None
    min_doorman_version: str = "0.1.0"
    max_doorman_version: str = "999.0.0"


class PluginConfig(BaseModel):
    """Configuration for plugin system."""

    plugins_dir: Path = Field(
        default_factory=lambda: Path.home() / ".doorman" / "plugins"
    )
    sandbox_timeout: int = 30
    max_memory_mb: int = 256
    allow_network: bool = False
    allow_filesystem: bool = False
    enable_sandboxing: bool = False


class AgentPlugin:
    """Base class for agent plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        raise NotImplementedError

    def get_required_tools(self) -> List[str]:
        """Return list of required tools."""
        return []

    def get_sprite_config(self) -> Optional[Dict[str, Any]]:
        """Return sprite configuration."""
        return None

    async def process_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task with this agent."""
        raise NotImplementedError


class ToolPlugin:
    """Base class for tool plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return MCP-compatible tool definition."""
        raise NotImplementedError

    async def call_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        raise NotImplementedError


class BillingProviderPlugin:
    """Base class for billing provider plugins."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider information."""
        raise NotImplementedError

    async def validate_subscription(
        self, user_id: str, license_key: str
    ) -> Dict[str, Any]:
        """Validate user subscription."""
        raise NotImplementedError


@dataclass
class LoadedPlugin:
    """Represents a loaded plugin."""

    manifest: PluginManifest
    plugin_instance: Union[AgentPlugin, ToolPlugin, BillingProviderPlugin]
    loaded_at: datetime
    is_active: bool = True
    error_count: int = 0


class PluginManager:
    """Manages plugin loading, execution, and lifecycle."""

    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
        self.config.plugins_dir.mkdir(parents=True, exist_ok=True)

        self._loaded_plugins: Dict[str, LoadedPlugin] = {}
        self._plugin_types: Dict[str, Type] = {
            "agent": AgentPlugin,
            "tool": ToolPlugin,
            "billing_provider": BillingProviderPlugin,
        }

    def discover_plugins(self) -> List[Path]:
        """Discover all plugin directories."""
        plugin_dirs = []

        # Look for plugins in standard locations
        search_locations = [
            self.config.plugins_dir,
            Path.cwd() / "plugins",
            Path(__file__).parent / "bundled",
        ]

        for location in search_locations:
            if location.exists():
                # Look for plugin.toml files
                for plugin_file in location.rglob("plugin.toml"):
                    plugin_dirs.append(plugin_file.parent)

        # Also check Python entry points
        try:
            import pkg_resources

            for entry_point in pkg_resources.iter_entry_points("doorman.plugins"):
                try:
                    module = entry_point.load()
                    if hasattr(module, "__file__"):
                        plugin_dirs.append(Path(module.__file__).parent)
                except Exception as e:
                    logger.warning(
                        f"Failed to load entry point {entry_point.name}: {e}"
                    )
        except ImportError:
            pass  # pkg_resources not available

        return list(set(plugin_dirs))  # Remove duplicates

    def load_plugin_manifest(self, plugin_dir: Path) -> Optional[PluginManifest]:
        """Load plugin manifest from plugin.toml."""
        manifest_file = plugin_dir / "plugin.toml"

        if not manifest_file.exists():
            return None

        try:
            data = toml.load(manifest_file)
            plugin_data = data.get("plugin", {})

            return PluginManifest(
                name=plugin_data["name"],
                version=plugin_data["version"],
                description=plugin_data.get("description", ""),
                author=plugin_data.get("author", "Unknown"),
                plugin_type=plugin_data["type"],
                entry_point=plugin_data["entry_point"],
                permissions=plugin_data.get("permissions", []),
                sprite_config=plugin_data.get("sprite", {}),
                dependencies=plugin_data.get("dependencies", []),
                min_doorman_version=plugin_data.get("min_doorman_version", "0.1.0"),
                max_doorman_version=plugin_data.get("max_doorman_version", "999.0.0"),
            )

        except Exception as e:
            logger.error(f"Failed to load plugin manifest from {manifest_file}: {e}")
            return None

    def validate_plugin_manifest(self, manifest: PluginManifest) -> List[str]:
        """Validate plugin manifest and return list of issues."""
        issues = []

        # Check plugin type
        if manifest.plugin_type not in self._plugin_types:
            issues.append(f"Unknown plugin type: {manifest.plugin_type}")

        # Check permissions
        valid_permissions = [
            "network",
            "filesystem",
            "subprocess",
            "openrouter_api",
            "mcp_server",
            "mcp_client",
            "database",
            "keyring",
        ]

        for permission in manifest.permissions or []:
            if permission not in valid_permissions:
                issues.append(f"Unknown permission: {permission}")

        # Check version compatibility (simplified)
        # In production, use proper semver comparison
        if not manifest.min_doorman_version or not manifest.max_doorman_version:
            issues.append("Missing Doorman version constraints")

        return issues

    async def load_plugin(self, plugin_dir: Path) -> Optional[LoadedPlugin]:
        """Load a single plugin from directory."""
        manifest = self.load_plugin_manifest(plugin_dir)
        if not manifest:
            logger.error(f"No valid manifest found in {plugin_dir}")
            return None

        # Validate manifest
        issues = self.validate_plugin_manifest(manifest)
        if issues:
            logger.error(f"Plugin validation failed for {manifest.name}: {issues}")
            return None

        try:
            # Load the plugin module
            if self.config.enable_sandboxing:
                plugin_instance = await self._load_plugin_sandboxed(
                    plugin_dir, manifest
                )
            else:
                plugin_instance = await self._load_plugin_direct(plugin_dir, manifest)

            if plugin_instance:
                loaded_plugin = LoadedPlugin(
                    manifest=manifest,
                    plugin_instance=plugin_instance,
                    loaded_at=datetime.now(),
                )

                self._loaded_plugins[manifest.name] = loaded_plugin
                logger.info(
                    f"Successfully loaded plugin: {manifest.name} v{manifest.version}"
                )
                return loaded_plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {manifest.name}: {e}")

        return None

    async def _load_plugin_direct(
        self, plugin_dir: Path, manifest: PluginManifest
    ) -> Optional[Any]:
        """Load plugin directly (no sandboxing)."""
        entry_point_parts = manifest.entry_point.split(":")
        if len(entry_point_parts) != 2:
            raise ValueError(f"Invalid entry point format: {manifest.entry_point}")

        module_name, class_name = entry_point_parts

        # Add plugin directory to Python path temporarily
        sys.path.insert(0, str(plugin_dir))

        try:
            # Handle hyphenated module names by replacing with underscores for import
            import_name = module_name.replace("-", "_")

            # Check if file exists with hyphens (rename if needed)
            expected_file = plugin_dir / f"{module_name}.py"
            import_file = plugin_dir / f"{import_name}.py"

            if expected_file.exists() and not import_file.exists():
                # Copy file with underscores for import
                shutil.copy2(expected_file, import_file)

            # Import the plugin module
            module = importlib.import_module(import_name)

            # Get the plugin class
            plugin_class = getattr(module, class_name)

            # Verify it's the right type
            expected_base = self._plugin_types[manifest.plugin_type]
            if not issubclass(plugin_class, expected_base):
                raise TypeError(
                    f"Plugin class must inherit from {expected_base.__name__}"
                )

            # Instantiate the plugin
            plugin_instance = plugin_class(config=manifest.sprite_config or {})

            return plugin_instance

        finally:
            # Remove from Python path
            if str(plugin_dir) in sys.path:
                sys.path.remove(str(plugin_dir))

    async def _load_plugin_sandboxed(
        self, plugin_dir: Path, manifest: PluginManifest
    ) -> Optional[Any]:
        """Load plugin in sandboxed environment."""
        # For now, implement basic subprocess isolation
        # In production, could use Docker or other sandboxing

        sandbox_script = self._create_sandbox_script(plugin_dir, manifest)

        try:
            # Run plugin in subprocess with timeout and resource limits
            result = subprocess.run(
                [sys.executable, "-c", sandbox_script],
                cwd=plugin_dir,
                capture_output=True,
                text=True,
                timeout=self.config.sandbox_timeout,
                # Add resource limits if available
                env={
                    **dict(os.environ),
                    "PYTHONPATH": str(plugin_dir),
                    "DOORMAN_SANDBOX": "1",
                },
            )

            if result.returncode == 0:
                # For now, return a simple wrapper
                # In production, implement proper IPC
                return SandboxedPluginWrapper(plugin_dir, manifest, sandbox_script)
            else:
                logger.error(f"Sandbox execution failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"Plugin {manifest.name} timed out during loading")
            return None

    def _create_sandbox_script(self, plugin_dir: Path, manifest: PluginManifest) -> str:
        """Create sandbox execution script."""
        return f"""
import sys
import importlib
sys.path.insert(0, '{plugin_dir}')

try:
    module_name, class_name = '{manifest.entry_point}'.split(':')
    module = importlib.import_module(module_name)
    plugin_class = getattr(module, class_name)
    plugin_instance = plugin_class(config={{}})
    
    # Basic validation
    if hasattr(plugin_instance, 'get_capabilities'):
        capabilities = plugin_instance.get_capabilities()
        print(f"SANDBOX_SUCCESS: {len(capabilities)} capabilities")
    else:
        print("SANDBOX_ERROR: Missing get_capabilities method")
        sys.exit(1)
        
except Exception as e:
    print(f"SANDBOX_ERROR: {{e}}")
    sys.exit(1)
"""

    async def load_all_plugins(self) -> Dict[str, LoadedPlugin]:
        """Discover and load all available plugins."""
        plugin_dirs = self.discover_plugins()

        results = {}
        for plugin_dir in plugin_dirs:
            try:
                loaded_plugin = await self.load_plugin(plugin_dir)
                if loaded_plugin:
                    results[loaded_plugin.manifest.name] = loaded_plugin
            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_dir}: {e}")

        return results

    def get_plugins_by_type(self, plugin_type: str) -> List[LoadedPlugin]:
        """Get all loaded plugins of a specific type."""
        return [
            plugin
            for plugin in self._loaded_plugins.values()
            if plugin.manifest.plugin_type == plugin_type and plugin.is_active
        ]

    def get_plugin(self, name: str) -> Optional[LoadedPlugin]:
        """Get a specific plugin by name."""
        return self._loaded_plugins.get(name)

    async def call_plugin_method(
        self, plugin_name: str, method_name: str, *args, **kwargs
    ) -> Any:
        """Call a method on a specific plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin or not plugin.is_active:
            raise ValueError(f"Plugin {plugin_name} not found or not active")

        try:
            method = getattr(plugin.plugin_instance, method_name)
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                return method(*args, **kwargs)

        except Exception as e:
            plugin.error_count += 1
            if plugin.error_count >= 5:
                plugin.is_active = False
                logger.error(f"Plugin {plugin_name} deactivated due to errors")
            raise e

    def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin."""
        if name in self._loaded_plugins:
            plugin = self._loaded_plugins[name]
            plugin.is_active = False

            # Cleanup if needed
            if hasattr(plugin.plugin_instance, "cleanup"):
                try:
                    plugin.plugin_instance.cleanup()
                except Exception as e:
                    logger.warning(f"Plugin cleanup failed for {name}: {e}")

            del self._loaded_plugins[name]
            logger.info(f"Unloaded plugin: {name}")
            return True

        return False

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all loaded plugins."""
        status = {}

        for name, plugin in self._loaded_plugins.items():
            status[name] = {
                "name": plugin.manifest.name,
                "version": plugin.manifest.version,
                "type": plugin.manifest.plugin_type,
                "is_active": plugin.is_active,
                "error_count": plugin.error_count,
                "loaded_at": plugin.loaded_at.isoformat(),
                "permissions": plugin.manifest.permissions or [],
            }

        return status


class SandboxedPluginWrapper:
    """Wrapper for sandboxed plugin execution."""

    def __init__(self, plugin_dir: Path, manifest: PluginManifest, sandbox_script: str):
        self.plugin_dir = plugin_dir
        self.manifest = manifest
        self.sandbox_script = sandbox_script

    async def get_capabilities(self) -> List[str]:
        """Get capabilities via sandbox."""
        # Placeholder - in production, implement proper IPC
        return ["sandboxed_execution"]

    async def process_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process task via sandbox."""
        # Placeholder - in production, implement proper IPC
        return {"result": "sandboxed_execution", "task": task}


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
