"""Billing providers for different payment and license systems."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import httpx

from .models import BillingConfig, Subscription, SubscriptionStatus, SubscriptionTier


class BillingProvider(ABC):
    """Abstract base class for billing providers."""

    def __init__(self, config: BillingConfig):
        self.config = config

    @abstractmethod
    async def validate_subscription(
        self, user_id: str, license_key: str
    ) -> Subscription:
        """Validate a subscription and return subscription details."""
        pass

    @abstractmethod
    async def create_subscription(
        self, user_id: str, tier: SubscriptionTier
    ) -> Subscription:
        """Create a new subscription."""
        pass

    @abstractmethod
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel an existing subscription."""
        pass

    @abstractmethod
    def get_upgrade_url(self, user_id: str, target_tier: SubscriptionTier) -> str:
        """Get URL for upgrading subscription."""
        pass


class SimpleLicenseProvider(BillingProvider):
    """Simple license key-based provider for MVP."""

    def __init__(self, config: BillingConfig):
        super().__init__(config)
        self.verification_url = (
            config.license_verification_url or "https://api.doorman.dev/verify"
        )

        # For MVP, we'll have some hardcoded demo keys
        self._demo_keys = {
            "DOORMAN_DEMO_PREMIUM": {
                "tier": SubscriptionTier.PREMIUM,
                "expires_at": datetime.now() + timedelta(days=30),
                "features": ["unlimited_plans", "custom_agents", "priority_queue"],
            },
            "DOORMAN_DEMO_ENTERPRISE": {
                "tier": SubscriptionTier.ENTERPRISE,
                "expires_at": datetime.now() + timedelta(days=90),
                "features": [
                    "unlimited_plans",
                    "custom_agents",
                    "priority_queue",
                    "team_spaces",
                ],
            },
        }

    async def validate_subscription(
        self, user_id: str, license_key: str
    ) -> Subscription:
        """Validate license key via API or demo keys."""

        # Check demo keys first
        if license_key in self._demo_keys:
            demo_data = self._demo_keys[license_key]
            return Subscription(
                user_id=user_id,
                tier=demo_data["tier"],
                status=SubscriptionStatus.ACTIVE,
                license_key=license_key,
                expires_at=demo_data["expires_at"],
                last_verified=datetime.now(),
                features=demo_data["features"],
                metadata={"provider": "simple_license", "demo": True},
            )

        # Try online verification
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.verification_url,
                    json={"license_key": license_key, "user_id": user_id},
                    headers={"User-Agent": "Doorman/1.0.0"},
                )

                if response.status_code == 200:
                    data = response.json()

                    return Subscription(
                        user_id=user_id,
                        tier=SubscriptionTier(data["tier"]),
                        status=SubscriptionStatus(data["status"]),
                        license_key=license_key,
                        expires_at=datetime.fromisoformat(data["expires_at"])
                        if data.get("expires_at")
                        else None,
                        last_verified=datetime.now(),
                        features=data.get("features", []),
                        metadata=data.get("metadata", {}),
                    )

                elif response.status_code == 404:
                    # Invalid license key
                    return Subscription(
                        user_id=user_id,
                        tier=SubscriptionTier.FREE,
                        status=SubscriptionStatus.INACTIVE,
                        license_key=license_key,
                        verification_failures=1,
                        metadata={"error": "Invalid license key"},
                    )

        except Exception as e:
            # Network error - allow grace period if previously verified
            return Subscription(
                user_id=user_id,
                tier=SubscriptionTier.FREE,
                status=SubscriptionStatus.INACTIVE,
                license_key=license_key,
                verification_failures=1,
                metadata={"error": str(e), "offline": True},
            )

        # Default to free tier
        return Subscription(
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            metadata={"provider": "simple_license"},
        )

    async def create_subscription(
        self, user_id: str, tier: SubscriptionTier
    ) -> Subscription:
        """Create a free subscription (paid subscriptions require external flow)."""

        if tier != SubscriptionTier.FREE:
            raise ValueError("SimpleLicenseProvider can only create FREE subscriptions")

        return Subscription(
            user_id=user_id,
            tier=SubscriptionTier.FREE,
            status=SubscriptionStatus.ACTIVE,
            created_at=datetime.now(),
            last_verified=datetime.now(),
            metadata={"provider": "simple_license"},
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription (placeholder - would call external API)."""
        # In MVP, this would just mark locally as cancelled
        return True

    def get_upgrade_url(self, user_id: str, target_tier: SubscriptionTier) -> str:
        """Get URL for purchasing upgrade."""
        base_url = "https://doorman.dev/pricing"

        pricing_urls = {
            SubscriptionTier.PREMIUM: f"{base_url}?plan=premium&user={user_id}",
            SubscriptionTier.ENTERPRISE: f"{base_url}?plan=enterprise&user={user_id}",
        }

        return pricing_urls.get(target_tier, base_url)


class StripeBillingProvider(BillingProvider):
    """Stripe-based billing provider for Phase 2."""

    def __init__(self, config: BillingConfig):
        super().__init__(config)

        if not config.stripe_secret_key:
            raise ValueError("Stripe secret key required for StripeBillingProvider")

        # Initialize Stripe (would import stripe library)
        self.stripe_key = config.stripe_secret_key

        # Price IDs for different tiers (set in Stripe dashboard)
        self.price_ids = {
            SubscriptionTier.PREMIUM: "price_premium_monthly",  # Replace with actual Stripe price ID
            SubscriptionTier.ENTERPRISE: "price_enterprise_monthly",
        }

    async def validate_subscription(
        self, user_id: str, stripe_subscription_id: str
    ) -> Subscription:
        """Validate Stripe subscription."""

        try:
            # This would use the Stripe API to fetch subscription details
            # For now, return a placeholder

            return Subscription(
                user_id=user_id,
                tier=SubscriptionTier.PREMIUM,
                status=SubscriptionStatus.ACTIVE,
                stripe_subscription_id=stripe_subscription_id,
                last_verified=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
                metadata={"provider": "stripe"},
            )

        except Exception as e:
            return Subscription(
                user_id=user_id,
                tier=SubscriptionTier.FREE,
                status=SubscriptionStatus.INACTIVE,
                verification_failures=1,
                metadata={"error": str(e)},
            )

    async def create_subscription(
        self, user_id: str, tier: SubscriptionTier
    ) -> Subscription:
        """Create Stripe subscription (placeholder)."""

        # This would create a Stripe subscription
        subscription_id = f"sub_{uuid.uuid4().hex[:24]}"

        return Subscription(
            user_id=user_id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            stripe_subscription_id=subscription_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            metadata={"provider": "stripe"},
        )

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel Stripe subscription."""
        # Would call Stripe API to cancel
        return True

    def get_upgrade_url(self, user_id: str, target_tier: SubscriptionTier) -> str:
        """Get Stripe Checkout URL."""
        # Would create Stripe Checkout session
        return f"https://checkout.stripe.com/session_placeholder?user={user_id}&tier={target_tier.value}"


class MockBillingProvider(BillingProvider):
    """Mock provider for testing."""

    def __init__(self, config: BillingConfig):
        super().__init__(config)
        self._subscriptions = {}

    async def validate_subscription(
        self, user_id: str, license_key: str
    ) -> Subscription:
        """Return mock subscription."""

        # Mock premium subscription for testing
        return Subscription(
            user_id=user_id,
            tier=SubscriptionTier.PREMIUM,
            status=SubscriptionStatus.ACTIVE,
            license_key=license_key,
            last_verified=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            features=["unlimited_plans", "custom_agents", "priority_queue"],
            metadata={"provider": "mock", "test": True},
        )

    async def create_subscription(
        self, user_id: str, tier: SubscriptionTier
    ) -> Subscription:
        """Create mock subscription."""

        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            metadata={"provider": "mock"},
        )

        self._subscriptions[user_id] = subscription
        return subscription

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel mock subscription."""
        return True

    def get_upgrade_url(self, user_id: str, target_tier: SubscriptionTier) -> str:
        """Get mock upgrade URL."""
        return f"https://example.com/upgrade?user={user_id}&tier={target_tier.value}"
