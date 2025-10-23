"""Main CLI entry point for Doorman."""

import asyncio
from typing import Annotated, Optional

import typer

from doorman.core.intent_engine import (
    ConfidenceEngine,
    IntentClassifier,
    TaxonomyGenerator,
)
from doorman.ui.cyberpunk_theme import (
    CyberpunkApp,
    console,
    print_cyberpunk_banner,
    print_taxonomy_yaml,
)

app = typer.Typer(
    name="doorman",
    help="▮▮▮ DOORMAN.EXE - Agentic task decomposition system ▮▮▮",
    rich_markup_mode="rich",
)

# Initialize engines
intent_classifier = IntentClassifier()
taxonomy_generator = TaxonomyGenerator()
confidence_engine = ConfidenceEngine()


@app.command()
def plan(
    task: Annotated[str, typer.Argument(help="The task you want to decompose")],
    save: Annotated[bool, typer.Option("--save", "-s")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    script_only: Annotated[
        bool, typer.Option("--script-only", help="Output executable script only")
    ] = False,
    output_file: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Save script to file")
    ] = None,
    debug: Annotated[bool, typer.Option("--debug", help="Enable debug mode")] = False,
) -> None:
    """Decompose a task into executable shell commands."""

    from rich.syntax import Syntax

    from doorman.config.manager import get_config
    from doorman.core.script_engine import ScriptEngine

    # Get configuration
    config = get_config()

    # Override with CLI flags
    if verbose:
        config.verbose = True
    if debug:
        config.debug = True

    # Show configuration warnings if needed
    if not config.openrouter_api_key and not script_only:
        console.print(
            "[yellow]⚠️  No OpenRouter API key configured. Using fallback mode.[/yellow]"
        )
        console.print(
            "[dim]Set API key with: doorman config set openrouter_api_key YOUR_KEY[/dim]\n"
        )

    if not script_only:
        print_cyberpunk_banner()
        console.print("\n[neon_cyan]▮▮▮ PROCESSING INTENT ▮▮▮[/neon_cyan]")
        console.print(f"[primary]Input:[/primary] {task}")

        if config.debug:
            console.print(f"[dim]Using model:[/dim] {config.default_model}")
            console.print(
                f"[dim]API configured:[/dim] {'Yes' if config.openrouter_api_key else 'No'}"
            )

    try:
        # Classify intent
        intent, confidence, category = intent_classifier.classify_intent(task)

        if not script_only:
            console.print(
                f"[secondary]Category:[/secondary] [accent]{category}[/accent]"
            )
            console.print(
                f"[secondary]Confidence:[/secondary] [{'neon_green' if confidence > 0.8 else 'warning'}]{confidence:.1%}[/{'neon_green' if confidence > 0.8 else 'warning'}]"
            )

        # Generate taxonomy
        taxonomy = asyncio.run(
            taxonomy_generator.generate_taxonomy(intent, category, confidence)
        )

    except Exception as e:
        if config.debug:
            console.print(f"[red]Debug: Error in taxonomy generation: {e}[/red]")

        # Graceful fallback - create simple taxonomy
        from doorman.core.taxonomy import (
            Assumption,
            Component,
            ComponentType,
            ConfidenceLevel,
            IntentTaxonomy,
        )

        taxonomy = IntentTaxonomy(
            intent=task,
            intent_category="general",
            context_confidence=0.5,
            confidence_level=ConfidenceLevel.LOW,
            components=[
                Component(
                    type=ComponentType.TOOL,
                    name="basic_tools",
                    description="Basic tools required for the task",
                    required=True,
                )
            ],
            assumptions=[
                Assumption(description="Basic system access available", confidence=0.7)
            ],
            estimated_total_time_minutes=15,
            complexity_score=3,
        )

        if not script_only:
            console.print("[yellow]Using fallback taxonomy due to API issues[/yellow]")

    # Generate execution plan
    script_engine = ScriptEngine()
    execution_plan = asyncio.run(script_engine.generate_execution_plan(taxonomy))

    if script_only:
        # Output just the shell script
        shell_script = script_engine.generate_shell_script(execution_plan)
        if output_file:
            with open(output_file, "w") as f:
                f.write(shell_script)
            console.print(f"[neon_green]✅ Script saved to {output_file}[/neon_green]")
        else:
            print(shell_script)
        return

    # Display execution plan
    console.print("\n[neon_cyan]▮▮▮ EXECUTION PLAN ▮▮▮[/neon_cyan]")

    # Show plan details
    console.print(f"\n[bold white]📋 {execution_plan.title}[/bold white]")
    console.print(f"[secondary]{execution_plan.description}[/secondary]")
    console.print(
        f"[primary]⏱️  Estimated time:[/primary] [accent]{execution_plan.estimated_total_time} minutes[/accent]"
    )

    # Show prerequisites
    if execution_plan.prerequisites:
        console.print("\n[warning]📋 Prerequisites:[/warning]")
        for prereq in execution_plan.prerequisites:
            console.print(f"  [accent]▸ {prereq}[/accent]")

    # Show safety warnings
    if execution_plan.safety_warnings:
        console.print("\n[danger]⚠️  Safety Warnings:[/danger]")
        for warning in execution_plan.safety_warnings:
            console.print(f"  [danger]▸ {warning}[/danger]")

    # Show commands
    console.print("\n[neon_green]🔧 Commands to Execute:[/neon_green]")
    for i, cmd in enumerate(execution_plan.commands, 1):
        safety_colors = {
            "safe": "neon_green",
            "moderate": "warning",
            "dangerous": "danger",
        }
        safety_color = safety_colors[cmd.safety_level.value]

        console.print(f"\n[bold white]{i}. {cmd.description}[/bold white]")

        # Show the command with syntax highlighting
        syntax = Syntax(cmd.command, "bash", theme="monokai", line_numbers=False)
        console.print(syntax)

        # Show metadata
        meta_info = []
        meta_info.append(
            f"Safety: [{safety_color}]{cmd.safety_level.value.title()}[/{safety_color}]"
        )

        if cmd.expected_duration:
            meta_info.append(f"Duration: [accent]~{cmd.expected_duration}s[/accent]")

        if cmd.requires_confirmation:
            meta_info.append("[warning]Requires confirmation[/warning]")

        console.print(f"   [muted]{' | '.join(meta_info)}[/muted]")

    # Show success criteria
    if execution_plan.success_criteria:
        console.print("\n[neon_green]✅ Success Criteria:[/neon_green]")
        for criterion in execution_plan.success_criteria:
            console.print(f"  [neon_green]▸ {criterion}[/neon_green]")

    # Show clarification questions if needed
    if confidence_engine.should_ask_clarification(taxonomy):
        console.print("\n[warning]▮▮▮ CLARIFICATION NEEDED ▮▮▮[/warning]")
        for q in taxonomy.clarification_questions:
            console.print(f"[accent]? {q.question}[/accent]")
            if q.options:
                for i, option in enumerate(q.options, 1):
                    console.print(f"  [muted]{i}. {option}[/muted]")

    # Offer script generation options
    console.print("\n[neon_cyan]▮▮▮ SCRIPT OPTIONS ▮▮▮[/neon_cyan]")
    console.print("[primary]Generate executable script:[/primary]")
    console.print(
        f'  [cyan]doorman plan "{task}" --script-only[/cyan] - Output script to terminal'
    )
    console.print(
        f'  [cyan]doorman plan "{task}" --script-only --output script.sh[/cyan] - Save to file'
    )
    console.print("\n[muted]Or run commands individually from the plan above[/muted]")

    if verbose:
        # Show original taxonomy for debugging
        console.print("\n[muted]▮▮▮ DEBUG: Original Taxonomy ▮▮▮[/muted]")
        taxonomy_dict = {
            "intent": taxonomy.intent,
            "context_confidence": taxonomy.context_confidence,
            "confidence_level": taxonomy.confidence_level.value,
            "components": [
                {
                    "name": c.name,
                    "type": c.type.value,
                    "required": c.required,
                    "description": c.description,
                }
                for c in taxonomy.components
            ],
            "assumptions": [a.description for a in taxonomy.assumptions],
            "tools_needed": [
                c.name for c in taxonomy.components if c.type.value == "tool"
            ],
        }
        print_taxonomy_yaml(taxonomy_dict)

        issues = confidence_engine.validate_taxonomy(taxonomy)
        if issues:
            console.print("\n[danger]Issues found:[/danger]")
            for issue in issues:
                console.print(f"  [danger]▸ {issue}[/danger]")

    # Show token usage and cost information
    console.print("\n[neon_cyan]▮▮▮ TOKEN USAGE ▮▮▮[/neon_cyan]")
    console.print(
        "[primary]Token pass-through model:[/primary] You pay OpenRouter directly"
    )
    console.print(
        "[secondary]Estimated tokens used:[/secondary] [accent]~50-200 tokens[/accent]"
    )
    console.print(
        "[secondary]Estimated cost:[/secondary] [accent]$0.0001-0.0005[/accent]"
    )
    console.print(
        "[muted]Cost depends on task complexity and model (GPT-3.5-turbo used)[/muted]"
    )

    if save:
        console.print("\n[neon_green]▮ Plan saved to database[/neon_green]")


