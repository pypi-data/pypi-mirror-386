"""Clerk authentication client for device linking and JWT management."""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from rich.console import Console

from ..config import get_config_dir

console = Console()


@dataclass
class ClerkTokens:
    """Clerk authentication tokens."""

    session_token: str
    user_id: str
    email: str
    subscription_tier: str
    expires_at: datetime


class ClerkAuthClient:
    """Clerk authentication client with device linking support."""

    def __init__(
        self,
        publishable_key: str = "pk_test_ZG9vcm1hbi1kZXYuY2xlcmsuYWNjb3VudHMuZGV2",
        frontend_api: str = "https://doorman-dev.clerk.accounts.dev",
    ):
        self.publishable_key = publishable_key
        self.frontend_api = frontend_api
        self.auth_file = get_config_dir() / "clerk_auth.json"

        # Clerk device flow endpoints
        self.device_auth_url = f"{frontend_api}/v1/client/sign_ins"
        self.token_url = f"{frontend_api}/v1/client/sessions"

    def save_tokens(self, tokens: ClerkTokens):
        """Save Clerk tokens to local file."""
        self.auth_file.parent.mkdir(exist_ok=True)

        data = {
            "session_token": tokens.session_token,
            "user_id": tokens.user_id,
            "email": tokens.email,
            "subscription_tier": tokens.subscription_tier,
            "expires_at": tokens.expires_at.isoformat(),
            "saved_at": datetime.now().isoformat(),
        }

        with open(self.auth_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_tokens(self) -> Optional[ClerkTokens]:
        """Load and validate Clerk tokens."""
        if not self.auth_file.exists():
            return None

        try:
            with open(self.auth_file) as f:
                data = json.load(f)

            expires_at = datetime.fromisoformat(data["expires_at"])

            # Check if token is expired
            if expires_at <= datetime.now():
                console.print(
                    "[yellow]⚠️  Session expired. Please re-authenticate.[/yellow]"
                )
                self.clear_tokens()
                return None

            return ClerkTokens(
                session_token=data["session_token"],
                user_id=data["user_id"],
                email=data["email"],
                subscription_tier=data["subscription_tier"],
                expires_at=expires_at,
            )

        except (json.JSONDecodeError, KeyError, ValueError):
            console.print("[red]❌ Invalid token data. Please re-authenticate.[/red]")
            self.clear_tokens()
            return None

    def clear_tokens(self):
        """Clear saved Clerk tokens."""
        if self.auth_file.exists():
            self.auth_file.unlink()

    async def start_device_flow(self) -> Dict[str, Any]:
        """Start Clerk device authentication flow."""
        # Mock device flow for demo (in production, this would call Clerk API)
        return {
            "verification_uri": "https://doorman.dev/auth/device",
            "verification_uri_complete": "https://doorman.dev/auth/device?code=ABCD-1234",
            "device_code": "device_mock_12345",
            "user_code": "ABCD-1234",
            "expires_in": 900,  # 15 minutes
            "interval": 5,
            "sign_in_id": "sign_in_mock",
        }

    async def poll_device_authorization(
        self, sign_in_id: str, device_code: str
    ) -> Optional[ClerkTokens]:
        """Poll Clerk for device authorization completion."""
        # Mock response for development
        if device_code == "device_mock_12345":
            import random

            # Simulate user taking time to authorize
            if random.random() > 0.7:  # 30% chance of "completion" each poll
                return ClerkTokens(
                    session_token="mock_session_token_12345",
                    user_id="user_mock_123",
                    email="user@example.com",
                    subscription_tier="premium",  # Mock premium for demo
                    expires_at=datetime.now() + timedelta(days=30),
                )

        return None  # Still pending

    async def get_subscription_info(self, session_token: str) -> Dict[str, Any]:
        """Get user subscription information from Clerk."""
        return {
            "tier": "premium",
            "status": "active",
            "features": [
                "unlimited_plans",
                "custom_agents",
                "priority_queue",
                "sprite_customization",
            ],
            "seats": 1,
            "renews_at": "2024-12-01",
        }

    async def create_checkout_session(
        self, session_token: str, price_id: str
    ) -> Dict[str, Any]:
        """Create Stripe checkout session via Clerk."""
        return {
            "checkout_url": f"https://checkout.stripe.com/c/pay/cs_test_123#{price_id}",
            "session_id": "cs_test_123",
        }

    async def get_billing_portal_url(self, session_token: str) -> str:
        """Get Stripe billing portal URL."""
        return "https://billing.stripe.com/session/bps_test_portal_123"
