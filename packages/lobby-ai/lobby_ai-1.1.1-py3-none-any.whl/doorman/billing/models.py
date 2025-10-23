"""Billing data models for Doorman."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SubscriptionTier(str, Enum):
    """Subscription tiers for Doorman."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class BillingConfig(BaseModel):
    """Configuration for billing system."""

    provider: str = "simple_license"
    license_verification_url: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    cache_duration_hours: int = 24
    offline_grace_period_days: int = 7
    enable_telemetry: bool = True


class UsageQuota(BaseModel):
    """Usage quota and limits for a subscription tier."""

    tier: SubscriptionTier
    plans_per_day: int = Field(default=10, description="Daily plan generation limit")
    plans_per_month: int = Field(
        default=300, description="Monthly plan generation limit"
    )
    custom_agents: bool = Field(default=False, description="Can create custom agents")
    custom_patterns: bool = Field(
        default=False, description="Can create custom patterns"
    )
    priority_queue: bool = Field(default=False, description="Priority MCP server queue")
    team_spaces: bool = Field(default=False, description="Team collaboration features")
    api_calls_per_hour: int = Field(default=100, description="API rate limit")
    max_workflow_complexity: int = Field(
        default=5, description="Maximum workflow steps"
    )
    sprite_customization: bool = Field(
        default=False, description="Custom sprite generation"
    )

    @classmethod
    def for_tier(cls, tier: SubscriptionTier) -> "UsageQuota":
        """Get default quota for subscription tier."""
        quotas = {
            SubscriptionTier.FREE: cls(
                tier=tier,
                plans_per_day=5,
                plans_per_month=50,
                custom_agents=False,
                custom_patterns=False,
                priority_queue=False,
                team_spaces=False,
                api_calls_per_hour=50,
                max_workflow_complexity=3,
                sprite_customization=False,
            ),
            SubscriptionTier.PREMIUM: cls(
                tier=tier,
                plans_per_day=100,
                plans_per_month=3000,
                custom_agents=True,
                custom_patterns=True,
                priority_queue=True,
                team_spaces=False,
                api_calls_per_hour=500,
                max_workflow_complexity=10,
                sprite_customization=True,
            ),
            SubscriptionTier.ENTERPRISE: cls(
                tier=tier,
                plans_per_day=10000,
                plans_per_month=100000,
                custom_agents=True,
                custom_patterns=True,
                priority_queue=True,
                team_spaces=True,
                api_calls_per_hour=5000,
                max_workflow_complexity=50,
                sprite_customization=True,
            ),
        }
        return quotas.get(tier, quotas[SubscriptionTier.FREE])


class Subscription(BaseModel):
    """User subscription details."""

    user_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    license_key: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_verified: Optional[datetime] = None
    verification_failures: int = 0
    features: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE and not self.is_expired

    @property
    def needs_verification(self) -> bool:
        """Check if subscription needs re-verification."""
        if not self.last_verified:
            return True

        # Re-verify every 24 hours
        return (datetime.now() - self.last_verified) > timedelta(hours=24)

    @property
    def is_in_grace_period(self) -> bool:
        """Check if subscription is in offline grace period."""
        if not self.last_verified or self.is_active:
            return False

        # 7-day grace period for offline verification failures
        grace_period = timedelta(days=7)
        return (datetime.now() - self.last_verified) < grace_period

    def get_quota(self) -> UsageQuota:
        """Get usage quota for this subscription."""
        return UsageQuota.for_tier(self.tier)


class UsageEntry(BaseModel):
    """Usage tracking entry."""

    user_id: str
    subscription_id: str
    resource_type: str  # "plan", "api_call", "agent_creation", etc.
    resource_id: Optional[str] = None
    tokens_consumed: int = 0
    cost_usd: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BillingTransaction(BaseModel):
    """Billing transaction record."""

    transaction_id: str
    user_id: str
    subscription_id: str
    amount_usd: float
    currency: str = "USD"
    provider: str
    provider_transaction_id: Optional[str] = None
    transaction_type: str  # "subscription", "credits", "refund"
    status: str  # "pending", "completed", "failed", "refunded"
    created_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
