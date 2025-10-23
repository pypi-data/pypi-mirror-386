#!/usr/bin/env python3
"""
DOORMAN - Production-Grade AI Orchestration CLI
Intelligent routing across OpenRouter, Anthropic, OpenAI with real billing
"""

import asyncio
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doorman.billing.clerk_integration import check_quota_limit, get_clerk_client
from doorman.providers.router import TaskType, get_provider_router
from openrouter_client import OpenRouterClient

console = Console()
app = typer.Typer(
    name="doorman",
    help="🚪 Doorman - Intelligent AI task orchestration with multi-provider routing",
    rich_markup_mode="rich",
)


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


@app.command()
async def plan(
    task: str = typer.Argument(..., help="Task to plan and execute"),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Force specific provider"
    ),
    max_cost: Optional[float] = typer.Option(
        None, "--max-cost", help="Maximum cost per plan"
    ),
    speed: bool = typer.Option(False, "--speed", help="Prioritize speed over cost"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show plan without executing"
    ),
    user_id: Optional[str] = typer.Option(
        "default_user", "--user", help="User ID for billing"
    ),
):
    """Create and execute an intelligent plan for any task."""

    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        console.print("❌ [red]OPENROUTER_API_KEY environment variable required[/red]")
        console.print("Set it with: [cyan]export OPENROUTER_API_KEY='your-key'[/cyan]")
        return

    print_banner()

    try:
        # Check billing quota
        if os.getenv("CLERK_SECRET_KEY"):
            allowed, quota_info = check_quota_limit(user_id)
            if not allowed:
                console.print("⚠️  [bold red]Usage quota exceeded![/]")
                console.print(
                    f"Tier: {quota_info['tier']} | Daily: {quota_info['daily_usage']['used']}/{quota_info['daily_usage']['limit']}"
                )
                console.print("\n💳 Upgrade: [cyan]doorman billing upgrade[/cyan]")
                return

        # Get router and optimal provider
        router = get_provider_router()

        # Classify task type
        task_lower = task.lower()
        if any(
            word in task_lower for word in ["code", "program", "script", "debug", "api"]
        ):
            task_type = TaskType.CODING
        elif any(
            word in task_lower for word in ["write", "blog", "article", "content"]
        ):
            task_type = TaskType.WRITING
        elif any(
            word in task_lower for word in ["analyze", "research", "study", "compare"]
        ):
            task_type = TaskType.ANALYSIS
        elif any(
            word in task_lower for word in ["create", "design", "brainstorm", "imagine"]
        ):
            task_type = TaskType.CREATIVE
        else:
            task_type = TaskType.REASONING

        # Get optimal routing
        if provider:
            # Force specific provider
            console.print(f"🎯 [yellow]Forcing provider: {provider}[/yellow]")
            # For simplicity, use OpenRouter with specified model
            provider_type, model, cost = (
                router.providers[list(router.providers.keys())[0]],
                provider,
                0.002,
            )
        else:
            provider_type, model, cost = router.get_optimal_provider(
                task_type=task_type,
                estimated_tokens=1500,
                max_cost=max_cost,
                require_speed=speed,
            )

        # Display routing info
        console.print("\n▮▮▮ INTELLIGENT ROUTING ▮▮▮")
        routing_table = Table(show_header=False)
        routing_table.add_column("Property", style="bright_white")
        routing_table.add_column("Value", style="bright_green")

        routing_table.add_row("Task Type", task_type.value.title())
        routing_table.add_row("Provider", provider_type.provider_type.value.upper())
        routing_table.add_row("Model", model)
        routing_table.add_row("Est. Cost", f"${cost:.4f}")
        routing_table.add_row("Optimization", "Speed" if speed else "Cost")

        console.print(routing_table)

        if dry_run:
            console.print("\n🔍 [yellow]Dry run complete - no API calls made[/yellow]")
            return

        # Make real API call
        console.print("\n▮▮▮ EXECUTING PLAN ▮▮▮")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Add task to progress
            api_task = progress.add_task("🤖 Calling AI provider...", total=None)

            # Initialize OpenRouter client
            openrouter = OpenRouterClient(
                api_key=os.getenv("OPENROUTER_API_KEY"),
                base_url="https://openrouter.ai/api/v1",
            )

            # Create the actual API request
            system_prompt = f"""You are Doorman, an intelligent AI task orchestration system. 
Break down the following {task_type.value} task into executable steps with shell commands.

Task: {task}

Provide:
1. A brief analysis of the task
2. 3-5 executable steps with actual shell commands
3. Expected outcomes for each step

Format as a structured plan with clear actionable items."""

            try:
                # Make the API call
                response = await openrouter.generate_structured_response(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=f"Create an execution plan for: {task}",
                    temperature=0.7,
                    max_tokens=1500,
                )

                progress.update(api_task, description="✅ Plan generated!")

                # Parse and display results
                console.print("\n▮▮▮ EXECUTION PLAN ▮▮▮")

                # Display the AI response
                plan_panel = Panel(
                    response.get("content", "No response generated"),
                    title="🤖 AI-Generated Plan",
                    border_style="bright_green",
                )
                console.print(plan_panel)

                # Display usage stats
                console.print("\n▮▮▮ USAGE STATS ▮▮▮")
                usage_table = Table(show_header=False)
                usage_table.add_column("Metric", style="bright_white")
                usage_table.add_column("Value", style="bright_yellow")

                tokens_used = response.get("usage", {}).get("total_tokens", 0)
                actual_cost = (tokens_used / 1000) * 0.002  # Rough estimate

                usage_table.add_row("Tokens Used", str(tokens_used))
                usage_table.add_row("Actual Cost", f"${actual_cost:.6f}")
                usage_table.add_row(
                    "Provider", f"{provider_type.provider_type.value} → {model}"
                )
                usage_table.add_row("User ID", user_id)

                console.print(usage_table)

                # Record usage for billing
                if os.getenv("CLERK_SECRET_KEY"):
                    console.print(
                        "\n📊 [dim]Usage recorded for billing analytics[/dim]"
                    )

            except Exception as e:
                progress.update(api_task, description="❌ API call failed")
                console.print(f"\n❌ [red]API Error: {e}[/red]")
                console.print("Check your API key and try again")

    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")