@app.command()
def tui() -> None:
    """Launch the cyberpunk TUI interface."""
    console.print("[neon_cyan]▮▮▮ INITIALIZING CYBERPUNK TUI ▮▮▮[/neon_cyan]")
    app_instance = CyberpunkApp()
    app_instance.run()


@app.command("mcp-server")
def mcp_server(
    port: Annotated[int, typer.Option("--port", "-p")] = 8080,
    host: Annotated[str, typer.Option("--host", "-h")] = "localhost",
) -> None:
    """Run Doorman as an MCP server."""
    from doorman.mcp_server.server import run_mcp_server

    console.print("[neon_cyan]▮▮▮ DOORMAN MCP SERVER ▮▮▮[/neon_cyan]")
    console.print(f"[primary]Host:[/primary] {host}")
    console.print(f"[primary]Port:[/primary] {port}")
    console.print(
        "[secondary]Status:[/secondary] [neon_green]Starting...[/neon_green]"
    )

    try:
        asyncio.run(run_mcp_server(host, port))
    except KeyboardInterrupt:
        console.print("\n[neon_green]▮ MCP Server stopped[/neon_green]")
    except Exception as e:
        console.print(f"\n[danger]▮ MCP Server error: {e}[/danger]")


@app.command("mcp-client")
def mcp_client(
    action: Annotated[
        str,
        typer.Argument(
            help="Action: discover, list-tools, list-servers, refresh, status"
        ),
    ] = "list-tools",
    server_name: Annotated[
        Optional[str], typer.Option("--server", "-s", help="Filter by server name")
    ] = None,
) -> None:
    """Use Doorman as an MCP client to discover tools."""
    from doorman.mcp_client.client import get_mcp_client

    console.print("[neon_cyan]▮▮▮ DOORMAN MCP CLIENT ▮▮▮[/neon_cyan]")
    console.print(f"[primary]Action:[/primary] {action}")

    if server_name:
        console.print(f"[secondary]Server filter:[/secondary] {server_name}")
    console.print()

    client = get_mcp_client()

    try:
        if action == "discover":
            console.print("🔍 [neon_yellow]Discovering MCP servers...[/neon_yellow]")
            results = asyncio.run(client.refresh_all_servers())

            console.print("✅ [neon_green]Discovery complete![/neon_green]")
            console.print(f"   📡 Servers found: {results['servers_discovered']}")
            console.print(f"   🔧 Tools discovered: {results['tools_discovered']}")

            if results["errors"]:
                console.print("\n⚠️  [warning]Errors:[/warning]")
                for error in results["errors"]:
                    console.print(f"   [danger]▸ {error}[/danger]")

        elif action == "list-servers":
            console.print("📡 [neon_yellow]Available MCP Servers:[/neon_yellow]")
            servers = client.get_server_status()

            if not servers:
                console.print(
                    "   [muted]No servers discovered yet. Run 'doorman mcp-client discover' first.[/muted]"
                )
            else:
                for name, server in servers.items():
                    if server_name and server_name.lower() not in name.lower():
                        continue

                    status_color = "neon_green" if server["is_active"] else "danger"
                    status_text = "Active" if server["is_active"] else "Inactive"

                    console.print(
                        f"\n[bold white]▸ {server['name']}[/bold white] ([{status_color}]{status_text}[/{status_color}])"
                    )
                    console.print(f"   📋 {server['description']}")
                    console.print(
                        f"   🔧 Tools: {server['tools_count']} | Protocol: {server['protocol']} | Version: {server['version']}"
                    )

                    if server["connection_errors"] > 0:
                        console.print(
                            f"   [warning]⚠️  Connection errors: {server['connection_errors']}[/warning]"
                        )

        elif action == "list-tools":
            console.print("🔧 [neon_yellow]Available MCP Tools:[/neon_yellow]")
            tools = client.get_available_tools()

            if not tools:
                console.print(
                    "   [muted]No tools discovered yet. Run 'doorman mcp-client discover' first.[/muted]"
                )
            else:
                filtered_tools = tools
                if server_name:
                    filtered_tools = [
                        t for t in tools if server_name.lower() in t.server_name.lower()
                    ]

                for i, tool in enumerate(filtered_tools, 1):
                    console.print(
                        f"\n[bold white]{i}. {tool.name}[/bold white] ([accent]{tool.server_name}[/accent])"
                    )
                    console.print(f"   📋 {tool.description}")

                    if tool.usage_count > 0:
                        console.print(
                            f"   📊 Used {tool.usage_count} times | Last used: {tool.last_used.strftime('%Y-%m-%d %H:%M') if tool.last_used else 'Never'}"
                        )

                    # Show input schema preview
                    if tool.input_schema.get("properties"):
                        params = list(tool.input_schema["properties"].keys())[:3]
                        if len(tool.input_schema["properties"]) > 3:
                            params.append(
                                f"... +{len(tool.input_schema['properties']) - 3} more"
                            )
                        console.print(f"   🔧 Parameters: {', '.join(params)}")

        elif action == "refresh":
            console.print(
                "🔄 [neon_yellow]Refreshing MCP server discovery...[/neon_yellow]"
            )
            results = asyncio.run(client.refresh_all_servers())

            console.print("✅ [neon_green]Refresh complete![/neon_green]")
            console.print(f"   📡 Servers: {results['servers_discovered']}")
            console.print(f"   🔧 Tools: {results['tools_discovered']}")

            if results["errors"]:
                console.print("\n[warning]Errors during refresh:[/warning]")
                for error in results["errors"]:
                    console.print(f"   [danger]▸ {error}[/danger]")

        elif action == "status":
            console.print("📊 [neon_yellow]MCP Client Status:[/neon_yellow]")
            servers = client.get_server_status()
            tools = client.get_available_tools()

            active_servers = len([s for s in servers.values() if s["is_active"]])
            total_tools = len(tools)
            used_tools = len([t for t in tools if t.usage_count > 0])

            console.print(f"   📡 Servers: {active_servers}/{len(servers)} active")
            console.print(f"   🔧 Tools: {total_tools} total, {used_tools} used")

            if tools:
                most_used = max(tools, key=lambda t: t.usage_count)
                if most_used.usage_count > 0:
                    console.print(
                        f"   🏆 Most used: {most_used.name} ({most_used.usage_count} times)"
                    )

        else:
            console.print(f"[danger]Unknown action: {action}[/danger]")
            console.print(
                "[muted]Available actions: discover, list-tools, list-servers, refresh, status[/muted]"
            )

    except Exception as e:
        console.print(f"[danger]Error: {e}[/danger]")


