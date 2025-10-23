#!/usr/bin/env python3
"""
LOBBY CLI - Your AI Concierge Service
Easy installation: pip install lobby-ai
"""

import asyncio
import os
import sys
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

# Add path for imports during development
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from doorman.providers.router import TaskType, get_provider_router
from lobby.patterns import PatternManager, TaskPattern

# Import UI components
from lobby.ui import (
    confirm,
    get_console,
    has_interactive_backend,
    input_text,
    is_interactive,
    password,
    print_banner,
    print_error,
    print_info,
    print_section_header,
    print_subtle,
    print_success,
    print_warning,
    select_many,
    select_one,
)
from openrouter_client import OpenRouterClient

console = get_console()
app = typer.Typer(
    name="lobby",
    help="🏢 LOBBY - Your AI concierge for intelligent task orchestration",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


# Global context for interactive mode
class GlobalContext:
    interactive: bool = True


ctx = GlobalContext()


@app.callback()
def main_callback(
    interactive: Optional[bool] = typer.Option(
        None,
        "--interactive/--no-interactive",
        help="Enable/disable interactive prompts",
    ),
):
    """Configure global options for LOBBY CLI."""
    if interactive is not None:
        ctx.interactive = interactive
    else:
        ctx.interactive = is_interactive()


async def orchestrate_task(
    task: str,
    agent: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_cost: Optional[float] = None,
    tools: Optional[list] = None,
    dry_run: bool = False,
):
    """Orchestrate a task using AI - like a concierge handling your request."""

    # Check API key - try secure storage first, then environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        # Try to retrieve from secure storage
        try:
            from lobby.security import get_secure_storage, retrieve_api_key_interactive

            storage = get_secure_storage()
            if storage.use_keychain:
                # Try keychain without password
                api_key = storage.retrieve_api_key("openrouter")
            elif ctx.interactive:
                # Interactive mode - prompt for password
                api_key = retrieve_api_key_interactive("openrouter")
        except Exception:
            pass

    if not api_key:
        console.print("🔑 [yellow]API key required for full service[/yellow]")
        console.print("   Run: [cyan]lobby setup[/cyan] to configure")
        console.print("   Or set: [cyan]export OPENROUTER_API_KEY='your-key'[/cyan]")
        console.print("   Get free credits at: [link]https://openrouter.ai[/link]")
        return

    # Get router for intelligent routing
    router = get_provider_router()

    # Determine task type based on agent or content
    if agent:
        agent_to_task_type = {
            "developer": TaskType.CODING,
            "writer": TaskType.WRITING,
            "analyst": TaskType.ANALYSIS,
            "researcher": TaskType.ANALYSIS,
            "strategist": TaskType.REASONING,
        }
        task_type = agent_to_task_type.get(agent, TaskType.REASONING)
        task_description = f"{agent.title()} task"
    else:
        # Auto-classify task type
        task_lower = task.lower()
        if any(word in task_lower for word in ["code", "program", "script", "debug"]):
            task_type = TaskType.CODING
            task_description = "Development project"
        elif any(word in task_lower for word in ["write", "blog", "article"]):
            task_type = TaskType.WRITING
            task_description = "Content creation"
        elif any(word in task_lower for word in ["analyze", "research", "study"]):
            task_type = TaskType.ANALYSIS
            task_description = "Research & analysis"
        elif any(word in task_lower for word in ["create", "design", "brainstorm"]):
            task_type = TaskType.CREATIVE
            task_description = "Creative project"
        else:
            task_type = TaskType.REASONING
            task_description = "Strategic planning"

    # Get optimal provider or use specified model
    try:
        if model:
            # Use specified model
            provider_type = (
                router.provider_registry.get_provider_for_model(model)
                if hasattr(router, "provider_registry")
                else router.default_provider
            )
            cost = 0.001  # Estimate
        else:
            # Auto-select optimal model
            provider_type, model, cost = router.get_optimal_provider(task_type, 1500)

        console.print("📋 [bold]Service Request Analysis[/bold]")
        console.print("────────────────────────────────────")

        service_table = Table(show_header=False, box=None, padding=(0, 2))
        service_table.add_column("Service", style="bright_white", width=18)
        service_table.add_column("Details", style="bright_green")

        service_table.add_row("Request Type", task_description)
        service_table.add_row("AI Provider", provider_type.value.upper())
        service_table.add_row("Model Selection", model)
        service_table.add_row(
            "Service Cost", f"${cost:.4f}" if cost > 0 else "Complimentary"
        )

        console.print(service_table)

        if dry_run:
            console.print("\n✨ [italic]Service preview complete[/italic]")
            return

        # Make real API call
        console.print("\n🤖 [bold]Executing your request...[/bold]")
        console.print("   [dim]Our AI concierge is working on this[/dim]")

        client = OpenRouterClient(api_key)

        system_prompt = f"""You are LOBBY, an elegant AI concierge service for task orchestration.
Create a sophisticated, actionable plan for this {task_description.lower()}: {task}

Provide:
1. Executive summary of the approach
2. 3-5 detailed steps with specific commands/actions
3. Expected deliverables and outcomes
4. Quality assurance recommendations

Format this as a professional service plan that a high-end concierge would deliver."""

        response = await client.generate_structured_response(
            model=model,
            system_prompt=system_prompt,
            user_prompt=f"Create a comprehensive execution plan for: {task}",
            temperature=temperature if temperature is not None else 0.7,
            max_tokens=1500,
        )

        # Display results elegantly
        console.print("\n📋 [bold]Your Personalized Service Plan[/bold]")
        console.print("────────────────────────────────────────────")

        plan_panel = Panel(
            response["content"],
            title="✨ Executive Plan",
            title_align="left",
            border_style="bright_green",
            padding=(1, 2),
        )
        console.print(plan_panel)

        # Service summary
        console.print("\n📊 [bold]Service Summary[/bold]")
        console.print("─────────────────────")

        usage = response.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        actual_cost = (tokens_used / 1000) * 0.002 if cost > 0 else 0.0

        summary_table = Table(show_header=False, box=None, padding=(0, 2))
        summary_table.add_column("Metric", style="bright_white", width=18)
        summary_table.add_column("Value", style="bright_yellow")

        summary_table.add_row("Processing Units", f"{tokens_used:,}")
        summary_table.add_row(
            "Service Cost",
            f"${actual_cost:.6f}" if actual_cost > 0 else "Complimentary",
        )
        summary_table.add_row(
            "AI Model", model.split("/")[-1] if "/" in model else model
        )
        summary_table.add_row("Provider Network", provider_type.value.upper())

        console.print(summary_table)

        console.print(
            "\n✅ [bright_green]Service completed successfully[/bright_green]"
        )
        console.print("   [dim]Thank you for using LOBBY concierge services[/dim]")

    except Exception as e:
        console.print(f"❌ [red]Service temporarily unavailable: {e}[/red]")
        console.print("   [dim]Please try again or contact our technical team[/dim]")


@app.command()
def setup(
    api_key: Optional[str] = typer.Option(None, "--api-key", help="OpenRouter API key"),
    model: Optional[str] = typer.Option(None, "--model", help="Default AI model"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Default agent profile"),
):
    """Configure LOBBY for your existing CLI tools (30 seconds)."""
    print_banner()
    print_section_header("LOBBY Setup")

    # Check existing API key
    existing_key = os.getenv("OPENROUTER_API_KEY")

    if ctx.interactive and not api_key:
        # Check if we should update existing key
        if existing_key:
            print_info(f"Found existing API key: {existing_key[:10]}...")
            if confirm("Would you like to update your API key?", default=False):
                api_key = password("Enter your new OpenRouter API key")
            else:
                api_key = existing_key
        else:
            print_warning("No API key found")
            print_subtle("Get free credits at https://openrouter.ai")

            api_key = password("Enter your OpenRouter API key")

    if not api_key and not existing_key:
        print_error("API key required for setup")
        print_info("Steps to get started:")
        console.print("   1. Visit [link]https://openrouter.ai[/link]")
        console.print("   2. Create account and get API key")
        console.print("   3. Run: [cyan]lobby setup --api-key YOUR_KEY[/cyan]")
        console.print(
            "   4. Or set: [cyan]export OPENROUTER_API_KEY='sk-or-...'[/cyan]"
        )
        raise typer.Exit(1)

    # Use existing key if not provided
    if not api_key:
        api_key = existing_key

    # Validate API key
    print_subtle("Validating API key...")
    try:
        # Quick validation with httpx
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}
        response = httpx.get(
            "https://openrouter.ai/api/v1/models", headers=headers, timeout=5.0
        )
        if response.status_code != 200:
            print_error(f"Invalid API key: {response.status_code}")
            raise typer.Exit(1)
        print_success("API key validated successfully")
    except Exception as e:
        print_warning(f"Could not validate API key: {e}")
        if not confirm("Continue without validation?", default=True):
            raise typer.Exit(1)

    # Select default agent
    if ctx.interactive and not agent:
        agents = {
            "developer": "Code generation, debugging, and technical solutions",
            "writer": "Content creation, blogs, and documentation",
            "analyst": "Data analysis, research, and insights",
            "researcher": "In-depth research and information gathering",
            "strategist": "Planning, strategy, and decision making",
        }

        agent_choices, agent_descriptions = list(agents.keys()), agents
        agent = select_one(
            "Choose your default agent profile",
            choices=agent_choices,
            descriptions=agent_descriptions,
            default="developer",
        )

    if not agent:
        agent = "developer"

    # Select default model
    if ctx.interactive and not model:
        models = {
            "agentica-org/deepcoder:free": "🎁 FREE - Code generation specialist",
            "meta-llama/llama-3.2-3b-instruct:free": "🎁 FREE - Fast, efficient general purpose",
            "google/gemini-flash-1.5": "💰 Balanced performance and cost",
            "anthropic/claude-3-haiku": "💰 Fast and affordable",
            "openai/gpt-4o-mini": "💰 OpenAI's efficient model",
            "anthropic/claude-3.5-sonnet": "💎 Premium - Best overall quality",
        }

        model_choices = list(models.keys())
        model = select_one(
            "Choose your default AI model",
            choices=model_choices,
            descriptions=models,
            default="meta-llama/llama-3.2-3b-instruct:free",
        )

    if not model:
        model = "meta-llama/llama-3.2-3b-instruct:free"

    # Save configuration
    print_section_header("Saving Configuration")

    # Store API key securely
    if ctx.interactive and confirm(
        "Store API key securely (recommended)?", default=True
    ):
        from lobby.security import store_api_key_interactive

        if store_api_key_interactive("openrouter", api_key):
            print_success("API key stored securely")
            if sys.platform == "darwin":
                print_subtle("Using macOS Keychain for secure storage")
            else:
                print_subtle("Using encrypted file for secure storage")
        else:
            print_warning("Could not store API key securely")
            # Fall back to environment variable
            os.environ["OPENROUTER_API_KEY"] = api_key
    else:
        # Set environment variable for current session
        os.environ["OPENROUTER_API_KEY"] = api_key

    # Save to config file for persistence
    config_dir = Path.home() / ".config" / "lobby"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"

    config = {
        "default_agent": agent,
        "default_model": model,
        "api_key_configured": True,  # Don't save actual key
    }

    try:
        import json

        with config_file.open("w") as f:
            json.dump(config, f, indent=2)
        # Restrict permissions on config file
        with suppress(Exception):
            os.chmod(config_file, 0o600)
        print_success(f"Configuration saved to {config_file}")
    except Exception as e:
        print_warning(f"Could not save config file: {e}")

    # Show summary
    print_section_header("Setup Complete")

    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("Setting", style="bright_white", width=20)
    summary_table.add_column("Value", style="bright_green")

    summary_table.add_row("API Key", f"{api_key[:10]}..." if api_key else "Not set")
    summary_table.add_row("Default Agent", agent)
    summary_table.add_row(
        "Default Model", model.split("/")[-1] if "/" in model else model
    )
    summary_table.add_row("Configuration", config_file)

    console.print(summary_table)

    # Next steps
    print_info("Next steps:")
    console.print("   • Run [cyan]lobby request 'Your task here'[/cyan] to start")
    console.print("   • Run [cyan]lobby --help[/cyan] to see all commands")
    console.print(
        "   • Set [cyan]export OPENROUTER_API_KEY[/cyan] in your shell profile"
    )

    print_subtle("\nThank you for choosing LOBBY concierge services")


@app.command()
def request(
    task: str = typer.Argument(..., help="Task description"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to use"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model to use"),
    temperature: Optional[float] = typer.Option(
        None, "--temperature", "-t", help="Temperature (0-1)"
    ),
    max_cost: Optional[float] = typer.Option(
        None, "--max-cost", help="Maximum cost in USD"
    ),
    tools: Optional[str] = typer.Option(
        None, "--tools", help="Comma-separated tools to use"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without executing"),
):
    """Submit a task request to your AI concierge."""
    print_banner()
    print_section_header("Processing Request")

    # Load config if exists
    config_file = Path.home() / ".config" / "lobby" / "config.json"
    config = {}
    if config_file.exists():
        try:
            import json

            with config_file.open() as f:
                config = json.load(f)
        except Exception:
            pass

    # Interactive mode: gather additional parameters
    if ctx.interactive:
        # Agent selection
        if not agent:
            agents = {
                "developer": "Code generation and debugging",
                "writer": "Content creation",
                "analyst": "Data analysis",
                "researcher": "Research tasks",
                "strategist": "Planning and strategy",
                "auto": "Let LOBBY decide",
            }

            agent = select_one(
                "Select agent specialization",
                choices=list(agents.keys()),
                descriptions=agents,
                default=config.get("default_agent", "auto"),
            )

        # Model selection
        if not model:
            models = {
                "auto": "🤖 Let LOBBY choose optimal model",
                "agentica-org/deepcoder:free": "🎁 FREE - Code specialist",
                "meta-llama/llama-3.2-3b-instruct:free": "🎁 FREE - General purpose",
                "google/gemini-flash-1.5": "💰 Fast and balanced",
                "anthropic/claude-3-haiku": "💰 Affordable quality",
                "openai/gpt-4o-mini": "💰 OpenAI efficient",
                "anthropic/claude-3.5-sonnet": "💎 Premium quality",
            }

            model = select_one(
                "Select AI model",
                choices=list(models.keys()),
                descriptions=models,
                default=config.get("default_model", "auto"),
            )

        # Tool selection
        if not tools and has_interactive_backend():
            available_tools = [
                "web-search",
                "code-execution",
                "file-operations",
                "database-query",
                "api-calls",
                "git-operations",
            ]

            selected_tools = select_many(
                "Select tools to enable (optional)", choices=available_tools, default=[]
            )

            if selected_tools:
                tools = ",".join(selected_tools)

        # Advanced options
        if has_interactive_backend() and confirm(
            "Configure advanced options?", default=False
        ):
            from lobby.ui import number_input

            if not temperature:
                temperature = number_input(
                    "Temperature (creativity, 0-1)",
                    default=0.7,
                    min_value=0.0,
                    max_value=1.0,
                    float_allowed=True,
                )

            if not max_cost:
                max_cost = number_input(
                    "Maximum cost in USD (0 for unlimited)",
                    default=0.0,
                    min_value=0.0,
                    max_value=10.0,
                    float_allowed=True,
                )

    # Show task preview
    console.print(f"\n[bold]Task:[/bold] {task}")
    console.print(f"[bold]Agent:[/bold] {agent or 'auto'}")
    console.print(f"[bold]Model:[/bold] {model or 'auto'}")
    if tools:
        console.print(f"[bold]Tools:[/bold] {tools}")
    if temperature is not None:
        console.print(f"[bold]Temperature:[/bold] {temperature}")
    if max_cost:
        console.print(f"[bold]Max Cost:[/bold] ${max_cost}")

    if dry_run:
        print_info("Dry run mode - no actual execution")
        return

    # Execute request
    if ctx.interactive and not confirm("\nProceed with this request?", default=True):
        print_subtle("Request cancelled")
        return

    # Run the orchestration
    asyncio.run(
        orchestrate_task(
            task,
            agent=agent if agent != "auto" else None,
            model=model if model != "auto" else None,
            temperature=temperature,
            max_cost=max_cost,
            tools=tools.split(",") if tools else None,
            dry_run=False,
        )
    )


@app.command(name="req")
def request_short(
    task: str = typer.Argument(..., help="Describe your request"),
    preview: bool = typer.Option(
        False, "--preview", help="Preview service without execution"
    ),
):
    """Submit a task request to your AI concierge (shorthand)."""
    print_banner()
    console.print(f"📝 [bold]New Service Request:[/bold] {task}")
    console.print()
    asyncio.run(orchestrate_task(task, dry_run=preview))


@app.command()
def status():
    """Check concierge service status."""
    print_banner()

    router = get_provider_router()
    service_status = router.get_provider_status()

    console.print("🏢 [bold]Concierge Service Status[/bold]")
    console.print("──────────────────────────────")

    status_table = Table()
    status_table.add_column("Service Provider", style="bright_cyan")
    status_table.add_column("Status", style="bright_white")
    status_table.add_column("Connection", style="bright_white")

    for name, info in service_status["providers"].items():
        status_icon = (
            "🟢 Available"
            if info["enabled"] and info["has_api_key"]
            else "🔴 Unavailable"
        )
        connection = info["source"].title()

        status_table.add_row(name.upper(), status_icon, connection)

    console.print(status_table)

    active = service_status["active_providers"]
    total = service_status["total_providers"]
    console.print(f"\n📊 Service Network: {active}/{total} providers available")


@app.command()
def config():
    """Show service configuration."""
    print_banner()

    router = get_provider_router()
    discovered = router.config_manager.discover_existing_configs()

    console.print("⚙️  [bold]Service Configuration[/bold]")
    console.print("───────────────────────────")

    if discovered:
        for provider_type, config in discovered.items():
            api_key_preview = (
                f"***{config['api_key'][-6:]}"
                if config.get("api_key")
                else "Not configured"
            )
            console.print(
                f"🔑 {provider_type.value.upper()}: {api_key_preview} ({config.get('source')})"
            )
    else:
        console.print("❌ No service credentials found")
        console.print("\n[dim]Configure your service credentials:[/dim]")
        console.print("   export OPENROUTER_API_KEY='your-key'")


@app.command()
def patterns(
    action: Optional[str] = typer.Argument(
        None, help="Action: list, new, run, edit, delete"
    ),
    pattern: Optional[str] = typer.Argument(
        None, help="Pattern name or ID for run/edit/delete"
    ),
):
    """Manage reusable task patterns and templates."""
    import re

    from rich.table import Table

    manager = PatternManager()

    # Default to list if no action specified
    if not action:
        action = "list"

    if action == "list":
        print_banner()
        print_section_header("Task Patterns")

        # Get all patterns
        patterns = manager.list_patterns()

        if not patterns:
            print_warning("No patterns found")
            print_info("Create your first pattern with: lobby patterns new")
            return

        # Group by category
        categories = {}
        for p in patterns:
            if p.category not in categories:
                categories[p.category] = []
            categories[p.category].append(p)

        # Display patterns by category
        for category, cat_patterns in sorted(categories.items()):
            console.print(f"\n[bold bright_cyan]{category.upper()}[/bold bright_cyan]")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Name", style="bright_white")
            table.add_column("Description", style="dim")
            table.add_column("Agent", style="cyan")
            table.add_column("Uses", justify="right", style="yellow")

            for p in cat_patterns:
                table.add_row(
                    p.name,
                    p.description[:50] + "..."
                    if len(p.description) > 50
                    else p.description,
                    p.agent,
                    str(p.usage_count),
                )

            console.print(table)

        print_subtle("\nRun a pattern: lobby patterns run <name>")
        print_subtle("Create new: lobby patterns new")

    elif action == "new":
        print_banner()
        print_section_header("Create New Pattern")

        if ctx.interactive:
            # Interactive pattern creation
            name = input_text("Pattern name", validate=lambda x: len(x) > 0)
            description = input_text("Description")

            # Select category
            existing_categories = manager.get_categories()
            categories = existing_categories + ["<new category>"]

            category = select_one(
                "Select category",
                choices=categories,
                default=existing_categories[0]
                if existing_categories
                else "<new category>",
            )

            if category == "<new category>":
                category = input_text("New category name")

            # Select agent
            agents = ["developer", "writer", "analyst", "researcher", "strategist"]
            agent = select_one(
                "Select default agent", choices=agents, default="developer"
            )

            # Select model
            models = [
                "auto",
                "agentica-org/deepcoder:free",
                "meta-llama/llama-3.2-3b-instruct:free",
                "anthropic/claude-3-haiku",
                "openai/gpt-4o-mini",
            ]
            model = select_one("Select default model", choices=models, default="auto")

            # Select tools
            available_tools = [
                "web-search",
                "code-execution",
                "file-operations",
                "database-query",
                "api-calls",
                "git-operations",
            ]
            tools = select_many(
                "Select tools (optional)", choices=available_tools, default=[]
            )

            # Template with variables
            console.print("\n[bold]Template Creation[/bold]")
            console.print("[dim]Use {variable_name} for placeholders[/dim]")
            template = input_text(
                "Task template", multiline=True, validate=lambda x: len(x) > 0
            )

            # Extract variables from template
            variables = {}
            var_pattern = re.compile(r"\{(\w+)\}")
            found_vars = var_pattern.findall(template)

            if found_vars:
                console.print(
                    f"\n[bold]Found variables: {', '.join(found_vars)}[/bold]"
                )
                for var in found_vars:
                    desc = input_text(f"Description for '{var}'")
                    variables[var] = desc

            # Create pattern
            new_pattern = TaskPattern(
                id=str(uuid.uuid4()),
                name=name,
                category=category,
                description=description,
                agent=agent,
                model=model,
                tools=tools,
                template=template,
                variables=variables,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            # Preview
            console.print("\n[bold]Pattern Preview:[/bold]")
            console.print(f"Name: {new_pattern.name}")
            console.print(f"Category: {new_pattern.category}")
            console.print(f"Agent: {new_pattern.agent}")
            console.print(
                f"Tools: {', '.join(new_pattern.tools) if new_pattern.tools else 'None'}"
            )
            console.print(
                f"Variables: {', '.join(new_pattern.variables.keys()) if new_pattern.variables else 'None'}"
            )

            if confirm("Save this pattern?", default=True):
                if manager.save_pattern(new_pattern):
                    print_success(f"Pattern '{name}' created successfully")
                else:
                    print_error("Failed to save pattern")
            else:
                print_subtle("Pattern creation cancelled")
        else:
            print_error("Pattern creation requires interactive mode")
            print_info("Run without --no-interactive flag")

    elif action == "run":
        if not pattern:
            print_error("Pattern name required")
            print_info("Usage: lobby patterns run <pattern-name>")
            return

        # Find pattern by name or ID
        patterns = manager.list_patterns()
        target_pattern = None

        for p in patterns:
            if p.name.lower() == pattern.lower() or p.id == pattern:
                target_pattern = p
                break

        if not target_pattern:
            # Try search
            results = manager.search_patterns(pattern)
            if results:
                target_pattern = results[0]

        if not target_pattern:
            print_error(f"Pattern '{pattern}' not found")
            return

        print_banner()
        print_section_header(f"Run Pattern: {target_pattern.name}")

        # Collect variable values
        variable_values = {}

        if target_pattern.variables:
            console.print("\n[bold]Fill in template variables:[/bold]")

            for var_name, var_desc in target_pattern.variables.items():
                if ctx.interactive:
                    value = input_text(
                        f"{var_name} ({var_desc})", validate=lambda x: len(x) > 0
                    )
                else:
                    value = typer.prompt(f"{var_name} ({var_desc})")
                variable_values[var_name] = value

        # Fill template
        task = target_pattern.template
        for var_name, value in variable_values.items():
            task = task.replace(f"{{{var_name}}}", value)

        # Preview
        console.print("\n[bold]Task to execute:[/bold]")
        console.print(Panel(task, border_style="cyan"))
        console.print(f"\nAgent: [cyan]{target_pattern.agent}[/cyan]")
        console.print(f"Model: [cyan]{target_pattern.model or 'auto'}[/cyan]")
        if target_pattern.tools:
            console.print(f"Tools: [cyan]{', '.join(target_pattern.tools)}[/cyan]")

        # Confirm and run
        if ctx.interactive and not confirm("Execute this task?", default=True):
            print_subtle("Task cancelled")
            return

        # Increment usage
        manager.increment_usage(target_pattern.id)

        # Run orchestration
        asyncio.run(
            orchestrate_task(
                task,
                agent=target_pattern.agent,
                model=target_pattern.model if target_pattern.model != "auto" else None,
                tools=target_pattern.tools,
                dry_run=False,
            )
        )

    elif action == "edit":
        if not pattern:
            print_error("Pattern name required")
            print_info("Usage: lobby patterns edit <pattern-name>")
            return

        # Find pattern
        patterns = manager.list_patterns()
        target_pattern = None

        for p in patterns:
            if p.name.lower() == pattern.lower() or p.id == pattern:
                target_pattern = p
                break

        if not target_pattern:
            print_error(f"Pattern '{pattern}' not found")
            return

        print_banner()
        print_section_header(f"Edit Pattern: {target_pattern.name}")

        if not ctx.interactive:
            print_error("Pattern editing requires interactive mode")
            return

        # Select fields to edit
        fields = [
            "name",
            "description",
            "category",
            "agent",
            "model",
            "tools",
            "template",
            "variables",
        ]

        fields_to_edit = select_many(
            "Select fields to edit", choices=fields, default=[]
        )

        if not fields_to_edit:
            print_subtle("No changes made")
            return

        # Edit selected fields
        if "name" in fields_to_edit:
            target_pattern.name = input_text("New name", default=target_pattern.name)

        if "description" in fields_to_edit:
            target_pattern.description = input_text(
                "New description", default=target_pattern.description
            )

        if "category" in fields_to_edit:
            categories = manager.get_categories() + ["<new>"]
            cat = select_one(
                "New category", choices=categories, default=target_pattern.category
            )
            if cat == "<new>":
                cat = input_text("New category name")
            target_pattern.category = cat

        if "agent" in fields_to_edit:
            agents = ["developer", "writer", "analyst", "researcher", "strategist"]
            target_pattern.agent = select_one(
                "New agent", choices=agents, default=target_pattern.agent
            )

        if "model" in fields_to_edit:
            models = [
                "auto",
                "agentica-org/deepcoder:free",
                "meta-llama/llama-3.2-3b-instruct:free",
            ]
            target_pattern.model = select_one(
                "New model", choices=models, default=target_pattern.model or "auto"
            )

        if "tools" in fields_to_edit:
            available_tools = [
                "web-search",
                "code-execution",
                "file-operations",
                "database-query",
                "api-calls",
                "git-operations",
            ]
            target_pattern.tools = select_many(
                "Select tools", choices=available_tools, default=target_pattern.tools
            )

        if "template" in fields_to_edit:
            target_pattern.template = input_text(
                "New template", default=target_pattern.template, multiline=True
            )

        target_pattern.updated_at = datetime.now()

        # Save
        if manager.save_pattern(target_pattern):
            print_success("Pattern updated successfully")
        else:
            print_error("Failed to update pattern")

    elif action == "delete":
        if not pattern:
            print_error("Pattern name required")
            print_info("Usage: lobby patterns delete <pattern-name>")
            return

        # Find pattern
        patterns = manager.list_patterns()
        target_pattern = None

        for p in patterns:
            if p.name.lower() == pattern.lower() or p.id == pattern:
                target_pattern = p
                break

        if not target_pattern:
            print_error(f"Pattern '{pattern}' not found")
            return

        print_warning(f"Delete pattern: {target_pattern.name}")
        console.print(f"Category: {target_pattern.category}")
        console.print(f"Description: {target_pattern.description}")

        if ctx.interactive:
            if confirm(
                f"Are you sure you want to delete '{target_pattern.name}'?",
                default=False,
            ):
                if manager.delete_pattern(target_pattern.id):
                    print_success("Pattern deleted")
                else:
                    print_error("Failed to delete pattern")
            else:
                print_subtle("Deletion cancelled")
        else:
            print_info("Use interactive mode to confirm deletion")

    else:
        print_error(f"Unknown action: {action}")
        print_info("Available actions: list, new, run, edit, delete")


@app.command()
def mcp():
    """Start LOBBY as an MCP server (for advanced users)."""
    import subprocess
    import sys

    print_banner()
    console.print("🔌 [bold]Starting LOBBY MCP Server[/bold]")
    console.print("─────────────────────────────")
    console.print("   Your CLI tools can now connect to LOBBY")
    console.print("   Press Ctrl+C to stop")
    console.print()

    try:
        # Start the MCP server
        subprocess.run([sys.executable, "-m", "lobby.mcp_server"])
    except KeyboardInterrupt:
        console.print("\n👋 [dim]LOBBY MCP server stopped[/dim]")


def main():
    """Main entry point for the CLI."""
    if len(sys.argv) == 1:
        # Show help by default
        print_banner()

        console.print("🎯 [bold]Quick Start:[/bold]")
        console.print(
            "   [cyan]lobby setup[/cyan]     - Configure with your CLI tools (30 seconds)"
        )
        console.print(
            "   [cyan]lobby request 'task'[/cyan] - Get AI orchestration for any task"
        )
        console.print("   [cyan]lobby status[/cyan]    - Check service availability")
        console.print()
        console.print("💡 [dim]Get started: lobby setup[/dim]")
        return

    app()


if __name__ == "__main__":
    main()
