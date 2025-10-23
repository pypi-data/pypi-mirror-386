#!/usr/bin/env python3
"""
LOBBY - Intelligent AI Task Orchestration
Your concierge for AI-powered task execution
"""

import asyncio
import os
import sys

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doorman.providers.router import TaskType, get_provider_router
from openrouter_client import OpenRouterClient

console = Console()
app = typer.Typer(
    name="lobby", help="🏢 LOBBY - Your AI concierge for intelligent task orchestration"
)


def print_banner():
    """Print the LOBBY banner with NYC elegance."""
    banner = Text()
    banner.append(
        "┌────────────────────────────────────────────────────┐\n", style="bright_white"
    )
    banner.append(
        "│                                                    │\n", style="bright_white"
    )
    banner.append("│           ", style="bright_white")
    banner.append("🏢 L O B B Y", style="bold bright_cyan")
    banner.append("                          │\n", style="bright_white")
    banner.append(
        "│                                                    │\n", style="bright_white"
    )
    banner.append("│        ", style="bright_white")
    banner.append("Intelligent AI Task Orchestration", style="bright_yellow")
    banner.append("         │\n", style="bright_white")
    banner.append("│        ", style="bright_white")
    banner.append("Your concierge for any task", style="dim white")
    banner.append("             │\n", style="bright_white")
    banner.append(
        "│                                                    │\n", style="bright_white"
    )
    banner.append(
        "└────────────────────────────────────────────────────┘", style="bright_white"
    )

    console.print(banner)
    console.print(
        "   [dim]Welcome to your AI concierge service[/dim]", justify="center"
    )
    console.print()


async def orchestrate_task(task: str, dry_run: bool = False):
    """Orchestrate a task using AI - like a concierge handling your request."""

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")

    # Get router for intelligent routing
    router = get_provider_router()

    # Classify task type with NYC metaphors
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

    # Get optimal provider
    try:
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

        # Check if we have an API key before making real API call
        if not api_key:
            console.print("\n🔑 [yellow]API key required for full service[/yellow]")
            console.print("   Set: [cyan]export OPENROUTER_API_KEY='your-key'[/cyan]")
            console.print(
                "\n💡 [italic]Demo mode: Showing what the response would look like[/italic]"
            )

            # Simulate a response for demo purposes
            demo_response = {
                "content": f"""# {task_description.title()} Plan

## Executive Summary
This plan outlines the approach for: {task}

## Implementation Steps
1. **Research Phase** - Gather requirements and existing resources
2. **Design Phase** - Create architecture and implementation plan
3. **Execution Phase** - Implement the solution
4. **Testing Phase** - Verify functionality and performance
5. **Deployment Phase** - Release to production

## Expected Deliverables
- Complete implementation of the requested task
- Documentation and usage instructions
- Testing procedures and validation results

## Quality Assurance
- Code reviews at each phase
- Automated testing coverage
- Performance benchmarks
- Security review""",
                "usage": {"total_tokens": 350},
                "model": model,
                "finish_reason": "stop",
            }

            # Display results elegantly
            console.print("\n📋 [bold]Your Personalized Service Plan[/bold]")
            console.print("────────────────────────────────────────────")

            plan_panel = Panel(
                demo_response["content"],
                title="✨ Executive Plan",
                title_align="left",
                border_style="bright_green",
                padding=(1, 2),
            )
            console.print(plan_panel)

            # Service summary
            console.print("\n📊 [bold]Service Summary[/bold]")
            console.print("─────────────────────")

            usage = demo_response.get("usage", {})
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
                "AI Model",
                demo_response["model"].split("/")[-1]
                if "/" in demo_response["model"]
                else demo_response["model"],
            )
            summary_table.add_row("Provider Network", provider_type.value.upper())

            console.print(summary_table)

            console.print(
                "\n✅ [bright_green]Service completed successfully[/bright_green]"
            )
            console.print("   [dim]Thank you for using LOBBY concierge services[/dim]")
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
            temperature=0.7,
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
def request(
    task: str = typer.Argument(..., help="Describe your request"),
    preview: bool = typer.Option(
        False, "--preview", help="Preview service without execution"
    ),
):
    """Submit a task request to your AI concierge."""
    print_banner()
    console.print(f"📝 [bold]New Service Request:[/bold] {task}")
    console.print()
    asyncio.run(orchestrate_task(task, preview))


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
def demo():
    """Experience LOBBY concierge services."""
    print_banner()

    console.print("🎭 [bold]LOBBY Concierge Demo[/bold]")
    console.print("Experience our AI-powered task orchestration\n")

    if not os.getenv("OPENROUTER_API_KEY"):
        console.print(
            "💡 [yellow]Set OPENROUTER_API_KEY to experience full service[/yellow]"
        )
        console.print("   For now, showing service preview capabilities...\n")

    demo_requests = [
        ("Build a Python web scraper", "development"),
        ("Draft a professional proposal", "business writing"),
        ("Analyze market trends data", "research & analysis"),
    ]

    router = get_provider_router()

    console.print("📋 [bold]Sample Service Requests:[/bold]\n")

    for i, (request, category) in enumerate(demo_requests, 1):
        console.print(f"{i}. [bright_cyan]{request}[/bright_cyan]")
        console.print(f"   Category: {category}")

        # Show intelligent routing
        try:
            if "python" in request.lower():
                task_type = TaskType.CODING
            elif "draft" in request.lower() or "proposal" in request.lower():
                task_type = TaskType.WRITING
            else:
                task_type = TaskType.ANALYSIS

            provider, model, cost = router.get_optimal_provider(task_type, 1000)
            cost_display = f"${cost:.4f}" if cost > 0 else "Complimentary"
            console.print(
                f"   Service: {provider.value.upper()} → {model} ({cost_display})"
            )

        except Exception:
            console.print("   Status: Service temporarily unavailable")

        console.print()

    console.print("✨ [italic]Ready to serve you![/italic]")
    console.print("   Try: [cyan]lobby request 'your task here'[/cyan]")


@app.command()
def help():
    """Get help with LOBBY services."""
    print_banner()

    console.print("📖 [bold]LOBBY Concierge Services Guide[/bold]")
    console.print("─────────────────────────────────────\n")

    help_sections = [
        ("🎯 Request Service", "lobby request 'create a Python script'"),
        ("👀 Preview Service", "lobby request 'your task' --preview"),
        ("📊 Check Status", "lobby status"),
        ("⚙️  Configuration", "lobby config"),
        ("🎭 Try Demo", "lobby demo"),
    ]

    for title, command in help_sections:
        console.print(f"{title}")
        console.print(f"   [cyan]{command}[/cyan]\n")

    console.print("💡 [bold]Service Features:[/bold]")
    console.print("   • Intelligent AI model selection")
    console.print("   • Multi-provider routing for best results")
    console.print("   • Cost optimization (free models preferred)")
    console.print("   • Professional execution plans")
    console.print("   • Real-time usage tracking")


if __name__ == "__main__":
    app()