# Import and integrate configuration system
from doorman.cli.config import config_app

# Import providers CLI
from doorman.cli.providers import app as providers_app

# Create subcommands
db_app = typer.Typer(name="db", help="Database management commands")

# Add subcommands to main app
app.add_typer(db_app, name="db")
app.add_typer(config_app, name="config")
app.add_typer(providers_app, name="providers")


@db_app.command("init")
def db_init() -> None:
    """Initialize database schema."""
    console.print("[neon_cyan]▮▮▮ INITIALIZING DATABASE ▮▮▮[/neon_cyan]")

    try:
        from doorman.core.database import init_database

        asyncio.run(init_database())
        console.print("[neon_green]▮ Database initialized successfully[/neon_green]")
    except Exception as e:
        console.print(f"[danger]▮ Database initialization failed: {e}[/danger]")


@db_app.command("status")
def db_status() -> None:
    """Show database status and statistics."""
    console.print("[neon_cyan]▮▮▮ DATABASE STATUS ▮▮▮[/neon_cyan]")
    # TODO: Implement database status check
    console.print("[warning]▮ Database status coming soon[/warning]")


# Auth commands are now handled in config.py under config auth


@app.command("fighters")
def show_fighters() -> None:
    """Show available 16-bit fighters (agents and tiers)."""
    from doorman.assets.sprites import (
        CHARACTER_SELECT,
        get_sprite,
    )

    console.print("[neon_cyan]▮▮▮ SELECT YOUR FIGHTER ▮▮▮[/neon_cyan]\n")

    # Show tier fighters (top row)
    console.print("[neon_magenta]► TIER FIGHTERS[/neon_magenta]")
    tier_row = CHARACTER_SELECT["grid"][0]

    for fighter in tier_row:
        sprite_data = get_sprite(fighter)
        console.print(
            f"\n[accent]{fighter.split('_')[0].upper()}[/accent] - {sprite_data['description']}"
        )
        # Show first 3 lines of sprite
        sprite_lines = sprite_data["ascii"].split("\n")[:3]
        for line in sprite_lines:
            console.print(
                f"[{sprite_data['colors'][0]}]{line}[/{sprite_data['colors'][0]}]"
            )

    console.print("\n" + "═" * 50)

    # Show agent fighters (remaining rows)
    console.print("\n[neon_green]► AGENT FIGHTERS[/neon_green]")
    agent_fighters = CHARACTER_SELECT["grid"][1] + CHARACTER_SELECT["grid"][2]

    for i, fighter in enumerate(agent_fighters):
        if i % 2 == 0:  # New row every 2 fighters
            console.print()

        sprite_data = get_sprite(fighter)
        fighter_name = fighter.split("_")[0].upper()
        role = fighter.split("_")[1].upper() if "_" in fighter else "AGENT"

        console.print(
            f"[accent]{fighter_name}[/accent] [{role}] - {sprite_data['description']}"
        )

    console.print(
        "\n[muted]Use 'doorman plan <task>' to see which fighter is recommended![/muted]"
    )


