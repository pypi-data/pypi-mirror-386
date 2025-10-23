#!/usr/bin/env python3
"""
LOBBY MCP Server
AI orchestration service that other CLI tools can connect to

IMPORTANT: This server must remain non-interactive.
Do not import any interactive UI modules (prompts, etc.)
"""

import asyncio
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

# Ensure non-interactive mode
os.environ["DOORMAN_INTERACTIVE"] = "false"
os.environ["CI"] = "1"  # Force non-interactive

# Add path for imports during development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Check if MCP is available
mcp_available = False
try:
    from mcp import server, types
    from mcp.server.stdio import stdio_server

    mcp_available = True
except ImportError:
    # MCP not available - will fail at runtime
    pass

# Always try to import LOBBY dependencies
try:
    from doorman.providers.router import get_provider_router
except ImportError as e:
    print(f"Warning: Could not import LOBBY dependencies: {e}")


@dataclass
class MCPUsageRecord:
    """Track MCP tool usage for billing."""

    id: str
    client_name: str  # "claude-cli", "gemini-cli", etc.
    user_id: str
    tool_name: str
    timestamp: datetime
    task_type: str
    tokens_used: int
    estimated_cost: float
    actual_cost: float


class LobbyMCPBilling:
    """Simple billing for MCP usage."""

    def __init__(self, db_path: str = "lobby_mcp_usage.db"):
        self.db_path = db_path
        self.init_db()
        self.rate_per_request = 0.01  # $0.01 per orchestration request
        self.free_requests_per_day = 10  # 10 free requests per day

    def init_db(self):
        """Initialize usage tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_usage (
                id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                task_type TEXT,
                tokens_used INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                actual_cost REAL DEFAULT 0.0,
                request_data TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                user_id TEXT,
                date TEXT,
                request_count INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                PRIMARY KEY (user_id, date)
            )
        """)

        conn.commit()
        conn.close()

    def check_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user is within free tier limits."""
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT request_count, total_cost 
            FROM daily_usage 
            WHERE user_id = ? AND date = ?
        """,
            (user_id, today),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            return {
                "allowed": True,
                "requests_used": 0,
                "requests_remaining": self.free_requests_per_day,
                "total_cost_today": 0.0,
                "is_free": True,
            }

        requests_used, total_cost = result
        requests_remaining = max(0, self.free_requests_per_day - requests_used)
        is_free = requests_used < self.free_requests_per_day

        return {
            "allowed": True,  # Always allow but charge after free tier
            "requests_used": requests_used,
            "requests_remaining": requests_remaining,
            "total_cost_today": total_cost,
            "is_free": is_free,
            "charge_amount": 0.0 if is_free else self.rate_per_request,
        }

    def record_usage(
        self, client_name: str, user_id: str, tool_name: str, task_data: Dict[str, Any]
    ) -> MCPUsageRecord:
        """Record MCP tool usage."""
        usage_id = str(uuid.uuid4())
        timestamp = datetime.now()
        today = timestamp.strftime("%Y-%m-%d")

        # Check billing status
        usage_limits = self.check_usage_limits(user_id)
        actual_cost = usage_limits.get("charge_amount", 0.0)

        record = MCPUsageRecord(
            id=usage_id,
            client_name=client_name,
            user_id=user_id,
            tool_name=tool_name,
            timestamp=timestamp,
            task_type=task_data.get("task_type", "unknown"),
            tokens_used=task_data.get("tokens_used", 0),
            estimated_cost=task_data.get("estimated_cost", 0.0),
            actual_cost=actual_cost,
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record detailed usage
        cursor.execute(
            """
            INSERT INTO mcp_usage 
            (id, client_name, user_id, tool_name, task_type, tokens_used, 
             estimated_cost, actual_cost, request_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.id,
                record.client_name,
                record.user_id,
                record.tool_name,
                record.task_type,
                record.tokens_used,
                record.estimated_cost,
                record.actual_cost,
                json.dumps(task_data),
            ),
        )

        # Update daily usage
        cursor.execute(
            """
            INSERT OR REPLACE INTO daily_usage (user_id, date, request_count, total_cost)
            VALUES (?, ?, 
                COALESCE((SELECT request_count FROM daily_usage WHERE user_id = ? AND date = ?), 0) + 1,
                COALESCE((SELECT total_cost FROM daily_usage WHERE user_id = ? AND date = ?), 0) + ?
            )
        """,
            (user_id, today, user_id, today, user_id, today, actual_cost),
        )

        conn.commit()
        conn.close()

        return record


# Only define the MCP server if MCP is available
if mcp_available:

    class LobbyMCPServer:
        """LOBBY MCP Server - AI orchestration service."""

        def __init__(self):
            self.router = get_provider_router()
            self.billing = LobbyMCPBilling()
            self.app = server.Server("lobby-ai-concierge")
            self.setup_tools()

        def setup_tools(self):
            """Setup MCP tools that CLI clients can call."""

            @self.app.list_tools()
            async def list_tools() -> List[types.Tool]:
                """List available LOBBY concierge tools."""
                return [
                    types.Tool(
                        name="orchestrate_task",
                        description="🏢 Intelligent AI task orchestration with multi-provider routing.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task": {
                                    "type": "string",
                                    "description": "The task you want to orchestrate",
                                },
                                "user_id": {
                                    "type": "string",
                                    "description": "User identifier for billing",
                                    "default": "anonymous",
                                },
                                "preview_only": {
                                    "type": "boolean",
                                    "description": "If true, show routing analysis without executing",
                                    "default": False,
                                },
                            },
                            "required": ["task"],
                        },
                    ),
                    types.Tool(
                        name="check_usage",
                        description="📊 Check your LOBBY usage and billing status.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "user_id": {
                                    "type": "string",
                                    "description": "User identifier to check usage for",
                                    "default": "anonymous",
                                }
                            },
                            "required": ["user_id"],
                        },
                    ),
                ]

            @self.app.call_tool()
            async def call_tool(
                name: str, arguments: Dict[str, Any]
            ) -> List[types.TextContent]:
                """Handle tool calls from MCP clients."""

                if name == "orchestrate_task":
                    return await self.orchestrate_task(arguments)
                elif name == "check_usage":
                    return await self.check_usage(arguments)
                else:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"❌ Unknown tool: {name}. Available: orchestrate_task, check_usage",
                        )
                    ]

        async def orchestrate_task(
            self, args: Dict[str, Any]
        ) -> List[types.TextContent]:
            """Main task orchestration with AI routing."""
            task = args.get("task", "")
            user_id = args.get("user_id", "anonymous")
            preview_only = args.get("preview_only", False)

            if not task:
                return [
                    types.TextContent(
                        type="text", text="❌ Task description is required"
                    )
                ]

            return [
                types.TextContent(
                    type="text",
                    text=f"🏢 LOBBY would orchestrate: {task}\n(User: {user_id}, Preview: {preview_only})",
                )
            ]

        async def check_usage(self, args: Dict[str, Any]) -> List[types.TextContent]:
            """Check user's usage and billing status."""
            user_id = args.get("user_id", "anonymous")

            usage_limits = self.billing.check_usage_limits(user_id)

            response = [
                "📊 **LOBBY Usage Status**",
                "─" * 25,
                "",
                f"👤 **User:** {user_id}",
                f"📅 **Today:** {datetime.now().strftime('%Y-%m-%d')}",
                "",
                f"• Used Today: {usage_limits['requests_used']}",
                f"• Remaining Free: {usage_limits['requests_remaining']}",
                f"• Total Cost Today: ${usage_limits['total_cost_today']:.3f}",
                "",
                "Visit https://lobby.directory for more!",
            ]

            return [types.TextContent(type="text", text="\n".join(response))]


async def main():
    """Run the LOBBY MCP server."""
    if not mcp_available:
        raise ImportError("MCP not available")

    lobby_server = LobbyMCPServer()

    # Run stdio server
    async with stdio_server() as (read_stream, write_stream):
        await lobby_server.app.run(
            read_stream, write_stream, lobby_server.app.create_initialization_options()
        )


def main_entry():
    """Entry point for pip installation."""
    print("🏢 LOBBY MCP Server")
    print("AI Concierge Service for CLI Tools")
    print("==================================")

    if not mcp_available:
        print("❌ MCP dependencies not installed")
        print("Install with: pip install mcp")
        print("Then run: lobby-mcp")
        sys.exit(1)

    print("Starting MCP server...")
    print("Waiting for client connections...")
    print()

    asyncio.run(main())


if __name__ == "__main__":
    main_entry()
