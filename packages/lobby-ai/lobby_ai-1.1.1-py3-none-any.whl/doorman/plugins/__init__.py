"""Plugin system for Doorman."""

from .manager import (
    AgentPlugin,
    BillingProviderPlugin,
    LoadedPlugin,
    PluginConfig,
    PluginManager,
    PluginManifest,
    ToolPlugin,
    get_plugin_manager,
)
from .sdk import (
    PluginSDK,
    create_agent_plugin,
    create_billing_plugin,
    create_tool_plugin,
)

__all__ = [
    # Manager classes
    "PluginManager",
    "PluginConfig",
    "PluginManifest",
    "LoadedPlugin",
    "get_plugin_manager",
    # Base plugin classes
    "AgentPlugin",
    "ToolPlugin",
    "BillingProviderPlugin",
    # SDK classes and functions
    "PluginSDK",
    "create_agent_plugin",
    "create_tool_plugin",
    "create_billing_plugin",
]