@app.command()
def patterns(
    query: Annotated[str, typer.Argument(help="Search query for workflow patterns")],
    category: Annotated[
        Optional[str], typer.Option("--category", "-c", help="Filter by category")
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum results to show")
    ] = 5,
):
    """Search workflow patterns library."""
    from doorman.core.pattern_library import PatternSearchRequest, get_pattern_library

    # Show search header
    console.print(
        f"🔍 [bold neon_cyan]Searching patterns for:[/bold neon_cyan] {query}"
    )
    if category:
        console.print(
            f"📁 [bold neon_yellow]Category filter:[/bold neon_yellow] {category}"
        )
    console.print()

    try:
        # Search patterns
        pattern_lib = get_pattern_library()
        request = PatternSearchRequest(
            query=query, category=category, max_results=limit, min_similarity=0.2
        )

        results = asyncio.run(pattern_lib.search_patterns(request))

        if not results:
            console.print("❌ No matching patterns found", style="bold red")
            console.print(
                "💡 Try a different search term or remove category filter",
                style="yellow",
            )
            return

        # Display results
        console.print(f"✅ Found {len(results)} matching patterns:", style="bold green")
        console.print()

        for i, result in enumerate(results, 1):
            pattern = result.pattern

            # Pattern header
            console.print(f"[bold white]{i}. {pattern['name']}[/bold white]")
            console.print(f"   📋 {pattern['description']}")
            console.print(
                f"   🏷️  Category: {pattern['category']} | Tags: {', '.join(pattern['tags'][:3])}"
            )
            console.print(
                f"   ⏱️  Time: {pattern['estimated_time_minutes']}min | Complexity: {pattern['complexity_score']:.1f}/1.0"
            )
            console.print(
                f"   📊 Similarity: {result.similarity_score:.2f} | Success Rate: {pattern['success_rate']:.1%}"
            )

            # Show components
            components = pattern["components"][:3]  # Show first 3
            comp_names = [comp["name"].replace("_", " ").title() for comp in components]
            if len(pattern["components"]) > 3:
                comp_names.append(f"... +{len(pattern['components']) - 3} more")
            console.print(f"   🔧 Components: {' → '.join(comp_names)}")
            console.print()

        # Show usage tip
        console.print(
            "💡 [italic yellow]Tip: Use 'doorman plan' with similar tasks to get pattern-enhanced workflow generation![/italic yellow]"
        )

    except Exception as e:
        console.print(f"❌ Error searching patterns: {e}", style="bold red")


