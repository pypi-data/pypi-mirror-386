#!/usr/bin/env python3
"""
DOORMAN - Production-Ready AI Orchestration CLI
Real API integration with intelligent routing
"""

import asyncio
import os
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doorman.providers.router import TaskType, get_provider_router
from openrouter_client import OpenRouterClient

console = Console()
app = typer.Typer(name="doorman")


def print_banner():
    """Print the Doorman banner."""
    console.print(
        """
╔══════════════════════════════════════════════╗
║  DOORMAN.EXE v2.0 ▮▮▮ PRODUCTION READY ▮▮▮  ║
╠══════════════════════════════════════════════╣
║  Intelligent Multi-Provider AI Orchestration ║
║  OpenRouter • Anthropic • OpenAI • Gemini    ║
╚══════════════════════════════════════════════╝
""",
        style="bright_cyan",
    )


async def make_plan(task: str, dry_run: bool = False):
    """Create a plan using real AI."""

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("❌ [red]OPENROUTER_API_KEY required[/red]")
        return

    # Get router for intelligent routing
    router = get_provider_router()

    # Classify task type
    task_lower = task.lower()
    if any(word in task_lower for word in ["code", "program", "script", "debug"]):
        task_type = TaskType.CODING
    elif any(word in task_lower for word in ["write", "blog", "article"]):
        task_type = TaskType.WRITING
    elif any(word in task_lower for word in ["analyze", "research", "study"]):
        task_type = TaskType.ANALYSIS
    elif any(word in task_lower for word in ["create", "design", "brainstorm"]):
        task_type = TaskType.CREATIVE
    else:
        task_type = TaskType.REASONING

    # Get optimal provider
    try:
        provider_type, model, cost = router.get_optimal_provider(task_type, 1500)

        console.print("\n▮▮▮ INTELLIGENT ROUTING ▮▮▮")
        console.print(f"Task Type: {task_type.value}")
        console.print(f"Provider: {provider_type.value}")
        console.print(f"Model: {model}")
        console.print(f"Est Cost: ${cost:.4f}")

        if dry_run:
            console.print("\n🔍 [yellow]Dry run complete[/yellow]")
            return

        # Make real API call
        console.print("\n▮▮▮ CALLING AI PROVIDER ▮▮▮")
        console.print("🤖 Generating plan...")

        client = OpenRouterClient(api_key)

        system_prompt = f"""You are Doorman, an intelligent AI task orchestration system.
Create an actionable execution plan for this {task_type.value} task: {task}

Provide:
1. Brief analysis of what needs to be done
2. 3-5 executable steps with actual shell commands 
3. Expected outcome for each step

Format as a clear, actionable plan."""

        response = await client.generate_structured_response(
            model=model,
            system_prompt=system_prompt,
            user_prompt=f"Create a detailed execution plan for: {task}",
            temperature=0.7,
            max_tokens=1500,
        )

        # Display results
        console.print("\n▮▮▮ AI-GENERATED PLAN ▮▮▮")
        plan_panel = Panel(
            response["content"], title="🤖 Execution Plan", border_style="bright_green"
        )
        console.print(plan_panel)

        # Usage stats
        console.print("\n▮▮▮ USAGE STATS ▮▮▮")
        usage = response.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        actual_cost = (tokens_used / 1000) * 0.002

        stats_table = Table(show_header=False)
        stats_table.add_column("Metric", style="bright_white")
        stats_table.add_column("Value", style="bright_yellow")

        stats_table.add_row("Tokens Used", str(tokens_used))
        stats_table.add_row("Actual Cost", f"${actual_cost:.6f}")
        stats_table.add_row("Model", model)
        stats_table.add_row("Provider", provider_type.value)

        console.print(stats_table)

        console.print("\n✅ [green]Plan generation complete![/green]")

    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


@app.command()
def plan(
    task: str = typer.Argument(..., help="Task to plan"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show routing only"),
):
    """Create and execute an intelligent plan for any task."""
    print_banner()
    asyncio.run(make_plan(task, dry_run))


@app.command()
def providers():
    """Show provider status."""
    print_banner()

    router = get_provider_router()
    status = router.get_provider_status()

    console.print("▮▮▮ PROVIDER STATUS ▮▮▮")

    table = Table()
    table.add_column("Provider", style="bright_cyan")
    table.add_column("Status", style="bright_white")
    table.add_column("Source", style="bright_white")

    for name, info in status["providers"].items():
        status_text = (
            "🟢 Active" if info["enabled"] and info["has_api_key"] else "🔴 Inactive"
        )
        table.add_row(name.upper(), status_text, info["source"])

    console.print(table)
    console.print(
        f"\n📊 {status['active_providers']} active, {status['total_providers']} total"
    )


@app.command()
def config():
    """Show discovered configuration."""
    router = get_provider_router()
    discovered = router.config_manager.discover_existing_configs()

    console.print("\n🔍 [bold]Configuration Discovery[/bold]")

    if discovered:
        for provider_type, config in discovered.items():
            api_key_preview = (
                f"***{config['api_key'][-8:]}" if config.get("api_key") else "None"
            )
            console.print(
                f"✅ {provider_type.value}: {api_key_preview} ({config.get('source')})"
            )
    else:
        console.print("❌ No API keys found")


@app.command()
def demo():
    """Run a demo of Doorman capabilities."""
    print_banner()

    console.print("🚀 [bold]Doorman Demo[/bold]\n")

    if not os.getenv("OPENROUTER_API_KEY"):
        console.print("⚠️  [yellow]Set OPENROUTER_API_KEY to see full demo[/yellow]")
        console.print("For now, showing intelligent routing only...\n")

    demo_tasks = [
        "Write a Python function to sort a list",
        "Create a blog post about AI trends",
        "Analyze sales data for patterns",
    ]

    router = get_provider_router()

    for task in demo_tasks:
        console.print(f"📝 Task: {task}")

        # Show intelligent routing
        try:
            # Simple classification
            if "python" in task.lower() or "function" in task.lower():
                task_type = TaskType.CODING
            elif "blog" in task.lower() or "write" in task.lower():
                task_type = TaskType.WRITING
            else:
                task_type = TaskType.ANALYSIS

            provider, model, cost = router.get_optimal_provider(task_type, 1000)
            console.print(f"   🎯 Route: {provider.value} → {model} (${cost:.4f})")

        except Exception as e:
            console.print(f"   ❌ Routing error: {e}")

        console.print()

    console.print("✅ Demo complete!")
    console.print("Try: [cyan]doorman plan 'your task here'[/cyan]")


if __name__ == "__main__":
    app()
