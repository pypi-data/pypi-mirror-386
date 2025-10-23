"""MCP client implementation for discovering and integrating with external MCP servers."""

import asyncio
import json
import logging
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""

    name: str
    description: str
    version: str
    protocol: str  # "stdio", "http", "websocket"
    command: Optional[str] = None  # For stdio protocol
    args: Optional[List[str]] = None
    url: Optional[str] = None  # For HTTP/WebSocket protocols
    port: Optional[int] = None
    env: Optional[Dict[str, str]] = None
    tools: List[Dict[str, Any]] = None
    last_discovered: Optional[datetime] = None
    is_active: bool = True
    connection_errors: int = 0


@dataclass
class MCPTool:
    """MCP tool definition from external server."""

    server_name: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_info: MCPServerInfo
    last_used: Optional[datetime] = None
    usage_count: int = 0


class MCPClientConfig(BaseModel):
    """Configuration for MCP client."""

    discovery_timeout: int = 30
    max_concurrent_discoveries: int = 5
    cache_duration_hours: int = 24
    retry_failed_connections: bool = True
    max_connection_errors: int = 3


class MCPClient:
    """Client for discovering and interacting with external MCP servers."""

    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self.data_dir = Path.home() / ".doorman" / "mcp_client"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.servers_file = self.data_dir / "servers.json"
        self.tools_cache_file = self.data_dir / "tools_cache.json"

        # In-memory caches
        self._servers: Dict[str, MCPServerInfo] = {}
        self._tools: Dict[str, MCPTool] = {}  # tool_name -> MCPTool
        self._server_connections: Dict[str, Any] = {}  # Active connections

        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached servers and tools from disk."""
        # Load servers
        if self.servers_file.exists():
            try:
                with open(self.servers_file) as f:
                    data = json.load(f)
                    for server_name, server_data in data.items():
                        # Convert datetime strings back
                        if server_data.get("last_discovered"):
                            server_data["last_discovered"] = datetime.fromisoformat(
                                server_data["last_discovered"]
                            )
                        self._servers[server_name] = MCPServerInfo(**server_data)
            except Exception as e:
                logger.warning(f"Failed to load server cache: {e}")

        # Load tools
        if self.tools_cache_file.exists():
            try:
                with open(self.tools_cache_file) as f:
                    data = json.load(f)
                    for tool_name, tool_data in data.items():
                        # Reconstruct server_info
                        server_info_data = tool_data.pop("server_info")
                        if server_info_data.get("last_discovered"):
                            server_info_data["last_discovered"] = (
                                datetime.fromisoformat(
                                    server_info_data["last_discovered"]
                                )
                            )
                        server_info = MCPServerInfo(**server_info_data)

                        # Convert datetime strings
                        if tool_data.get("last_used"):
                            tool_data["last_used"] = datetime.fromisoformat(
                                tool_data["last_used"]
                            )

                        tool_data["server_info"] = server_info
                        self._tools[tool_name] = MCPTool(**tool_data)
            except Exception as e:
                logger.warning(f"Failed to load tools cache: {e}")

    def _save_cache(self) -> None:
        """Save servers and tools cache to disk."""
        try:
            # Save servers
            servers_data = {}
            for name, server in self._servers.items():
                server_dict = asdict(server)
                # Convert datetime to string
                if server_dict.get("last_discovered"):
                    server_dict["last_discovered"] = server.last_discovered.isoformat()
                servers_data[name] = server_dict

            with open(self.servers_file, "w") as f:
                json.dump(servers_data, f, indent=2)

            # Save tools
            tools_data = {}
            for name, tool in self._tools.items():
                tool_dict = asdict(tool)
                # Convert datetime fields
                if tool_dict.get("last_used"):
                    tool_dict["last_used"] = tool.last_used.isoformat()
                if tool_dict.get("server_info", {}).get("last_discovered"):
                    tool_dict["server_info"]["last_discovered"] = (
                        tool.server_info.last_discovered.isoformat()
                    )
                tools_data[name] = tool_dict

            with open(self.tools_cache_file, "w") as f:
                json.dump(tools_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    async def discover_local_servers(self) -> List[MCPServerInfo]:
        """Discover MCP servers on the local system."""
        discovered_servers = []

        # Common MCP server discovery methods
        discovery_methods = [
            self._discover_npm_mcp_servers,
            self._discover_python_mcp_servers,
            self._discover_config_file_servers,
            self._discover_well_known_servers,
        ]

        for method in discovery_methods:
            try:
                servers = await method()
                discovered_servers.extend(servers)
            except Exception as e:
                logger.warning(f"Discovery method {method.__name__} failed: {e}")

        # Update cache
        for server in discovered_servers:
            server.last_discovered = datetime.now()
            self._servers[server.name] = server

        self._save_cache()
        return discovered_servers

    async def _discover_npm_mcp_servers(self) -> List[MCPServerInfo]:
        """Discover NPM-installed MCP servers."""
        servers = []

        try:
            # Look for globally installed MCP packages
            result = subprocess.run(
                ["npm", "list", "-g", "--depth=0", "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})

                for package_name, package_info in dependencies.items():
                    # Look for packages that might be MCP servers
                    if any(
                        keyword in package_name.lower()
                        for keyword in ["mcp", "model-context"]
                    ):
                        # Try to get package.json to check for MCP server info
                        server_info = await self._check_npm_package_for_mcp(
                            package_name
                        )
                        if server_info:
                            servers.append(server_info)

        except Exception as e:
            logger.warning(f"NPM discovery failed: {e}")

        return servers

    async def _check_npm_package_for_mcp(
        self, package_name: str
    ) -> Optional[MCPServerInfo]:
        """Check if an NPM package is an MCP server."""
        try:
            # Get package info
            result = subprocess.run(
                ["npm", "view", package_name, "--json"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                package_data = json.loads(result.stdout)

                # Check if it has MCP server indicators
                if self._is_mcp_server_package(package_data):
                    return MCPServerInfo(
                        name=package_name,
                        description=package_data.get("description", ""),
                        version=package_data.get("version", "unknown"),
                        protocol="stdio",
                        command="npx",
                        args=[package_name],
                        tools=[],
                    )

        except Exception as e:
            logger.debug(f"Failed to check NPM package {package_name}: {e}")

        return None

    def _is_mcp_server_package(self, package_data: Dict[str, Any]) -> bool:
        """Check if package data indicates an MCP server."""
        # Check various indicators
        indicators = [
            "mcp" in package_data.get("keywords", []),
            "model-context-protocol" in package_data.get("keywords", []),
            "mcp-server" in package_data.get("name", "").lower(),
            any(
                "mcp" in dep.lower()
                for dep in package_data.get("dependencies", {}).keys()
            ),
            "mcp" in package_data.get("description", "").lower(),
        ]

        return any(indicators)

    async def _discover_python_mcp_servers(self) -> List[MCPServerInfo]:
        """Discover Python MCP servers via pip."""
        servers = []

        try:
            # Look for installed Python packages with MCP indicators
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                for package in packages:
                    package_name = package["name"]
                    if any(
                        keyword in package_name.lower()
                        for keyword in ["mcp", "model-context"]
                    ):
                        # Check if it's actually an MCP server
                        server_info = await self._check_python_package_for_mcp(
                            package_name, package["version"]
                        )
                        if server_info:
                            servers.append(server_info)

        except Exception as e:
            logger.warning(f"Python package discovery failed: {e}")

        return servers

    async def _check_python_package_for_mcp(
        self, package_name: str, version: str
    ) -> Optional[MCPServerInfo]:
        """Check if a Python package is an MCP server."""
        try:
            # Try to import and check for MCP server indicators
            import importlib

            try:
                module = importlib.import_module(package_name.replace("-", "_"))

                # Look for common MCP server patterns
                if hasattr(module, "main") or hasattr(module, "run_server"):
                    return MCPServerInfo(
                        name=package_name,
                        description=f"Python MCP server: {package_name}",
                        version=version,
                        protocol="stdio",
                        command="python",
                        args=["-m", package_name.replace("-", "_")],
                        tools=[],
                    )

            except ImportError:
                pass

        except Exception as e:
            logger.debug(f"Failed to check Python package {package_name}: {e}")

        return None

    async def _discover_config_file_servers(self) -> List[MCPServerInfo]:
        """Discover servers from configuration files."""
        servers = []

        # Common MCP config file locations
        config_locations = [
            Path.home() / ".mcp" / "servers.json",
            Path.home() / ".config" / "mcp" / "servers.json",
            Path.cwd() / "mcp-servers.json",
            Path.cwd() / ".mcp" / "servers.json",
        ]

        for config_file in config_locations:
            if config_file.exists():
                try:
                    with open(config_file) as f:
                        config_data = json.load(f)

                    # Parse different config formats
                    parsed_servers = self._parse_config_servers(config_data)
                    servers.extend(parsed_servers)

                except Exception as e:
                    logger.warning(f"Failed to parse config file {config_file}: {e}")

        return servers

    def _parse_config_servers(self, config_data: Dict[str, Any]) -> List[MCPServerInfo]:
        """Parse servers from config data."""
        servers = []

        # Handle different config formats
        if "servers" in config_data:
            server_configs = config_data["servers"]
        elif isinstance(config_data, dict) and all(
            isinstance(v, dict) for v in config_data.values()
        ):
            server_configs = config_data
        else:
            return servers

        for server_name, server_config in server_configs.items():
            try:
                server = MCPServerInfo(
                    name=server_name,
                    description=server_config.get("description", ""),
                    version=server_config.get("version", "unknown"),
                    protocol=server_config.get("protocol", "stdio"),
                    command=server_config.get("command"),
                    args=server_config.get("args", []),
                    url=server_config.get("url"),
                    port=server_config.get("port"),
                    env=server_config.get("env", {}),
                    tools=[],
                )
                servers.append(server)

            except Exception as e:
                logger.warning(f"Failed to parse server config {server_name}: {e}")

        return servers

    async def _discover_well_known_servers(self) -> List[MCPServerInfo]:
        """Discover well-known MCP servers from community registries."""
        servers = []

        # Well-known MCP servers (from community knowledge)
        well_known = [
            {
                "name": "mcp-server-git",
                "description": "Git repository MCP server",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-git"],
            },
            {
                "name": "mcp-server-filesystem",
                "description": "Filesystem operations MCP server",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem"],
            },
            {
                "name": "mcp-server-fetch",
                "description": "HTTP fetch MCP server",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-fetch"],
            },
            {
                "name": "mcp-server-sqlite",
                "description": "SQLite database MCP server",
                "command": "npx",
                "args": ["@modelcontextprotocol/server-sqlite"],
            },
        ]

        for server_data in well_known:
            # Check if the server is actually available
            if await self._check_server_availability(
                server_data["command"], server_data["args"]
            ):
                server = MCPServerInfo(
                    name=server_data["name"],
                    description=server_data["description"],
                    version="latest",
                    protocol="stdio",
                    command=server_data["command"],
                    args=server_data["args"],
                    tools=[],
                )
                servers.append(server)

        return servers

    async def _check_server_availability(self, command: str, args: List[str]) -> bool:
        """Check if an MCP server command is available."""
        try:
            # Try to run the server with --help or similar to see if it exists
            result = subprocess.run(
                [command] + args + ["--help"], capture_output=True, text=True, timeout=5
            )
            # If command exists and doesn't return major error, consider it available
            return result.returncode in [0, 1]  # 0 = success, 1 = help shown

        except Exception:
            return False

    async def discover_server_tools(self, server: MCPServerInfo) -> List[MCPTool]:
        """Discover available tools from a specific MCP server."""
        tools = []

        try:
            if server.protocol == "stdio":
                tools = await self._discover_stdio_server_tools(server)
            elif server.protocol == "http":
                tools = await self._discover_http_server_tools(server)
            else:
                logger.warning(f"Unsupported protocol: {server.protocol}")

        except Exception as e:
            logger.warning(f"Failed to discover tools for {server.name}: {e}")
            server.connection_errors += 1

            if server.connection_errors >= self.config.max_connection_errors:
                server.is_active = False

        # Cache discovered tools
        for tool in tools:
            self._tools[tool.name] = tool

        self._save_cache()
        return tools

    async def _discover_stdio_server_tools(
        self, server: MCPServerInfo
    ) -> List[MCPTool]:
        """Discover tools from a stdio MCP server."""
        tools = []

        try:
            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **(server.env or {})},
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "doorman", "version": "0.1.0"},
                },
            }

            process.stdin.write((json.dumps(init_request) + "\n").encode())
            await process.stdin.drain()

            # Read response
            response_line = await process.stdout.readline()
            init_response = json.loads(response_line.decode())

            if init_response.get("result"):
                # Send tools/list request
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }

                process.stdin.write((json.dumps(tools_request) + "\n").encode())
                await process.stdin.drain()

                # Read tools response
                tools_response_line = await process.stdout.readline()
                tools_response = json.loads(tools_response_line.decode())

                if tools_response.get("result", {}).get("tools"):
                    for tool_data in tools_response["result"]["tools"]:
                        tool = MCPTool(
                            server_name=server.name,
                            name=tool_data["name"],
                            description=tool_data.get("description", ""),
                            input_schema=tool_data.get("inputSchema", {}),
                            server_info=server,
                        )
                        tools.append(tool)

            # Clean shutdown
            process.terminate()
            await process.wait()

        except Exception as e:
            logger.warning(f"Failed to discover stdio tools for {server.name}: {e}")

        return tools

    async def _discover_http_server_tools(self, server: MCPServerInfo) -> List[MCPTool]:
        """Discover tools from an HTTP MCP server."""
        tools = []

        try:
            base_url = server.url or f"http://localhost:{server.port}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send tools list request
                response = await client.post(
                    f"{base_url}/mcp/tools/list",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {},
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("result", {}).get("tools"):
                        for tool_data in data["result"]["tools"]:
                            tool = MCPTool(
                                server_name=server.name,
                                name=tool_data["name"],
                                description=tool_data.get("description", ""),
                                input_schema=tool_data.get("inputSchema", {}),
                                server_info=server,
                            )
                            tools.append(tool)

        except Exception as e:
            logger.warning(f"Failed to discover HTTP tools for {server.name}: {e}")

        return tools

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on an external MCP server."""
        if tool_name not in self._tools:
            return {"error": f"Tool {tool_name} not found"}

        tool = self._tools[tool_name]
        server = tool.server_info

        try:
            if server.protocol == "stdio":
                result = await self._call_stdio_tool(tool, arguments)
            elif server.protocol == "http":
                result = await self._call_http_tool(tool, arguments)
            else:
                return {"error": f"Unsupported protocol: {server.protocol}"}

            # Update usage stats
            tool.last_used = datetime.now()
            tool.usage_count += 1
            self._save_cache()

            return result

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"error": str(e)}

    async def _call_stdio_tool(
        self, tool: MCPTool, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool via stdio protocol."""
        server = tool.server_info

        # Reuse connection if available, otherwise create new one
        if server.name not in self._server_connections:
            process = await asyncio.create_subprocess_exec(
                server.command,
                *server.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **(server.env or {})},
            )

            # Initialize connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "doorman", "version": "0.1.0"},
                },
            }

            process.stdin.write((json.dumps(init_request) + "\n").encode())
            await process.stdin.drain()
            response = await process.stdout.readline()

            self._server_connections[server.name] = process

        process = self._server_connections[server.name]

        # Call the tool
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool.name, "arguments": arguments},
        }

        process.stdin.write((json.dumps(tool_request) + "\n").encode())
        await process.stdin.drain()
        response_line = await process.stdout.readline()
        response = json.loads(response_line.decode())

        return response.get("result", response)

    async def _call_http_tool(
        self, tool: MCPTool, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool via HTTP protocol."""
        server = tool.server_info
        base_url = server.url or f"http://localhost:{server.port}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/mcp/tools/call",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {"name": tool.name, "arguments": arguments},
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("result", data)
            else:
                return {"error": f"HTTP error {response.status_code}: {response.text}"}

    def get_available_tools(self, category: Optional[str] = None) -> List[MCPTool]:
        """Get list of available external tools."""
        tools = list(self._tools.values())

        if category:
            # Simple category filtering based on tool name/description
            filtered_tools = []
            for tool in tools:
                if (
                    category.lower() in tool.name.lower()
                    or category.lower() in tool.description.lower()
                ):
                    filtered_tools.append(tool)
            tools = filtered_tools

        # Sort by usage count (most used first)
        tools.sort(key=lambda t: t.usage_count, reverse=True)
        return tools

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all discovered servers."""
        status = {}

        for server_name, server in self._servers.items():
            tools_count = len(
                [t for t in self._tools.values() if t.server_name == server_name]
            )

            status[server_name] = {
                "name": server.name,
                "description": server.description,
                "version": server.version,
                "protocol": server.protocol,
                "is_active": server.is_active,
                "tools_count": tools_count,
                "connection_errors": server.connection_errors,
                "last_discovered": server.last_discovered.isoformat()
                if server.last_discovered
                else None,
            }

        return status

    async def refresh_all_servers(self) -> Dict[str, Any]:
        """Refresh all server discoveries and tool listings."""
        results = {"servers_discovered": 0, "tools_discovered": 0, "errors": []}

        try:
            # Discover servers
            servers = await self.discover_local_servers()
            results["servers_discovered"] = len(servers)

            # Discover tools for each server
            for server in servers:
                if server.is_active:
                    try:
                        tools = await self.discover_server_tools(server)
                        results["tools_discovered"] += len(tools)
                    except Exception as e:
                        results["errors"].append(f"{server.name}: {str(e)}")

        except Exception as e:
            results["errors"].append(f"Discovery failed: {str(e)}")

        return results

    async def cleanup_connections(self) -> None:
        """Clean up active server connections."""
        for server_name, process in self._server_connections.items():
            try:
                if process.returncode is None:  # Process still running
                    process.terminate()
                    await process.wait()
            except Exception as e:
                logger.warning(f"Failed to cleanup connection to {server_name}: {e}")

        self._server_connections.clear()


# Global client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# Fix missing import
import os