@app.command("mcp-call")
def mcp_call(
    tool_name: Annotated[str, typer.Argument(help="Name of the MCP tool to call")],
    arguments: Annotated[
        str, typer.Option("--args", help="JSON arguments for the tool")
    ] = "{}",
):
    """Call an external MCP tool."""
    import json

    from doorman.mcp_client.client import get_mcp_client

    console.print("[neon_cyan]▮▮▮ DOORMAN MCP TOOL CALL ▮▮▮[/neon_cyan]")
    console.print(f"[primary]Tool:[/primary] {tool_name}")
    console.print(f"[secondary]Arguments:[/secondary] {arguments}")
    console.print()

    try:
        client = get_mcp_client()

        # Parse arguments
        try:
            args_dict = json.loads(arguments)
        except json.JSONDecodeError as e:
            console.print(f"[danger]Invalid JSON arguments: {e}[/danger]")
            return

        # Call the tool
        console.print("🔄 [neon_yellow]Calling external MCP tool...[/neon_yellow]")
        result = asyncio.run(client.call_tool(tool_name, args_dict))

        # Display result
        if "error" in result:
            console.print(f"❌ [danger]Error: {result['error']}[/danger]")
        else:
            console.print("✅ [neon_green]Tool call successful![/neon_green]")
            console.print()

            # Pretty print the result
            if isinstance(result, dict) and "content" in result:
                # Handle MCP text response format
                for item in result.get("content", []):
                    if item.get("type") == "text":
                        console.print("📄 [bold white]Result:[/bold white]")
                        console.print(item.get("text", ""))
            else:
                # Handle other result formats
                console.print("📊 [bold white]Raw Result:[/bold white]")
                console.print(json.dumps(result, indent=2))

    except Exception as e:
        console.print(f"❌ [danger]Error calling MCP tool: {e}[/danger]")


# Plugin commands
plug_app = typer.Typer(help="Plugin management commands")
app.add_typer(plug_app, name="plugins")