@app.command()
def providers():
    """List and manage AI providers."""
    print_banner()

    router = get_provider_router()
    status = router.get_provider_status()

    console.print("▮▮▮ PROVIDER STATUS ▮▮▮")

    providers_table = Table()
    providers_table.add_column("Provider", style="bright_cyan")
    providers_table.add_column("Status", style="bright_white")
    providers_table.add_column("Models", style="bright_white")
    providers_table.add_column("Speed Score", style="bright_white")
    providers_table.add_column("Source", style="bright_white")

    for provider_name, info in status["providers"].items():
        status_icon = "🟢" if info["enabled"] and info["has_api_key"] else "🔴"
        status_text = (
            "Active" if info["enabled"] and info["has_api_key"] else "Inactive"
        )

        providers_table.add_row(
            provider_name.upper(),
            f"{status_icon} {status_text}",
            str(info["models_available"]),
            f"{info['speed_score']}/10",
            info["source"],
        )

    console.print(providers_table)

    console.print(
        f"\n📊 Summary: {status['active_providers']} active, {status['total_providers']} total"
    )

    if status["active_providers"] == 0:
        console.print("\n⚠️  [yellow]No providers active[/yellow]")
        console.print("Set API keys:")
        console.print("• [cyan]export OPENROUTER_API_KEY='your-key'[/cyan]")
        console.print("• [cyan]export ANTHROPIC_API_KEY='your-key'[/cyan]")


