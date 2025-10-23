"""MCP client package for discovering and integrating with external MCP servers."""

from .client import MCPClient, MCPServerInfo, MCPTool, get_mcp_client

__all__ = ["MCPClient", "MCPServerInfo", "MCPTool", "get_mcp_client"]
