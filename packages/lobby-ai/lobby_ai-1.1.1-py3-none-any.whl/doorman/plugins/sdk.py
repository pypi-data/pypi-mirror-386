"""Plugin SDK and development utilities for Doorman."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml


class PluginSDK:
    """SDK for creating Doorman plugins."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()

    def create_plugin_scaffold(
        self,
        name: str,
        plugin_type: str,
        description: str = "",
        author: str = "Unknown",
        version: str = "0.1.0",
    ) -> Path:
        """Create a new plugin scaffold directory."""

        if plugin_type not in ["agent", "tool", "billing_provider"]:
            raise ValueError(f"Invalid plugin type: {plugin_type}")

        # Create plugin directory
        plugin_dir = self.base_dir / name
        plugin_dir.mkdir(exist_ok=True)

        # Create plugin.toml
        manifest = {
            "plugin": {
                "name": name,
                "version": version,
                "description": description,
                "author": author,
                "type": plugin_type,
                "entry_point": f"{name.replace('-', '_')}_plugin:Plugin",
                "permissions": self._get_default_permissions(plugin_type),
                "dependencies": [],
                "min_doorman_version": "0.1.0",
                "max_doorman_version": "999.0.0",
            }
        }

        # Add sprite configuration for agents
        if plugin_type == "agent":
            manifest["plugin"]["sprite"] = {
                "archetype": "developer",
                "color_scheme": "neon",
                "accessories": [],
            }

        with open(plugin_dir / "plugin.toml", "w") as f:
            toml.dump(manifest, f)

        # Create main plugin file
        plugin_file_content = self._get_plugin_template(name, plugin_type)
        plugin_filename = f"{name.replace('-', '_')}_plugin.py"
        with open(plugin_dir / plugin_filename, "w") as f:
            f.write(plugin_file_content)

        # Create __init__.py
        with open(plugin_dir / "__init__.py", "w") as f:
            f.write(f'"""Doorman {plugin_type} plugin: {name}."""\n')

        # Create example config
        example_config = self._get_example_config(plugin_type)
        with open(plugin_dir / "config.example.json", "w") as f:
            json.dump(example_config, f, indent=2)

        # Create README
        readme_content = self._get_readme_template(name, plugin_type, description)
        with open(plugin_dir / "README.md", "w") as f:
            f.write(readme_content)

        return plugin_dir

    def _get_default_permissions(self, plugin_type: str) -> List[str]:
        """Get default permissions for plugin type."""
        defaults = {
            "agent": ["openrouter_api"],
            "tool": ["filesystem", "network"],
            "billing_provider": ["network", "keyring"],
        }
        return defaults.get(plugin_type, [])

    def _get_plugin_template(self, name: str, plugin_type: str) -> str:
        """Get plugin template code."""

        if plugin_type == "agent":
            return f'''"""
{name.title()} Agent Plugin for Doorman.

This plugin provides AI agent capabilities for specific tasks.
"""

import asyncio
from typing import Dict, List, Any, Optional

from doorman.plugins.manager import AgentPlugin


class Plugin(AgentPlugin):
    """Main plugin class for {name} agent."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Plugin configuration
        self.specialization = config.get("specialization", "{name}")
        self.model_preference = config.get("model", "anthropic/claude-3-sonnet")
        self.max_iterations = config.get("max_iterations", 5)
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "task_planning",
            "code_generation", 
            "problem_solving",
            "{name}_specific_tasks"
        ]
    
    def get_required_tools(self) -> List[str]:
        """Return list of required tools."""
        return [
            "code_editor",
            "file_manager",
            "web_search"
        ]
    
    def get_sprite_config(self) -> Optional[Dict[str, Any]]:
        """Return sprite configuration."""
        return {{
            "archetype": "developer",
            "color_scheme": self.config.get("color_scheme", "neon"),
            "accessories": ["glasses", "headset"]
        }}
    
    async def process_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task with this agent."""
        
        # Extract task information
        task_type = context.get("task_type", "general")
        available_tools = context.get("available_tools", [])
        user_preferences = context.get("user_preferences", {{}})
        
        # Agent-specific processing logic
        plan_steps = await self._create_task_plan(task, task_type, available_tools)
        
        return {{
            "agent": self.specialization,
            "task": task,
            "plan": plan_steps,
            "estimated_duration": self._estimate_duration(plan_steps),
            "required_tools": self.get_required_tools(),
            "status": "ready",
            "sprite_config": self.get_sprite_config()
        }}
    
    async def _create_task_plan(
        self, 
        task: str, 
        task_type: str, 
        available_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """Create detailed task plan."""
        
        # Placeholder implementation
        # In production, use LLM to generate detailed plans
        
        base_steps = [
            {{
                "step": 1,
                "action": "analyze_requirements",
                "description": f"Analyze requirements for: {{task}}",
                "tools": ["analyzer"],
                "estimated_time": 60
            }},
            {{
                "step": 2, 
                "action": "implement_solution",
                "description": f"Implement solution for {{task_type}} task",
                "tools": available_tools[:3],  # Use first 3 available tools
                "estimated_time": 300
            }},
            {{
                "step": 3,
                "action": "validate_result", 
                "description": "Validate and test the implemented solution",
                "tools": ["tester", "validator"],
                "estimated_time": 120
            }}
        ]
        
        return base_steps
    
    def _estimate_duration(self, plan_steps: List[Dict[str, Any]]) -> int:
        """Estimate total duration in seconds."""
        return sum(step.get("estimated_time", 60) for step in plan_steps)
    
    def cleanup(self):
        """Clean up plugin resources."""
        pass
'''

        elif plugin_type == "tool":
            return f'''"""
{name.title()} Tool Plugin for Doorman.

This plugin provides tool capabilities for specific operations.
"""

import asyncio
from typing import Dict, Any

from doorman.plugins.manager import ToolPlugin


class Plugin(ToolPlugin):
    """Main plugin class for {name} tool."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Tool configuration
        self.tool_name = config.get("tool_name", "{name}")
        self.endpoint_url = config.get("endpoint_url")
        self.api_key = config.get("api_key")
        self.timeout = config.get("timeout", 30)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Return MCP-compatible tool definition."""
        return {{
            "name": self.tool_name,
            "description": "Tool for {name}-related operations",
            "inputSchema": {{
                "type": "object",
                "properties": {{
                    "operation": {{
                        "type": "string",
                        "description": "Operation to perform",
                        "enum": ["create", "read", "update", "delete"]
                    }},
                    "target": {{
                        "type": "string", 
                        "description": "Target resource or identifier"
                    }},
                    "data": {{
                        "type": "object",
                        "description": "Optional data for the operation"
                    }}
                }},
                "required": ["operation", "target"]
            }}
        }}
    
    async def call_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given arguments."""
        
        operation = arguments.get("operation")
        target = arguments.get("target")
        data = arguments.get("data", {{}})
        
        try:
            # Tool-specific implementation
            result = await self._execute_operation(operation, target, data)
            
            return {{
                "tool": self.tool_name,
                "operation": operation,
                "target": target,
                "result": result,
                "status": "success"
            }}
            
        except Exception as e:
            return {{
                "tool": self.tool_name,
                "operation": operation,
                "target": target,
                "error": str(e),
                "status": "error"
            }}
    
    async def _execute_operation(
        self, 
        operation: str, 
        target: str, 
        data: Dict[str, Any]
    ) -> Any:
        """Execute the specific operation."""
        
        # Placeholder implementation
        # Replace with actual tool logic
        
        await asyncio.sleep(0.1)  # Simulate work
        
        if operation == "create":
            return f"Created {{target}} with data: {{data}}"
        elif operation == "read":
            return f"Read data from {{target}}"
        elif operation == "update":
            return f"Updated {{target}} with data: {{data}}"
        elif operation == "delete":
            return f"Deleted {{target}}"
        else:
            raise ValueError(f"Unknown operation: {{operation}}")
    
    def cleanup(self):
        """Clean up plugin resources."""
        pass
'''

        else:  # billing_provider
            return f'''"""
{name.title()} Billing Provider Plugin for Doorman.

This plugin provides billing and subscription management capabilities.
"""

import asyncio
from typing import Dict, Any

from doorman.plugins.manager import BillingProviderPlugin


class Plugin(BillingProviderPlugin):
    """Main plugin class for {name} billing provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Provider configuration
        self.provider_name = config.get("provider_name", "{name}")
        self.api_endpoint = config.get("api_endpoint")
        self.webhook_secret = config.get("webhook_secret")
        self.default_currency = config.get("currency", "USD")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider information."""
        return {{
            "name": self.provider_name,
            "supported_currencies": [self.default_currency, "EUR", "GBP"],
            "supported_plans": ["free", "premium", "enterprise"],
            "features": {{
                "subscriptions": True,
                "one_time_payments": True,
                "webhooks": True,
                "customer_portal": True
            }},
            "endpoints": {{
                "api": self.api_endpoint,
                "webhooks": f"{{self.api_endpoint}}/webhooks"
            }}
        }}
    
    async def validate_subscription(
        self, 
        user_id: str, 
        license_key: str
    ) -> Dict[str, Any]:
        """Validate user subscription."""
        
        try:
            # Provider-specific validation logic
            subscription_data = await self._check_subscription_status(user_id, license_key)
            
            return {{
                "valid": True,
                "user_id": user_id,
                "plan": subscription_data.get("plan", "free"),
                "status": subscription_data.get("status", "active"),
                "expires_at": subscription_data.get("expires_at"),
                "features": subscription_data.get("features", []),
                "usage_limits": subscription_data.get("usage_limits", {{}})
            }}
            
        except Exception as e:
            return {{
                "valid": False,
                "user_id": user_id,
                "error": str(e),
                "plan": "free",
                "status": "error"
            }}
    
    async def _check_subscription_status(
        self, 
        user_id: str, 
        license_key: str
    ) -> Dict[str, Any]:
        """Check subscription status with provider API."""
        
        # Placeholder implementation
        # Replace with actual API calls
        
        await asyncio.sleep(0.1)  # Simulate API call
        
        # Mock subscription data
        return {{
            "plan": "premium",
            "status": "active", 
            "expires_at": "2024-12-31T23:59:59Z",
            "features": ["unlimited_plans", "custom_agents", "priority_queue"],
            "usage_limits": {{
                "plans_per_day": 1000,
                "api_calls_per_hour": 500
            }}
        }}
    
    def cleanup(self):
        """Clean up plugin resources."""
        pass
'''

    def _get_example_config(self, plugin_type: str) -> Dict[str, Any]:
        """Get example configuration for plugin type."""

        if plugin_type == "agent":
            return {
                "specialization": "coding",
                "model": "anthropic/claude-3-sonnet",
                "max_iterations": 5,
                "color_scheme": "neon",
                "sprite": {
                    "archetype": "developer",
                    "accessories": ["glasses", "headset"],
                },
            }

        elif plugin_type == "tool":
            return {
                "tool_name": "example_tool",
                "endpoint_url": "https://api.example.com",
                "api_key": "your_api_key_here",
                "timeout": 30,
            }

        else:  # billing_provider
            return {
                "provider_name": "example_billing",
                "api_endpoint": "https://billing.example.com/api",
                "webhook_secret": "your_webhook_secret",
                "currency": "USD",
            }

    def _get_readme_template(
        self, name: str, plugin_type: str, description: str
    ) -> str:
        """Get README template for plugin."""

        return f"""# {name.title()} Plugin

{description or f"A {plugin_type} plugin for Doorman."}

## Installation

1. Copy this plugin directory to your Doorman plugins folder:
   ```bash
   cp -r {name} ~/.doorman/plugins/
   ```

2. Install any required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the plugin by copying the example config:
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

## Configuration

The plugin accepts the following configuration options in `config.json`:

```json
{{
  "example_setting": "value",
  "another_setting": true
}}
```

## Usage

This {plugin_type} plugin provides the following capabilities:

- Feature 1: Description
- Feature 2: Description  
- Feature 3: Description

## Development

To modify this plugin:

1. Edit `{name}_plugin.py` with your custom logic
2. Update `plugin.toml` if you change capabilities or requirements
3. Test with: `doorman plugins test {name}`

## Permissions

This plugin requires the following permissions:
- permission1: Description
- permission2: Description

## License

[Your chosen license]
"""

    def validate_plugin(self, plugin_dir: Path) -> List[str]:
        """Validate a plugin directory structure and configuration."""
        issues = []

        # Check required files
        required_files = ["plugin.toml", "__init__.py"]
        for file_name in required_files:
            if not (plugin_dir / file_name).exists():
                issues.append(f"Missing required file: {file_name}")

        # Check plugin.toml format
        manifest_file = plugin_dir / "plugin.toml"
        if manifest_file.exists():
            try:
                data = toml.load(manifest_file)
                plugin_data = data.get("plugin", {})

                required_fields = ["name", "version", "type", "entry_point"]
                for field in required_fields:
                    if field not in plugin_data:
                        issues.append(f"Missing required field in plugin.toml: {field}")

                # Check entry point format
                entry_point = plugin_data.get("entry_point", "")
                if ":" not in entry_point:
                    issues.append("Entry point must be in format 'module:class'")

            except Exception as e:
                issues.append(f"Invalid plugin.toml format: {e}")

        # Check entry point file exists
        if not issues:  # Only if we successfully parsed the manifest
            try:
                data = toml.load(manifest_file)
                entry_point = data["plugin"]["entry_point"]
                module_name = entry_point.split(":")[0]

                expected_file = plugin_dir / f"{module_name}.py"
                if not expected_file.exists():
                    issues.append(f"Entry point file not found: {expected_file}")

            except Exception as e:
                issues.append(f"Could not validate entry point file: {e}")

        return issues

    def package_plugin(
        self, plugin_dir: Path, output_path: Optional[Path] = None
    ) -> Path:
        """Package plugin as distributable archive."""

        if not output_path:
            output_path = plugin_dir.parent / f"{plugin_dir.name}_plugin.tar.gz"

        # Validate plugin first
        issues = self.validate_plugin(plugin_dir)
        if issues:
            raise ValueError(f"Plugin validation failed: {issues}")

        # Create archive
        import tarfile

        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(plugin_dir, arcname=plugin_dir.name)

        return output_path


def create_agent_plugin(name: str, description: str = "", **kwargs) -> Path:
    """Convenience function to create agent plugin."""
    sdk = PluginSDK()
    return sdk.create_plugin_scaffold(name, "agent", description, **kwargs)


def create_tool_plugin(name: str, description: str = "", **kwargs) -> Path:
    """Convenience function to create tool plugin."""
    sdk = PluginSDK()
    return sdk.create_plugin_scaffold(name, "tool", description, **kwargs)


def create_billing_plugin(name: str, description: str = "", **kwargs) -> Path:
    """Convenience function to create billing provider plugin."""
    sdk = PluginSDK()
    return sdk.create_plugin_scaffold(name, "billing_provider", description, **kwargs)
