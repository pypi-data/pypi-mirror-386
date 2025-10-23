"""CLI commands for provider management and intelligent routing."""

from typing import Optional

import typer
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..billing.clerk_integration import get_clerk_client
from ..config.manager import get_config
from ..providers.router import TaskType, get_provider_router

app = typer.Typer(
    name="providers", help="🔀 Provider routing and configuration management"
)
console = Console()


@app.command("list")
def list_providers():
    """List all configured AI providers with status."""
    router = get_provider_router()
    status = router.get_provider_status()

    console.print("\n")
    console.print("╔══════════════════════════════════════╗", style="bright_cyan")
    console.print("║ DOORMAN.EXE ▮▮▮ PROVIDER STATUS ▮▮▮ ║", style="bright_cyan")
    console.print("╚══════════════════════════════════════╝", style="bright_cyan")

    # Summary stats
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Metric", style="bright_white")
    summary_table.add_column("Value", style="bright_green")

    summary_table.add_row("Total Providers", str(status["total_providers"]))
    summary_table.add_row("Active Providers", str(status["active_providers"]))
    summary_table.add_row(
        "Discovered Configs", ", ".join([p.value for p in status["discovered_configs"]])
    )

    console.print("\n▮▮▮ PROVIDER SUMMARY ▮▮▮")
    console.print(summary_table)

    # Provider details
    console.print("\n▮▮▮ PROVIDER DETAILS ▮▮▮")

    provider_table = Table()
    provider_table.add_column("Provider", style="bright_cyan")
    provider_table.add_column("Status", style="bright_white")
    provider_table.add_column("API Key", style="bright_white")
    provider_table.add_column("Models", style="bright_white")
    provider_table.add_column("Speed", style="bright_white")
    provider_table.add_column("Source", style="bright_white")

    for provider_name, info in status["providers"].items():
        status_emoji = "🟢" if info["enabled"] and info["has_api_key"] else "🔴"
        api_key_status = "✅ Configured" if info["has_api_key"] else "❌ Missing"

        provider_table.add_row(
            provider_name.upper(),
            f"{status_emoji} {'Active' if info['enabled'] and info['has_api_key'] else 'Inactive'}",
            api_key_status,
            str(info["models_available"]),
            f"{info['speed_score']}/10",
            info["source"],
        )

    console.print(provider_table)

    if status["active_providers"] == 0:
        console.print(
            "\n⚠️  No active providers found. Run [bold]doorman config doctor[/] for setup help."
        )


@app.command("route")
def show_routing(
    task: str = typer.Argument(..., help="Task description to route"),
    task_type: Optional[str] = typer.Option(
        None, help="Override task type (coding, writing, analysis, creative, reasoning)"
    ),
    max_cost: Optional[float] = typer.Option(None, help="Maximum cost per plan"),
    require_speed: bool = typer.Option(False, help="Prioritize speed over cost"),
):
    """Show optimal provider routing for a task."""
    router = get_provider_router()

    # Determine task type
    if task_type:
        try:
            task_enum = TaskType(task_type.lower())
        except ValueError:
            console.print(f"❌ Invalid task type: {task_type}")
            console.print("Valid types: coding, writing, analysis, creative, reasoning")
            return
    else:
        # Simple heuristic for task type classification
        task_lower = task.lower()
        if any(
            word in task_lower
            for word in ["code", "program", "script", "debug", "api", "function"]
        ):
            task_enum = TaskType.CODING
        elif any(
            word in task_lower
            for word in ["write", "blog", "article", "content", "copy"]
        ):
            task_enum = TaskType.WRITING
        elif any(
            word in task_lower
            for word in ["analyze", "research", "study", "compare", "evaluate"]
        ):
            task_enum = TaskType.ANALYSIS
        elif any(
            word in task_lower
            for word in ["create", "design", "brainstorm", "imagine", "story"]
        ):
            task_enum = TaskType.CREATIVE
        else:
            task_enum = TaskType.REASONING

    try:
        # Get optimal routing
        provider_type, model_name, estimated_cost = router.get_optimal_provider(
            task_type=task_enum,
            estimated_tokens=1000,  # Default estimation
            max_cost=max_cost,
            require_speed=require_speed,
        )

        console.print("\n")
        console.print("╔══════════════════════════════════════╗", style="bright_cyan")
        console.print("║ DOORMAN.EXE ▮▮▮ SMART ROUTING ▮▮▮  ║", style="bright_cyan")
        console.print("╚══════════════════════════════════════╝", style="bright_cyan")

        # Task info
        task_panel = Panel(
            f"[bold]Task:[/] {task}\n"
            f"[bold]Type:[/] {task_enum.value}\n"
            f"[bold]Speed Priority:[/] {'Yes' if require_speed else 'No'}",
            title="▮ Task Analysis ▮",
            border_style="bright_green",
        )

        # Optimal routing
        routing_panel = Panel(
            f"[bold]Provider:[/] {provider_type.value.upper()}\n"
            f"[bold]Model:[/] {model_name}\n"
            f"[bold]Estimated Cost:[/] ${estimated_cost:.4f}",
            title="▮ Optimal Route ▮",
            border_style="bright_yellow",
        )

        console.print(Columns([task_panel, routing_panel], equal=True))

        # Cost comparison
        console.print("\n▮▮▮ COST COMPARISON ▮▮▮")
        cost_comparison = router.estimate_task_cost(
            task_enum, 800, 200
        )  # Estimate input/output tokens

        cost_table = Table()
        cost_table.add_column("Provider", style="bright_cyan")
        cost_table.add_column("Estimated Cost", style="bright_white")
        cost_table.add_column("Status", style="bright_white")

        for provider, cost in cost_comparison.items():
            status = "🎯 Selected" if provider == provider_type else "💰 Alternative"
            cost_table.add_row(provider.value.upper(), f"${cost:.4f}", status)

        console.print(cost_table)

    except RuntimeError as e:
        console.print(f"❌ Routing failed: {e}")
        console.print("Run [bold]doorman providers list[/] to check provider status")


