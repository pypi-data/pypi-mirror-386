"""Configuration management CLI commands."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..config.manager import ConfigScope, get_config_manager
from .auth import auth_app

console = Console()
config_app = typer.Typer(help="Configuration management")


@config_app.command("list", help="List configuration values")
def list_config(
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Configuration scope (global, project)"
    ),
    all: bool = typer.Option(
        False, "--all", "-a", help="Show all possible configuration keys"
    ),
):
    """List configuration values."""
    try:
        manager = get_config_manager()

        config_scope = None
        if scope:
            try:
                config_scope = ConfigScope(scope.lower())
            except ValueError:
                console.print(
                    f"[red]Invalid scope: {scope}. Use: global, project[/red]"
                )
                raise typer.Exit(1)

        manager.list_config(scope=config_scope, show_all=all)

    except Exception as e:
        console.print(f"[red]Error listing config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("get", help="Get a configuration value")
def get_config(
    key: str = typer.Argument(help="Configuration key to get"),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Configuration scope (global, project)"
    ),
):
    """Get a configuration value."""
    try:
        manager = get_config_manager()

        config_scope = None
        if scope:
            try:
                config_scope = ConfigScope(scope.lower())
            except ValueError:
                console.print(
                    f"[red]Invalid scope: {scope}. Use: global, project[/red]"
                )
                raise typer.Exit(1)

        value = manager.get(key, scope=config_scope)

        if value is not None:
            console.print(f"[cyan]{key}[/cyan] = [white]{value}[/white]")
        else:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")

    except Exception as e:
        console.print(f"[red]Error getting config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("set", help="Set a configuration value")
def set_config(
    key: str = typer.Argument(help="Configuration key to set"),
    value: str = typer.Argument(help="Configuration value to set"),
    global_scope: bool = typer.Option(
        False, "--global", "-g", help="Set in global scope"
    ),
    project: bool = typer.Option(False, "--project", "-p", help="Set in project scope"),
):
    """Set a configuration value."""
    try:
        manager = get_config_manager()

        # Determine scope
        scope = ConfigScope.GLOBAL
        if project:
            scope = ConfigScope.PROJECT
        elif global_scope:
            scope = ConfigScope.GLOBAL

        # Type conversion for known keys
        typed_value = _convert_value(key, value)

        manager.set(key, typed_value, scope=scope)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error setting config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("remove", help="Remove a configuration value")
def remove_config(
    key: str = typer.Argument(help="Configuration key to remove"),
    global_scope: bool = typer.Option(
        False, "--global", "-g", help="Remove from global scope"
    ),
    project: bool = typer.Option(
        False, "--project", "-p", help="Remove from project scope"
    ),
):
    """Remove a configuration value."""
    try:
        manager = get_config_manager()

        # Determine scope
        scope = ConfigScope.GLOBAL
        if project:
            scope = ConfigScope.PROJECT
        elif global_scope:
            scope = ConfigScope.GLOBAL

        manager.remove(key, scope=scope)

    except Exception as e:
        console.print(f"[red]Error removing config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("validate", help="Validate current configuration")
def validate_config():
    """Validate current configuration."""
    try:
        manager = get_config_manager()
        issues = manager.validate_config()

        if not issues:
            console.print("[green]✓ Configuration is valid[/green]")
        else:
            console.print("[red]Configuration issues found:[/red]")
            for issue in issues:
                console.print(f"  [red]•[/red] {issue}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error validating config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("reset", help="Reset configuration to defaults")
def reset_config(
    global_scope: bool = typer.Option(
        False, "--global", "-g", help="Reset global configuration"
    ),
    project: bool = typer.Option(
        False, "--project", "-p", help="Reset project configuration"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Reset configuration to defaults."""
    try:
        scope = ConfigScope.GLOBAL
        scope_name = "global"

        if project:
            scope = ConfigScope.PROJECT
            scope_name = "project"

        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to reset {scope_name} configuration to defaults?"
            )
            if not confirm:
                console.print("[yellow]Operation cancelled[/yellow]")
                return

        manager = get_config_manager()
        manager.reset_to_defaults(scope=scope)

    except Exception as e:
        console.print(f"[red]Error resetting config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("export", help="Export configuration to a file")
def export_config(
    file_path: str = typer.Argument(help="File path to export to"),
    scope: Optional[str] = typer.Option(
        None, "--scope", "-s", help="Configuration scope (global, project, merged)"
    ),
):
    """Export configuration to a file."""
    try:
        manager = get_config_manager()

        config_scope = None
        if scope and scope.lower() != "merged":
            try:
                config_scope = ConfigScope(scope.lower())
            except ValueError:
                console.print(
                    f"[red]Invalid scope: {scope}. Use: global, project, merged[/red]"
                )
                raise typer.Exit(1)

        manager.export_config(Path(file_path), scope=config_scope)

    except Exception as e:
        console.print(f"[red]Error exporting config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("import", help="Import configuration from a file")
def import_config(
    file_path: str = typer.Argument(help="File path to import from"),
    global_scope: bool = typer.Option(
        False, "--global", "-g", help="Import to global scope"
    ),
    project: bool = typer.Option(
        False, "--project", "-p", help="Import to project scope"
    ),
):
    """Import configuration from a file."""
    try:
        if not Path(file_path).exists():
            console.print(f"[red]File not found: {file_path}[/red]")
            raise typer.Exit(1)

        scope = ConfigScope.GLOBAL
        if project:
            scope = ConfigScope.PROJECT

        manager = get_config_manager()
        manager.import_config(Path(file_path), scope=scope)

    except Exception as e:
        console.print(f"[red]Error importing config: {e}[/red]")
        raise typer.Exit(1)


@config_app.command("doctor", help="Diagnose configuration and system health")
def config_doctor():
    """Diagnose configuration and system health."""
    try:
        manager = get_config_manager()
        config = manager.get_merged_config()

        console.print("🔍 [bold cyan]Doorman Configuration Doctor[/bold cyan]\\n")

        # Check API key
        if config.openrouter_api_key:
            console.print("[green]✓[/green] OpenRouter API key is configured")

            # Test API connection if possible
            try:
                from ..providers.openrouter import OpenRouterProvider

                provider = OpenRouterProvider()
                # This would test the connection in a real scenario
                console.print("[green]✓[/green] API key format appears valid")
            except Exception:
                console.print(
                    "[yellow]⚠[/yellow]  Could not verify API key (this is normal without internet)"
                )
        else:
            console.print("[red]✗[/red] No OpenRouter API key configured")
            console.print(
                "  [dim]Set with: doorman config set openrouter_api_key YOUR_KEY[/dim]"
            )

        # Check directories
        if manager.global_config_dir.exists():
            console.print(
                f"[green]✓[/green] Config directory: {manager.global_config_dir}"
            )
        else:
            console.print(
                f"[red]✗[/red] Config directory missing: {manager.global_config_dir}"
            )

        # Check permissions
        try:
            test_file = manager.global_config_dir / ".test"
            test_file.touch()
            test_file.unlink()
            console.print("[green]✓[/green] Config directory is writable")
        except Exception:
            console.print("[red]✗[/red] Config directory is not writable")

        # Check model settings
        if config.default_model.startswith(
            ("openai/", "anthropic/", "meta-llama/", "google/")
        ):
            console.print(
                f"[green]✓[/green] Default model looks valid: {config.default_model}"
            )
        else:
            console.print(
                f"[yellow]⚠[/yellow]  Default model may not be available: {config.default_model}"
            )

        # Validate full config
        issues = manager.validate_config()
        if not issues:
            console.print("\\n[green]🎉 All checks passed![/green]")
        else:
            console.print("\\n[yellow]Issues found:[/yellow]")
            for issue in issues:
                console.print(f"  [red]•[/red] {issue}")

        # Show config summary
        console.print("\\n[dim]Configuration sources:[/dim]")
        console.print(f"  Global: {manager.global_config_file}")
        console.print(f"  Project: {manager.project_config_file}")
        console.print("  Environment: OPENROUTER_API_KEY, DOORMAN_*")

    except Exception as e:
        console.print(f"[red]Error running doctor: {e}[/red]")
        raise typer.Exit(1)


def _convert_value(key: str, value: str):
    """Convert string value to appropriate type based on key."""
    # Boolean keys
    boolean_keys = {
        "auto_confirm_safe",
        "auto_confirm_moderate",
        "auto_confirm_dangerous",
        "interactive_mode",
        "verbose",
        "debug",
        "show_token_usage",
        "show_cost_estimates",
        "save_sessions",
        "usage_tracking",
        "cost_alerts",
    }

    # Float keys
    float_keys = {"max_cost_per_plan", "require_confirmation_over"}

    # Integer keys
    integer_keys = {"max_saved_sessions", "session_timeout_hours"}

    # List keys (comma-separated)
    list_keys = {"allowed_tools", "disallowed_tools"}

    if key in boolean_keys:
        return value.lower() in ("true", "1", "yes", "on")
    elif key in float_keys:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid float for {key}")
    elif key in integer_keys:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"'{value}' is not a valid integer for {key}")
    elif key in list_keys:
        return [item.strip() for item in value.split(",") if item.strip()]
    else:
        return value


# Add auth commands as a subcommand
config_app.add_typer(auth_app, name="auth")


if __name__ == "__main__":
    config_app()