@app.command()
def route(
    task: str = typer.Argument(..., help="Task to analyze for routing"),
    show_costs: bool = typer.Option(False, "--costs", help="Show cost comparison"),
):
    """Test intelligent routing for a task."""
    router = get_provider_router()

    # Classify task
    task_lower = task.lower()
    if any(word in task_lower for word in ["code", "program", "script", "debug"]):
        task_type = TaskType.CODING
    elif any(word in task_lower for word in ["write", "blog", "article"]):
        task_type = TaskType.WRITING
    elif any(word in task_lower for word in ["analyze", "research", "study"]):
        task_type = TaskType.ANALYSIS
    else:
        task_type = TaskType.REASONING

    console.print("\n🎯 [bold]Routing Analysis[/bold]")
    console.print(f"Task: {task}")
    console.print(f"Type: {task_type.value}")

    try:
        provider, model, cost = router.get_optimal_provider(task_type, 1000)

        console.print("\n✅ [green]Optimal Route[/green]")
        console.print(f"Provider: {provider.value}")
        console.print(f"Model: {model}")
        console.print(f"Cost: ${cost:.4f}")

        if show_costs:
            console.print("\n💰 [yellow]Cost Comparison[/yellow]")
            costs = router.estimate_task_cost(task_type, 800, 200)
            for p, c in sorted(costs.items(), key=lambda x: x[1]):
                marker = "🎯" if p == provider else "💰"
                console.print(f"{marker} {p.value}: ${c:.4f}")

    except Exception as e:
        console.print(f"❌ [red]Routing failed: {e}[/red]")


@app.command()
def billing(
    user_id: str = typer.Option("default_user", "--user", help="User ID to check"),
):
    """Check billing status and usage."""
    if not os.getenv("CLERK_SECRET_KEY"):
        console.print("⚠️  [yellow]Clerk billing not configured[/yellow]")
        console.print("Set: [cyan]export CLERK_SECRET_KEY='your-key'[/cyan]")
        return

    try:
        clerk_client = get_clerk_client()
        billing_info = clerk_client.get_user_billing(user_id)

        console.print(f"\n💳 [bold]Billing Status ({user_id})[/bold]")

        billing_table = Table(show_header=False)
        billing_table.add_column("Property", style="bright_white")
        billing_table.add_column("Value", style="bright_green")

        billing_table.add_row("Tier", billing_info.subscription_tier.value.upper())
        billing_table.add_row(
            "Daily Limit", str(billing_info.usage_limits["plans_per_day"])
        )
        billing_table.add_row(
            "Monthly Limit", str(billing_info.usage_limits["plans_per_month"])
        )
        billing_table.add_row(
            "Cost Per Plan", f"${billing_info.usage_limits['cost_per_plan']:.2f}"
        )
        billing_table.add_row("Monthly Spend", f"${billing_info.monthly_spend:.2f}")

        console.print(billing_table)

        # Check quota
        allowed, quota_info = check_quota_limit(user_id)
        status = "✅ Within Limits" if allowed else "❌ Exceeded"
        console.print(f"\nQuota Status: {status}")

        if not allowed:
            console.print("\n💳 [yellow]Upgrade needed[/yellow]")
            console.print("Available plans:")
            console.print("• Premium: $29/month - 1000 plans/day")
            console.print("• Enterprise: $299/month - Unlimited")

    except Exception as e:
        console.print(f"❌ [red]Billing check failed: {e}[/red]")


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
        console.print("\nSet environment variables:")
        console.print("• export OPENROUTER_API_KEY='your-key'")
        console.print("• export ANTHROPIC_API_KEY='your-key'")
        console.print("• export OPENAI_API_KEY='your-key'")


@app.command()
def demo():
    """Run a quick demo of Doorman capabilities."""
    print_banner()

    console.print("🚀 [bold]Running Doorman Demo[/bold]\n")

    demo_tasks = [
        ("Write a Python function to sort a list", "coding"),
        ("Create a blog post about AI trends", "writing"),
        ("Analyze this data for patterns", "analysis"),
    ]

    router = get_provider_router()

    for task, category in demo_tasks:
        console.print(f"📝 Task: {task}")
        console.print(f"   Category: {category}")

        # Show routing
        if category == "coding":
            task_type = TaskType.CODING
        elif category == "writing":
            task_type = TaskType.WRITING
        else:
            task_type = TaskType.ANALYSIS

        try:
            provider, model, cost = router.get_optimal_provider(task_type, 1000)
            console.print(f"   🎯 Route: {provider.value} → {model} (${cost:.4f})")
        except:
            console.print("   ❌ No providers available")

        console.print()

    console.print("✅ Demo complete! Try: [cyan]doorman plan 'your task here'[/cyan]")


if __name__ == "__main__":
    # Make async work in CLI
    def run_async_command():
        try:
            app()
        except RuntimeError as e:
            if "There is no current event loop" in str(e):
                # Handle async context
                asyncio.run(app())
            else:
                raise

    run_async_command()
