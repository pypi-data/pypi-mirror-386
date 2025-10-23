"""MCP server implementation for Doorman."""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel

# Note: model-context-protocol will be added when available
# For now, we'll create a compatible interface


class MCPTool(BaseModel):
    """MCP tool definition."""

    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = "doorman"
    version: str = "1.0.0"
    description: str = "Universal intent taxonomy and agentic orchestration system"
    host: str = "localhost"
    port: int = 8080


class DoormanMCPServer:
    """Doorman MCP server implementation."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.tools = self._register_tools()

    def _register_tools(self) -> List[MCPTool]:
        """Register all available MCP tools."""
        return [
            MCPTool(
                name="doorman.plan",
                description="Decompose any task into an executable taxonomy with agents, tools, and dependencies",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The task to decompose and plan",
                        },
                        "constraints": {
                            "type": "object",
                            "properties": {
                                "deadline": {
                                    "type": "string",
                                    "description": "ISO datetime deadline",
                                },
                                "budget_usd": {
                                    "type": "number",
                                    "description": "Budget limit in USD",
                                },
                                "privacy_level": {
                                    "type": "string",
                                    "enum": ["standard", "high", "enterprise"],
                                },
                            },
                            "required": [],
                        },
                        "user_context": {
                            "type": "object",
                            "properties": {
                                "user_id": {
                                    "type": "string",
                                    "description": "User identifier for sprite generation",
                                },
                                "tier": {
                                    "type": "string",
                                    "enum": ["free", "premium", "enterprise"],
                                    "default": "free",
                                },
                            },
                            "required": [],
                        },
                    },
                    "required": ["task"],
                },
            ),
            MCPTool(
                name="doorman.recommend_agents",
                description="Recommend AI agents for specific task categories",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task_category": {
                            "type": "string",
                            "description": "Category of task",
                            "enum": [
                                "coding",
                                "writing",
                                "analysis",
                                "research",
                                "project_management",
                                "design",
                            ],
                        },
                        "complexity": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "description": "Task complexity (1-10)",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier for personalized agents",
                        },
                    },
                    "required": ["task_category"],
                },
            ),
            MCPTool(
                name="doorman.billing.status",
                description="Check user tier, quotas, and feature access",
                input_schema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"}
                    },
                    "required": ["user_id"],
                },
            ),
            MCPTool(
                name="doorman.patterns.search",
                description="Search for similar task patterns and templates",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Task pattern to search for",
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category filter",
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 20,
                            "default": 5,
                            "description": "Number of patterns to return",
                        },
                    },
                    "required": ["query"],
                },
            ),
            MCPTool(
                name="doorman.sprites.generate",
                description="Generate unique 16-bit style sprites for users and agents",
                input_schema={
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "User ID or agent identifier",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["user", "agent"],
                            "description": "Type of sprite to generate",
                        },
                        "tier": {
                            "type": "string",
                            "enum": ["free", "premium", "enterprise"],
                            "default": "free",
                        },
                        "agent_type": {
                            "type": "string",
                            "enum": [
                                "developer",
                                "writer",
                                "analyst",
                                "researcher",
                                "pm",
                                "designer",
                                "support",
                            ],
                            "description": "Required if type is 'agent'",
                        },
                    },
                    "required": ["identifier", "type"],
                },
            ),
        ]

    async def handle_plan(
        self,
        task: str,
        constraints: Optional[Dict] = None,
        user_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Handle doorman.plan tool call."""
        from doorman.assets.sprite_generator import generate_user_sprite
        from doorman.core.database import get_db_session
        from doorman.core.intent_engine import IntentClassifier, TaxonomyGenerator
        from doorman.core.models import UserTier
        from doorman.core.tier_guard import check_plan_quota, get_tier_guard

        # Extract user context
        user_id = (
            user_context.get("user_id", "mcp_user") if user_context else "mcp_user"
        )
        tier_str = user_context.get("tier", "free") if user_context else "free"
        user_tier = UserTier(tier_str)

        # Check quota limits
        try:
            await check_plan_quota(uuid4(), user_tier)  # Use dummy UUID for now
        except Exception as e:
            tier_guard = get_tier_guard()
            upgrade_cta = tier_guard.get_upgrade_cta(user_tier)
            return {
                "error": "quota_exceeded",
                "message": str(e),
                "upgrade_cta": upgrade_cta,
            }

        # Generate taxonomy
        classifier = IntentClassifier()
        generator = TaxonomyGenerator()

        intent, confidence, category = classifier.classify_intent(task)
        taxonomy = await generator.generate_taxonomy(intent, category, confidence)

        # Suggest relevant patterns
        from doorman.core.pattern_library import get_pattern_library

        pattern_lib = get_pattern_library()
        suggested_patterns = await pattern_lib.suggest_patterns_for_intent(
            intent, category
        )

        # Format pattern suggestions
        pattern_suggestions = []
        for result in suggested_patterns:
            pattern = result.pattern
            pattern_suggestions.append(
                {
                    "id": result.pattern_id,
                    "name": pattern["name"],
                    "similarity_score": result.similarity_score,
                    "estimated_time_minutes": pattern["estimated_time_minutes"],
                    "complexity_score": pattern["complexity_score"],
                    "success_rate": pattern["success_rate"],
                }
            )

        # Suggest relevant MCP tools from external servers
        from doorman.mcp_client.client import get_mcp_client

        mcp_client = get_mcp_client()
        external_tools = mcp_client.get_available_tools()

        # Simple keyword matching for tool suggestions
        suggested_tools = []
        task_keywords = task.lower().split()
        for tool in external_tools[:10]:  # Limit to top 10 tools
            tool_text = f"{tool.name} {tool.description}".lower()
            relevance_score = sum(
                1 for keyword in task_keywords if keyword in tool_text
            )

            if relevance_score > 0:
                suggested_tools.append(
                    {
                        "name": tool.name,
                        "server": tool.server_name,
                        "description": tool.description[:100] + "..."
                        if len(tool.description) > 100
                        else tool.description,
                        "relevance_score": relevance_score,
                        "usage_count": tool.usage_count,
                    }
                )

        # Sort by relevance and usage
        suggested_tools.sort(
            key=lambda t: (t["relevance_score"], t["usage_count"]), reverse=True
        )

        # Generate user sprite
        user_sprite = generate_user_sprite(user_id, tier_str)

        # Build response with visual metadata
        response = {
            "intent": taxonomy.intent,
            "category": taxonomy.intent_category,
            "confidence": taxonomy.context_confidence,
            "confidence_level": taxonomy.confidence_level.value,
            "components": [
                {
                    "name": c.name,
                    "type": c.type.value,
                    "description": c.description,
                    "required": c.required,
                    "alternatives": c.alternatives,
                    "mcp_server": c.mcp_server,
                    "mcp_tool": c.mcp_tool,
                }
                for c in taxonomy.components
            ],
            "dependencies": [
                {
                    "from": str(d.from_component),
                    "to": str(d.to_component),
                    "type": d.dependency_type.value,
                    "condition": d.condition,
                }
                for d in taxonomy.dependencies
            ],
            "assumptions": [
                {
                    "description": a.description,
                    "confidence": a.confidence,
                    "fallback_strategy": a.fallback_strategy,
                }
                for a in taxonomy.assumptions
            ],
            "clarification_questions": [
                {"question": q.question, "type": q.question_type, "options": q.options}
                for q in taxonomy.clarification_questions
            ],
            "metadata": {
                "complexity_score": taxonomy.complexity_score,
                "estimated_time_minutes": taxonomy.estimated_total_time_minutes,
                "user_sprite": user_sprite,
                "tier": tier_str,
                "created_at": taxonomy.created_at.isoformat(),
            },
            "suggested_patterns": pattern_suggestions,
            "suggested_mcp_tools": suggested_tools[:5],  # Top 5 most relevant
        }

        # Save to database if user context provided
        if user_context and user_context.get("save", False):
            async with get_db_session() as db:
                await db.save_taxonomy(taxonomy, uuid4())  # Use dummy UUID

        return response

    async def handle_recommend_agents(
        self, task_category: str, complexity: int = 5, user_id: str = "default"
    ) -> Dict[str, Any]:
        """Handle doorman.recommend_agents tool call."""
        from doorman.assets.sprite_generator import generate_agent_sprite

        # Agent recommendations by category
        agent_recommendations = {
            "coding": ["developer", "support"],
            "writing": ["writer", "designer"],
            "analysis": ["analyst", "researcher"],
            "research": ["researcher", "analyst"],
            "project_management": ["pm", "support"],
            "design": ["designer", "writer"],
        }

        recommended_agents = agent_recommendations.get(task_category, ["developer"])

        # Generate sprites for each recommended agent
        agents = []
        for agent_type in recommended_agents:
            sprite = generate_agent_sprite(agent_type, user_id)
            agents.append(
                {
                    "type": agent_type,
                    "sprite": sprite,
                    "suitability_score": 9
                    if agent_type in recommended_agents[:2]
                    else 7,
                    "complexity_match": abs(complexity - 5)
                    <= 3,  # Simple matching logic
                }
            )

        return {
            "task_category": task_category,
            "complexity": complexity,
            "recommended_agents": agents,
        }

    async def handle_billing_status(self, user_id: str) -> Dict[str, Any]:
        """Handle doorman.billing.status tool call."""
        from doorman.assets.sprite_generator import generate_user_sprite
        from doorman.core.models import UserTier
        from doorman.core.tier_guard import get_tier_guard

        # For now, assume free tier - in production, look up user in database
        user_tier = UserTier.FREE
        tier_guard = get_tier_guard()
        limits = tier_guard.get_tier_limits(user_tier)
        user_sprite = generate_user_sprite(user_id, user_tier.value)

        # Get usage stats (mock for now)
        usage_today = {"total_requests": 3, "total_tokens": 1500}

        return {
            "user_id": user_id,
            "tier": user_tier.value,
            "tier_limits": {
                "daily_plans": limits.daily_plans,
                "monthly_plans": limits.monthly_plans,
                "max_steps_per_plan": limits.max_steps_per_plan,
                "concurrent_requests": limits.concurrent_requests,
                "features": [f.value for f in limits.features],
            },
            "usage_today": usage_today,
            "sprite": user_sprite,
            "upgrade_available": user_tier != UserTier.ENTERPRISE,
        }

    async def handle_patterns_search(
        self, query: str, category: Optional[str] = None, limit: int = 5
    ) -> Dict[str, Any]:
        """Handle doorman.patterns.search tool call."""
        from doorman.core.pattern_library import (
            PatternSearchRequest,
            get_pattern_library,
        )

        pattern_lib = get_pattern_library()

        # Create search request
        request = PatternSearchRequest(
            query=query,
            category=category,
            max_results=limit,
            min_similarity=0.2,
            include_embeddings=False,
        )

        # Search patterns using embedding similarity
        results = await pattern_lib.search_patterns(request)

        # Format results for MCP response
        formatted_patterns = []
        for result in results:
            pattern = result.pattern
            formatted_patterns.append(
                {
                    "id": result.pattern_id,
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "category": pattern["category"],
                    "tags": pattern["tags"],
                    "similarity_score": result.similarity_score,
                    "components": [comp["name"] for comp in pattern["components"]],
                    "estimated_time_minutes": pattern["estimated_time_minutes"],
                    "complexity_score": pattern["complexity_score"],
                    "success_rate": pattern["success_rate"],
                    "usage_count": pattern["usage_count"],
                    "template_variables": pattern.get("template_variables", {}),
                }
            )

        return {
            "query": query,
            "category": category,
            "patterns": formatted_patterns,
            "total_found": len(results),
            "search_method": "embedding_similarity",
        }

    async def handle_sprites_generate(
        self,
        identifier: str,
        sprite_type: str,
        tier: str = "free",
        agent_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Handle doorman.sprites.generate tool call."""
        from doorman.assets.sprite_generator import (
            generate_agent_sprite,
            generate_user_sprite,
        )

        if sprite_type == "user":
            sprite = generate_user_sprite(identifier, tier)
        elif sprite_type == "agent" and agent_type:
            sprite = generate_agent_sprite(agent_type, identifier)
        else:
            return {"error": "Invalid sprite type or missing agent_type"}

        return {"identifier": identifier, "type": sprite_type, "sprite": sprite}

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to appropriate handlers."""
        try:
            if name == "doorman.plan":
                return await self.handle_plan(
                    task=arguments["task"],
                    constraints=arguments.get("constraints"),
                    user_context=arguments.get("user_context"),
                )
            elif name == "doorman.recommend_agents":
                return await self.handle_recommend_agents(
                    task_category=arguments["task_category"],
                    complexity=arguments.get("complexity", 5),
                    user_id=arguments.get("user_id", "default"),
                )
            elif name == "doorman.billing.status":
                return await self.handle_billing_status(user_id=arguments["user_id"])
            elif name == "doorman.patterns.search":
                return await self.handle_patterns_search(
                    query=arguments["query"],
                    category=arguments.get("category"),
                    limit=arguments.get("limit", 5),
                )
            elif name == "doorman.sprites.generate":
                return await self.handle_sprites_generate(
                    identifier=arguments["identifier"],
                    sprite_type=arguments["type"],
                    tier=arguments.get("tier", "free"),
                    agent_type=arguments.get("agent_type"),
                )
            else:
                return {"error": f"Unknown tool: {name}"}

        except Exception as e:
            return {"error": str(e), "tool": name}

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information for MCP discovery."""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in self.tools
            ],
            "capabilities": {
                "supports_progress": False,
                "supports_cancellation": False,
                "supports_notifications": False,
            },
            "metadata": {
                "website": "https://github.com/franco/doorman",
                "repository": "https://github.com/franco/doorman",
                "author": "Franco",
                "tags": [
                    "ai",
                    "agents",
                    "task-planning",
                    "taxonomy",
                    "cyberpunk",
                    "16-bit",
                ],
            },
        }


# Global server instance
_server: Optional[DoormanMCPServer] = None


def get_mcp_server() -> DoormanMCPServer:
    """Get global MCP server instance."""
    global _server
    if _server is None:
        config = MCPServerConfig()
        _server = DoormanMCPServer(config)
    return _server


async def run_mcp_server(host: str = "localhost", port: int = 8080) -> None:
    """Run the MCP server."""
    server = get_mcp_server()
    server.config.host = host
    server.config.port = port

    print(f"🔌 Doorman MCP Server starting on {host}:{port}")
    print(f"🎮 Available tools: {len(server.tools)}")
    print("📋 Tools:")
    for tool in server.tools:
        print(f"  ▸ {tool.name} - {tool.description}")

    # In production, this would start actual MCP server
    # For now, just keep alive
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🔌 Doorman MCP Server stopped")


def main(host: str = "localhost", port: int = 8080) -> None:
    """Main entry point for MCP server CLI."""
    asyncio.run(run_mcp_server(host, port))


if __name__ == "__main__":
    main()