@app.command("discover")
def discover_configs():
    """Discover existing CLI configurations from Claude, Gemini, etc."""
    router = get_provider_router()
    discovered = router.config_manager.discover_existing_configs()

    console.print("\n")
    console.print("╔══════════════════════════════════════╗", style="bright_cyan")
    console.print("║ DOORMAN.EXE ▮▮▮ CONFIG DISCOVERY ▮▮▮ ║", style="bright_cyan")
    console.print("╚══════════════════════════════════════╝", style="bright_cyan")

    if not discovered:
        console.print("\n❌ No existing CLI configurations found.")
        console.print("\nSearched locations:")
        console.print("  • ~/.config/claude/config.json")
        console.print("  • ~/.config/gemini/config.json")
        console.print("  • ~/.openrouter_api_key")
        console.print("  • ANTHROPIC_API_KEY environment variable")
        console.print("  • OPENROUTER_API_KEY environment variable")
        return

    console.print(f"\n✅ Discovered {len(discovered)} provider configurations:")

    for provider_type, config in discovered.items():
        provider_name = provider_type.value.upper()
        api_key_masked = (
            f"{'*' * 20}...{config['api_key'][-8:]}"
            if config.get("api_key")
            else "Not found"
        )

        panel = Panel(
            f"[bold]Provider:[/] {provider_name}\n"
            f"[bold]API Key:[/] {api_key_masked}\n"
            f"[bold]Model:[/] {config.get('model', 'default')}\n"
            f"[bold]Source:[/] {config.get('source', 'unknown')}",
            title=f"▮ {provider_name} Configuration ▮",
            border_style="bright_green",
        )
        console.print(panel)

    console.print(
        "\n🔀 These configurations are automatically used for intelligent routing."
    )
    console.print(
        "Run [bold]doorman providers route 'your task'[/] to see optimal routing."
    )


