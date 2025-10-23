"""CLI authentication commands for device linking and token management."""

import json
import webbrowser
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import get_config_dir

console = Console()
auth_app = typer.Typer(help="Authentication and subscription management")


class AuthClient:
    """Client for device authentication flow."""

    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.auth_file = get_config_dir() / "auth.json"

    def save_tokens(self, tokens: dict):
        """Save authentication tokens to file."""
        self.auth_file.parent.mkdir(exist_ok=True)
        with open(self.auth_file, "w") as f:
            json.dump(tokens, f, indent=2)

    def load_tokens(self) -> Optional[dict]:
        """Load authentication tokens from file."""
        if not self.auth_file.exists():
            return None

        try:
            with open(self.auth_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def clear_tokens(self):
        """Clear saved authentication tokens."""
        if self.auth_file.exists():
            self.auth_file.unlink()

    async def start_device_flow(self) -> dict:
        """Start device authentication flow."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/device/start", json={"client_id": "doorman-cli"}
            )
            response.raise_for_status()
            return response.json()

    async def poll_authorization(
        self, device_code: str, interval: int = 5
    ) -> Optional[dict]:
        """Poll for authorization completion."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/device/poll",
                json={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                },
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 428:  # Authorization pending
                return None
            elif response.status_code == 403:  # Denied
                raise typer.Exit("Authorization was denied by user")
            elif response.status_code == 400:  # Expired
                raise typer.Exit("Device code has expired. Please try again.")
            else:
                response.raise_for_status()

    async def get_subscription_info(self, access_token: str) -> dict:
        """Get user subscription information."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/me/subscription",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()


@auth_app.command("link")
def link_device(
    api_base: str = typer.Option(
        "http://localhost:8000", "--api-base", help="API base URL"
    ),
    auto_open: bool = typer.Option(
        True, "--auto-open/--no-auto-open", help="Automatically open browser"
    ),
):
    """Link this device with your Doorman account."""
    import asyncio

    async def _link():
        client = AuthClient(api_base)

        try:
            # Start device flow
            console.print("🔗 Starting device authentication flow...", style="cyan")
            flow_data = await client.start_device_flow()

            # Display user code
            console.print()
            console.print(
                Panel.fit(
                    f"[bold white]{flow_data['user_code']}[/bold white]",
                    title="[cyan]Your Device Code[/cyan]",
                    border_style="cyan",
                )
            )

            console.print()
            console.print(
                f"📱 Go to: [bold blue]{flow_data['verification_uri']}[/bold blue]"
            )
            console.print(f"⏱️  Code expires in {flow_data['expires_in'] // 60} minutes")
            console.print()

            # Auto-open browser
            if auto_open:
                try:
                    webbrowser.open(flow_data["verification_uri_complete"])
                    console.print("🌐 Opened browser for authorization")
                except Exception:
                    console.print("❌ Could not open browser automatically")
                console.print()

            # Poll for authorization
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Waiting for authorization...", total=None)

                timeout = flow_data["expires_in"]
                interval = flow_data["interval"]
                elapsed = 0

                while elapsed < timeout:
                    await asyncio.sleep(interval)
                    elapsed += interval

                    tokens = await client.poll_authorization(
                        flow_data["device_code"], interval
                    )
                    if tokens:
                        progress.stop()
                        break

                    # Update progress
                    remaining = timeout - elapsed
                    progress.update(
                        task,
                        description=f"Waiting for authorization... ({remaining}s remaining)",
                    )

                else:
                    raise typer.Exit("❌ Device code expired. Please try again.")

            # Save tokens
            client.save_tokens(tokens)

            # Get subscription info
            subscription = await client.get_subscription_info(tokens["access_token"])

            console.print()
            console.print("✅ [green]Device linked successfully![/green]")
            console.print()
            console.print(f"📧 Email: [bold]{tokens.get('email', 'N/A')}[/bold]")
            console.print(f"🎫 Tier: [bold]{subscription['tier'].upper()}[/bold]")
            console.print(f"📊 Features: {', '.join(subscription['features'])}")
            console.print()

        except httpx.HTTPError as e:
            console.print(f"❌ [red]Network error: {e}[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"❌ [red]Error: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_link())


@auth_app.command("status")
def auth_status(
    api_base: str = typer.Option(
        "http://localhost:8000", "--api-base", help="API base URL"
    ),
):
    """Show authentication and subscription status."""
    import asyncio

    async def _status():
        client = AuthClient(api_base)
        tokens = client.load_tokens()

        if not tokens:
            console.print(
                "❌ [red]Not authenticated. Run 'doorman auth link' to get started.[/red]"
            )
            return

        try:
            # Get subscription info
            subscription = await client.get_subscription_info(tokens["access_token"])

            console.print()
            console.print(
                Panel.fit(
                    f"[green]✅ Authenticated[/green]\n\n"
                    f"📧 Email: [bold]{tokens.get('email', 'N/A')}[/bold]\n"
                    f"🎫 Tier: [bold]{subscription['tier'].upper()}[/bold]\n"
                    f"📊 Status: [bold]{subscription['status'].upper()}[/bold]\n"
                    f"👥 Seats: [bold]{subscription['seats']}[/bold]\n"
                    f"🔧 Features: {', '.join(subscription['features'])}",
                    title="[cyan]Doorman Account[/cyan]",
                    border_style="green",
                )
            )
            console.print()

        except httpx.HTTPError as e:
            if "401" in str(e):
                console.print(
                    "❌ [red]Authentication expired. Run 'doorman auth link' to re-authenticate.[/red]"
                )
                client.clear_tokens()
            else:
                console.print(f"❌ [red]Error: {e}[/red]")
            raise typer.Exit(1)

    asyncio.run(_status())


@auth_app.command("logout")
def logout():
    """Log out and clear authentication tokens."""
    client = AuthClient()

    if not client.auth_file.exists():
        console.print("ℹ️  [yellow]Not currently authenticated.[/yellow]")
        return

    client.clear_tokens()
    console.print("✅ [green]Logged out successfully![/green]")


@auth_app.command("upgrade")
def upgrade(
    tier: Optional[str] = typer.Argument(None, help="Target subscription tier"),
    api_base: str = typer.Option(
        "http://localhost:8000", "--api-base", help="API base URL"
    ),
):
    """Upgrade your subscription or open billing portal."""
    import asyncio

    async def _upgrade():
        client = AuthClient(api_base)
        tokens = client.load_tokens()

        if not tokens:
            console.print(
                "❌ [red]Not authenticated. Run 'doorman auth link' first.[/red]"
            )
            raise typer.Exit(1)

        if tier:
            # Create checkout session for specific tier
            price_ids = {
                "premium": "price_premium_monthly",
                "enterprise": "price_enterprise_monthly",
            }

            if tier.lower() not in price_ids:
                console.print(
                    f"❌ [red]Invalid tier: {tier}. Available: premium, enterprise[/red]"
                )
                raise typer.Exit(1)

            try:
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.post(
                        f"{api_base}/checkout",
                        json={
                            "price_id": price_ids[tier.lower()],
                            "email": tokens.get("email", ""),
                        },
                        headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    )
                    response.raise_for_status()
                    checkout = response.json()

                console.print(
                    f"🛒 [cyan]Opening checkout for {tier.upper()} tier...[/cyan]"
                )
                webbrowser.open(checkout["checkout_url"])

            except httpx.HTTPError as e:
                console.print(f"❌ [red]Error creating checkout: {e}[/red]")
                raise typer.Exit(1)
        else:
            # Open billing portal
            try:
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.post(
                        f"{api_base}/billing/portal",
                        headers={"Authorization": f"Bearer {tokens['access_token']}"},
                    )
                    response.raise_for_status()
                    portal = response.json()

                console.print("💳 [cyan]Opening billing portal...[/cyan]")
                webbrowser.open(portal["portal_url"])

            except httpx.HTTPError as e:
                console.print(f"❌ [red]Error opening portal: {e}[/red]")
                raise typer.Exit(1)

    asyncio.run(_upgrade())


if __name__ == "__main__":
    auth_app()