@plug_app.command()
def list(
    plugin_type: Annotated[
        Optional[str], typer.Option("--type", help="Filter by plugin type")
    ] = None,
    status: Annotated[
        Optional[str], typer.Option("--status", help="Filter by status")
    ] = None,
):
    """List installed plugins."""
    from doorman.plugins import get_plugin_manager

    try:
        plugin_manager = get_plugin_manager()
        plugin_status = plugin_manager.get_plugin_status()

        if not plugin_status:
            console.print("[yellow]No plugins currently loaded.[/yellow]")
            console.print("\nTo create a new plugin:")
            console.print("  [cyan]doorman plugins create my-agent agent[/cyan]")
            return

        console.print("\n[bold green]📦 Installed Plugins[/bold green]")

        for name, info in plugin_status.items():
            # Apply filters
            if plugin_type and info["type"] != plugin_type:
                continue

            plugin_status_str = "active" if info["is_active"] else "inactive"
            if info["error_count"] > 0:
                plugin_status_str = "error"

            if status and plugin_status_str != status:
                continue

            # Format status with emoji
            status_display = {
                "active": "✅ Active",
                "inactive": "⏸️ Inactive",
                "error": "❌ Error",
            }.get(plugin_status_str, plugin_status_str)

            permissions_str = ", ".join(info["permissions"][:2])
            if len(info["permissions"]) > 2:
                permissions_str += f" (+{len(info['permissions']) - 2})"

            console.print(
                f"\n[bold white]{name}[/bold white] [dim]v{info['version']}[/dim]"
            )
            console.print(f"  Type: {info['type']} | Status: {status_display}")
            console.print(f"  Permissions: {permissions_str}")
            if info["error_count"] > 0:
                console.print(f"  [red]Errors: {info['error_count']}[/red]")

        total = len(
            [
                p
                for p in plugin_status.values()
                if not plugin_type or p["type"] == plugin_type
            ]
        )
        console.print(f"\n[dim]Total: {total} plugins[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@plug_app.command()
def create(
    name: Annotated[str, typer.Argument(help="Plugin name")],
    plugin_type: Annotated[
        str, typer.Argument(help="Plugin type (agent, tool, billing_provider)")
    ],
    description: Annotated[
        Optional[str], typer.Option("--description", help="Plugin description")
    ] = None,
    author: Annotated[
        Optional[str], typer.Option("--author", help="Plugin author")
    ] = None,
    output_dir: Annotated[
        Optional[str], typer.Option("--output", help="Output directory")
    ] = None,
):
    """Create a new plugin from template."""
    from pathlib import Path

    from doorman.plugins import PluginSDK

    try:
        base_dir = Path(output_dir) if output_dir else Path.cwd()
        sdk = PluginSDK(base_dir)

        plugin_dir = sdk.create_plugin_scaffold(
            name=name,
            plugin_type=plugin_type,
            description=description or f"A {plugin_type} plugin for Doorman",
            author=author or "Unknown",
        )

        console.print("\n[bold green]✅ Plugin created successfully![/bold green]")
        console.print(f"[dim]Location:[/dim] {plugin_dir}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"1. [cyan]cd {plugin_dir}[/cyan]")
        console.print(
            f"2. Edit [yellow]{name}_plugin.py[/yellow] with your implementation"
        )
        console.print("3. Update [yellow]plugin.toml[/yellow] if needed")
        console.print(f"4. Test with [cyan]doorman plugins test {name}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error creating plugin:[/red] {str(e)}")
        raise typer.Exit(1)


@plug_app.command()
def test(
    name: Annotated[
        str, typer.Argument(help="Plugin name or path to plugin directory")
    ],
):
    """Test and validate a plugin."""
    from pathlib import Path

    from doorman.plugins import PluginSDK, get_plugin_manager

    try:
        # Check if it's a path or plugin name
        plugin_path = Path(name)
        if not plugin_path.exists():
            # Try standard plugin locations
            possible_paths = [
                Path.home() / ".doorman" / "plugins" / name,
                Path.cwd() / name,
                Path.cwd() / "plugins" / name,
            ]

            plugin_path = None
            for path in possible_paths:
                if path.exists() and (path / "plugin.toml").exists():
                    plugin_path = path
                    break

            if not plugin_path:
                console.print(f"[red]Plugin not found:[/red] {name}")
                console.print("\nTried locations:")
                for path in possible_paths:
                    console.print(f"  {path}")
                raise typer.Exit(1)

        console.print(f"\n[bold blue]🧪 Testing plugin:[/bold blue] {plugin_path.name}")

        # Validate plugin structure
        sdk = PluginSDK()
        issues = sdk.validate_plugin(plugin_path)

        if issues:
            console.print("\n[red]❌ Validation failed:[/red]")
            for issue in issues:
                console.print(f"  • {issue}")
            raise typer.Exit(1)

        console.print("\n[green]✅ Plugin structure is valid[/green]")

        # Try to load the plugin
        plugin_manager = get_plugin_manager()
        loaded_plugin = asyncio.run(plugin_manager.load_plugin(plugin_path))

        if loaded_plugin:
            console.print("[green]✅ Plugin loaded successfully[/green]")
            console.print(f"[dim]Name:[/dim] {loaded_plugin.manifest.name}")
            console.print(f"[dim]Version:[/dim] {loaded_plugin.manifest.version}")
            console.print(f"[dim]Type:[/dim] {loaded_plugin.manifest.plugin_type}")

            # Test basic functionality
            if loaded_plugin.manifest.plugin_type == "agent":
                capabilities = asyncio.run(
                    plugin_manager.call_plugin_method(
                        loaded_plugin.manifest.name, "get_capabilities"
                    )
                )
                console.print(f"[dim]Capabilities:[/dim] {', '.join(capabilities)}")

            elif loaded_plugin.manifest.plugin_type == "tool":
                tool_def = asyncio.run(
                    plugin_manager.call_plugin_method(
                        loaded_plugin.manifest.name, "get_tool_definition"
                    )
                )
                console.print(f"[dim]Tool:[/dim] {tool_def['name']}")

            console.print("\n[green]🎉 All tests passed![/green]")

            # Unload after testing
            plugin_manager.unload_plugin(loaded_plugin.manifest.name)
        else:
            console.print("[red]❌ Plugin failed to load[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Test failed:[/red] {str(e)}")
        raise typer.Exit(1)


@plug_app.command()
def load(
    plugins_dir: Annotated[
        Optional[str], typer.Option("--dir", help="Directory to load plugins from")
    ] = None,
):
    """Load all available plugins."""
    from pathlib import Path

    from doorman.plugins import PluginConfig, get_plugin_manager

    try:
        config = PluginConfig()
        if plugins_dir:
            config.plugins_dir = Path(plugins_dir)

        plugin_manager = get_plugin_manager()
        plugin_manager.config = config

        console.print("[bold blue]🔄 Loading plugins...[/bold blue]")

        loaded_plugins = asyncio.run(plugin_manager.load_all_plugins())

        if loaded_plugins:
            console.print(f"\n[green]✅ Loaded {len(loaded_plugins)} plugins:[/green]")

            for name, plugin in loaded_plugins.items():
                status = "[green]✅[/green]" if plugin.is_active else "[red]❌[/red]"
                console.print(
                    f"  {status} {name} ({plugin.manifest.plugin_type}) v{plugin.manifest.version}"
                )
        else:
            console.print("\n[yellow]No plugins found to load.[/yellow]")
            console.print(f"\nSearched in: {config.plugins_dir}")
            console.print(
                "\nTo create a plugin: [cyan]doorman plugins create my-plugin agent[/cyan]"
            )

    except Exception as e:
        console.print(f"[red]Error loading plugins:[/red] {str(e)}")
        raise typer.Exit(1)


# Billing commands
billing_app = typer.Typer(help="Billing and subscription management")
app.add_typer(billing_app, name="billing")


@billing_app.command()
def status(
    license_key: Annotated[
        Optional[str], typer.Option("--license", help="License key to validate")
    ] = None,
):
    """Show subscription status and usage."""
    import os

    from doorman.billing import get_billing_manager
    from doorman.core.models import get_user_id

    try:
        user_id = get_user_id()

        # Get license key from environment if not provided
        if not license_key:
            license_key = os.environ.get("DOORMAN_LICENSE_KEY")

        billing_manager = asyncio.run(get_billing_manager())
        usage_summary = asyncio.run(billing_manager.get_usage_summary(user_id))

        console.print("\n[bold green]💰 Doorman Billing Status[/bold green]")

        # Subscription info
        sub_info = usage_summary["subscription"]
        console.print("\n[bold white]Subscription:[/bold white]")
        console.print(f"  Tier: [cyan]{sub_info['tier'].title()}[/cyan]")
        console.print(
            f"  Status: [green]{sub_info['status'].title()}[/green]"
            if sub_info["is_active"]
            else f"  Status: [red]{sub_info['status'].title()}[/red]"
        )

        if sub_info.get("expires_at"):
            console.print(f"  Expires: [yellow]{sub_info['expires_at'][:10]}[/yellow]")

        # Quota info
        quota = usage_summary["quota"]
        console.print("\n[bold white]Usage Limits:[/bold white]")
        console.print(f"  Plans per day: [cyan]{quota['plans_per_day']}[/cyan]")
        console.print(f"  Plans per month: [cyan]{quota['plans_per_month']}[/cyan]")
        console.print(
            "  Custom agents: [green]✓[/green]"
            if quota["custom_agents"]
            else "  Custom agents: [red]✗[/red]"
        )
        console.print(
            "  Custom patterns: [green]✓[/green]"
            if quota["custom_patterns"]
            else "  Custom patterns: [red]✗[/red]"
        )
        console.print(
            "  Priority queue: [green]✓[/green]"
            if quota["priority_queue"]
            else "  Priority queue: [red]✗[/red]"
        )

        # Usage info
        usage = usage_summary["usage"]
        console.print("\n[bold white]Current Usage:[/bold white]")
        console.print(
            f"  Plans today: [yellow]{usage['plans_today']}[/yellow] / [cyan]{quota['plans_per_day']}[/cyan]"
        )
        console.print(
            f"  Plans this month: [yellow]{usage['plans_this_month']}[/yellow] / [cyan]{quota['plans_per_month']}[/cyan]"
        )
        console.print(
            f"  Remaining today: [green]{usage['plans_remaining_today']}[/green]"
        )
        console.print(
            f"  Remaining this month: [green]{usage['plans_remaining_month']}[/green]"
        )

        # Show upgrade info for free users
        if sub_info["tier"] == "free":
            console.print("\n[bold yellow]🚀 Upgrade Available[/bold yellow]")
            console.print(
                "Unlock unlimited plans, custom agents, and priority support!"
            )
            console.print("Run [cyan]doorman billing upgrade[/cyan] to see options.")

    except Exception as e:
        console.print(f"[red]Error checking billing status:[/red] {str(e)}")
        raise typer.Exit(1)


@billing_app.command()
def upgrade(
    tier: Annotated[
        Optional[str], typer.Argument(help="Target tier (premium, enterprise)")
    ] = None,
):
    """Get upgrade URL for subscription."""
    from doorman.billing import SubscriptionTier, get_billing_manager
    from doorman.core.models import get_user_id

    try:
        user_id = get_user_id()
        billing_manager = asyncio.run(get_billing_manager())

        if not tier:
            # Show available tiers
            console.print("\n[bold green]🚀 Doorman Subscription Tiers[/bold green]")

            console.print("\n[bold cyan]Premium - $19/month[/bold cyan]")
            console.print("  ✓ 100 plans per day (3,000/month)")
            console.print("  ✓ Custom agents and patterns")
            console.print("  ✓ Priority MCP server queue")
            console.print("  ✓ Sprite customization")
            console.print("  ✓ Email support")

            console.print("\n[bold magenta]Enterprise - $99/month[/bold magenta]")
            console.print("  ✓ Unlimited plans")
            console.print("  ✓ Team spaces and collaboration")
            console.print("  ✓ SSO and advanced security")
            console.print("  ✓ Custom deployment options")
            console.print("  ✓ Priority phone support")

            console.print(
                "\n[dim]Choose a tier:[/dim] [cyan]doorman billing upgrade premium[/cyan]"
            )
            return

        # Validate tier
        if tier.lower() == "premium":
            target_tier = SubscriptionTier.PREMIUM
        elif tier.lower() == "enterprise":
            target_tier = SubscriptionTier.ENTERPRISE
        else:
            console.print(f"[red]Unknown tier: {tier}[/red]")
            console.print("Available tiers: premium, enterprise")
            raise typer.Exit(1)

        # Get upgrade URL
        upgrade_url = billing_manager.get_upgrade_url(user_id, target_tier)

        console.print(f"\n[bold green]🚀 Upgrade to {tier.title()}[/bold green]")
        console.print("\n[bold white]Upgrade URL:[/bold white]")
        console.print(f"[cyan]{upgrade_url}[/cyan]")
        console.print(
            "\n[yellow]Visit the URL above to complete your subscription upgrade.[/yellow]"
        )
        console.print(
            "[dim]After purchase, use your license key with:[/dim] [cyan]doorman billing activate <license-key>[/cyan]"
        )

    except Exception as e:
        console.print(f"[red]Error getting upgrade URL:[/red] {str(e)}")
        raise typer.Exit(1)


@billing_app.command()
def activate(
    license_key: Annotated[str, typer.Argument(help="License key to activate")],
):
    """Activate a license key."""
    from doorman.billing import get_billing_manager
    from doorman.core.models import get_user_id

    try:
        user_id = get_user_id()
        billing_manager = asyncio.run(get_billing_manager())

        console.print("\n[bold blue]🔑 Activating License Key...[/bold blue]")

        # Validate subscription
        subscription = asyncio.run(
            billing_manager.get_subscription(user_id, license_key, force_refresh=True)
        )

        if subscription.is_active:
            console.print(
                "\n[bold green]✓ License activated successfully![/bold green]"
            )
            console.print(
                f"[dim]Tier:[/dim] [cyan]{subscription.tier.value.title()}[/cyan]"
            )
            console.print(
                f"[dim]Status:[/dim] [green]{subscription.status.value.title()}[/green]"
            )

            if subscription.expires_at:
                console.print(
                    f"[dim]Expires:[/dim] [yellow]{subscription.expires_at.strftime('%Y-%m-%d')}[/yellow]"
                )

            # Save license key to environment suggestion
            console.print("\n[bold yellow]Environment Setup:[/bold yellow]")
            console.print("To automatically use this license key, set:")
            console.print(f"[cyan]export DOORMAN_LICENSE_KEY='{license_key}'[/cyan]")

        else:
            console.print("\n[red]❌ License activation failed[/red]")
            console.print(f"[dim]Status:[/dim] [red]{subscription.status.value}[/red]")

            if subscription.metadata.get("error"):
                console.print(
                    f"[dim]Error:[/dim] [red]{subscription.metadata['error']}[/red]"
                )

            console.print("\n[yellow]Troubleshooting:[/yellow]")
            console.print("1. Check that the license key is correct")
            console.print("2. Ensure you have an internet connection for verification")
            console.print("3. Contact support if the issue persists")

            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error activating license:[/red] {str(e)}")
        raise typer.Exit(1)


@billing_app.command()
def demo():
    """Try Doorman with a demo license."""

    console.print("\n[bold green]🎆 Doorman Demo Mode[/bold green]")
    console.print("\nTry these demo license keys:")
    console.print("\n[bold cyan]Premium Demo (30 days):[/bold cyan]")
    console.print("  [yellow]DOORMAN_DEMO_PREMIUM[/yellow]")

    console.print("\n[bold magenta]Enterprise Demo (90 days):[/bold magenta]")
    console.print("  [yellow]DOORMAN_DEMO_ENTERPRISE[/yellow]")

    console.print(
        "\n[dim]Usage:[/dim] [cyan]doorman billing activate DOORMAN_DEMO_PREMIUM[/cyan]"
    )
    console.print(
        "[dim]Or set:[/dim] [cyan]export DOORMAN_LICENSE_KEY=DOORMAN_DEMO_PREMIUM[/cyan]"
    )


def main() -> None:
    """Main entry point for standalone CLI."""
    app()


if __name__ == "__main__":
    main()