@app.command("billing")
def show_billing_status(
    user_id: Optional[str] = typer.Option(None, help="User ID for billing check"),
):
    """Show billing status and subscription information."""
    clerk_client = get_clerk_client()

    # Use default user ID if not provided
    if not user_id:
        config = get_config()
        user_id = config.user_id or "default_user"

    console.print("\n")
    console.print("╔══════════════════════════════════════╗", style="bright_cyan")
    console.print("║ DOORMAN.EXE ▮▮▮ BILLING STATUS ▮▮▮  ║", style="bright_cyan")
    console.print("╚══════════════════════════════════════╝", style="bright_cyan")

    try:
        # Get user billing info
        billing = clerk_client.get_user_billing(user_id)

        # Subscription info
        subscription_panel = Panel(
            f"[bold]Tier:[/] {billing.subscription_tier.value.upper()}\n"
            f"[bold]User ID:[/] {billing.user_id}\n"
            f"[bold]Clerk ID:[/] {billing.clerk_user_id or 'Not linked'}\n"
            f"[bold]Subscription ID:[/] {billing.subscription_id or 'None'}",
            title="▮ Subscription Details ▮",
            border_style="bright_green",
        )

        # Usage limits
        usage_panel = Panel(
            f"[bold]Daily Plans:[/] {billing.current_usage.get('plans_today', 0)}/{billing.usage_limits['plans_per_day']}\n"
            f"[bold]Monthly Plans:[/] {billing.current_usage.get('plans_this_month', 0)}/{billing.usage_limits['plans_per_month']}\n"
            f"[bold]Cost Per Plan:[/] ${billing.usage_limits['cost_per_plan']:.2f} max\n"
            f"[bold]Monthly Spend:[/] ${billing.monthly_spend:.2f}",
            title="▮ Usage & Limits ▮",
            border_style="bright_yellow",
        )

        console.print(Columns([subscription_panel, usage_panel], equal=True))

        # Feature access
        console.print("\n▮▮▮ FEATURE ACCESS ▮▮▮")
        features_table = Table()
        features_table.add_column("Feature", style="bright_cyan")
        features_table.add_column("Access", style="bright_white")

        features = [
            ("Custom Agents", "custom_agents"),
            ("Priority Queue", "priority_queue"),
            ("Team Spaces", "team_spaces"),
            ("Advanced Analytics", "advanced_analytics"),
            ("API Access", "api_access"),
        ]

        for feature_name, feature_key in features:
            has_access = clerk_client.check_feature_access(user_id, feature_key)
            access_status = "✅ Enabled" if has_access else "🔒 Premium Required"
            features_table.add_row(feature_name, access_status)

        console.print(features_table)

        # Quota check
        allowed, quota_info = clerk_client.check_usage_quota(user_id)

        if not allowed:
            console.print("\n⚠️  [bold red]Usage quota exceeded![/]")
            if quota_info["daily_usage"]["percentage"] >= 100:
                console.print(
                    f"Daily limit reached: {quota_info['daily_usage']['used']}/{quota_info['daily_usage']['limit']}"
                )
            if quota_info["monthly_usage"]["percentage"] >= 100:
                console.print(
                    f"Monthly limit reached: {quota_info['monthly_usage']['used']}/{quota_info['monthly_usage']['limit']}"
                )

            console.print("\n💳 Consider upgrading to Premium for higher limits:")
            console.print("   doorman billing upgrade premium")
        else:
            remaining_daily = quota_info["daily_usage"]["remaining"]
            remaining_monthly = quota_info["monthly_usage"]["remaining"]
            console.print("\n✅ Quota Status: [bright_green]Within limits[/]")
            console.print(f"   Daily remaining: {remaining_daily} plans")
            console.print(f"   Monthly remaining: {remaining_monthly} plans")

    except Exception as e:
        console.print(f"❌ Failed to get billing status: {e}")
        console.print("Check your Clerk configuration and API keys.")


@app.command("plans")
def list_subscription_plans():
    """List available subscription plans."""
    clerk_client = get_clerk_client()

    console.print("\n")
    console.print("╔══════════════════════════════════════╗", style="bright_cyan")
    console.print("║ DOORMAN.EXE ▮▮▮ SUBSCRIPTION PLANS ▮▮▮ ║", style="bright_cyan")
    console.print("╚══════════════════════════════════════╝", style="bright_cyan")

    try:
        plans = clerk_client.list_plans()

        for plan in plans:
            features = plan.get("features", {})
            price = plan.get("price", 0)

            # Plan header
            if price == 0:
                price_text = "FREE"
                border_style = "bright_green"
            elif price < 100:
                price_text = f"${price:.0f}/month"
                border_style = "bright_yellow"
            else:
                price_text = f"${price:.0f}/month"
                border_style = "bright_red"

            # Feature list
            feature_text = ""
            if features.get("max_plans_per_day"):
                feature_text += f"• {features['max_plans_per_day']} plans/day\n"
            if features.get("max_plans_per_month"):
                feature_text += f"• {features['max_plans_per_month']} plans/month\n"
            if features.get("max_cost_per_plan"):
                feature_text += (
                    f"• ${features['max_cost_per_plan']:.2f} max cost/plan\n"
                )
            if features.get("custom_agents"):
                feature_text += "• Custom agents\n"
            if features.get("priority_queue"):
                feature_text += "• Priority queue\n"
            if features.get("team_spaces"):
                feature_text += "• Team collaboration\n"
            if features.get("advanced_analytics"):
                feature_text += "• Advanced analytics\n"
            if features.get("api_access"):
                feature_text += "• API access\n"

            support = features.get("support_level", "community").title()
            feature_text += f"• {support} support"

            plan_panel = Panel(
                feature_text,
                title=f"▮ {plan['name']} - {price_text} ▮",
                border_style=border_style,
            )
            console.print(plan_panel)

        console.print("\n💳 To upgrade: [bold]doorman billing upgrade <plan_name>[/]")
        console.print("📊 Current status: [bold]doorman providers billing[/]")

    except Exception as e:
        console.print(f"❌ Failed to list plans: {e}")


if __name__ == "__main__":
    app()
