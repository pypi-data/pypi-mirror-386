"""TierGuard system for quota enforcement and feature gating."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel

from doorman.core.database import get_db_session
from doorman.core.models import UserTier


class FeatureFlag(str, Enum):
    """Available feature flags."""

    UNLIMITED_PLANNING = "unlimited_planning"
    CUSTOM_AGENTS = "custom_agents"
    CUSTOM_GRAPHS = "custom_graphs"
    PRIORITY_QUEUE = "priority_queue"
    TEAM_SPACES = "team_spaces"
    ADVANCED_ROUTING = "advanced_routing"
    MCP_SERVER = "mcp_server"
    WEB_UI = "web_ui"
    API_ACCESS = "api_access"
    SSO = "sso"
    ON_PREM = "on_prem"
    CUSTOM_BRANDING = "custom_branding"


class QuotaType(str, Enum):
    """Types of quotas."""

    DAILY_PLANS = "daily_plans"
    MONTHLY_PLANS = "monthly_plans"
    MAX_STEPS_PER_PLAN = "max_steps_per_plan"
    MAX_COMPONENTS_PER_PLAN = "max_components_per_plan"
    CONCURRENT_REQUESTS = "concurrent_requests"


class TierLimits(BaseModel):
    """Limits and features for each tier."""

    # Quotas
    daily_plans: int
    monthly_plans: int
    max_steps_per_plan: int
    max_components_per_plan: int
    concurrent_requests: int

    # Features
    features: List[FeatureFlag]

    # UI badges and branding
    badge_text: str
    badge_color: str
    sprite_character: str  # 16-bit character sprite name


# Tier configurations
TIER_CONFIG = {
    UserTier.FREE: TierLimits(
        daily_plans=10,
        monthly_plans=100,
        max_steps_per_plan=5,
        max_components_per_plan=10,
        concurrent_requests=2,
        features=[],
        badge_text="FREE",
        badge_color="neon_cyan",
        sprite_character="ryu_basic",  # Basic Ryu sprite
    ),
    UserTier.PREMIUM: TierLimits(
        daily_plans=100,
        monthly_plans=2000,
        max_steps_per_plan=20,
        max_components_per_plan=50,
        concurrent_requests=5,
        features=[
            FeatureFlag.UNLIMITED_PLANNING,
            FeatureFlag.CUSTOM_AGENTS,
            FeatureFlag.CUSTOM_GRAPHS,
            FeatureFlag.PRIORITY_QUEUE,
            FeatureFlag.TEAM_SPACES,
            FeatureFlag.ADVANCED_ROUTING,
            FeatureFlag.WEB_UI,
        ],
        badge_text="PREMIUM",
        badge_color="neon_magenta",
        sprite_character="chun_li_premium",  # Chun-Li sprite for premium
    ),
    UserTier.ENTERPRISE: TierLimits(
        daily_plans=1000,
        monthly_plans=20000,
        max_steps_per_plan=100,
        max_components_per_plan=200,
        concurrent_requests=20,
        features=[
            FeatureFlag.UNLIMITED_PLANNING,
            FeatureFlag.CUSTOM_AGENTS,
            FeatureFlag.CUSTOM_GRAPHS,
            FeatureFlag.PRIORITY_QUEUE,
            FeatureFlag.TEAM_SPACES,
            FeatureFlag.ADVANCED_ROUTING,
            FeatureFlag.MCP_SERVER,
            FeatureFlag.WEB_UI,
            FeatureFlag.API_ACCESS,
            FeatureFlag.SSO,
            FeatureFlag.ON_PREM,
            FeatureFlag.CUSTOM_BRANDING,
        ],
        badge_text="ENTERPRISE",
        badge_color="neon_green",
        sprite_character="ken_enterprise",  # Ken sprite for enterprise
    ),
}


class QuotaExceededError(Exception):
    """Raised when user exceeds their quota."""

    def __init__(
        self,
        quota_type: str,
        limit: int,
        current: int,
        reset_time: Optional[datetime] = None,
    ):
        self.quota_type = quota_type
        self.limit = limit
        self.current = current
        self.reset_time = reset_time
        super().__init__(f"Quota exceeded: {current}/{limit} {quota_type}")


class FeatureNotAllowedError(Exception):
    """Raised when user tries to access a feature not in their tier."""

    def __init__(self, feature: FeatureFlag, required_tier: UserTier):
        self.feature = feature
        self.required_tier = required_tier
        super().__init__(f"Feature {feature.value} requires {required_tier.value} tier")


class TierGuard:
    """Guards access to features and enforces quotas."""

    def __init__(self):
        self.concurrent_requests: Dict[UUID, int] = {}

    async def check_quota(
        self, user_id: UUID, user_tier: UserTier, quota_type: QuotaType
    ) -> Tuple[bool, int, int, Optional[datetime]]:
        """
        Check if user is within quota limits.

        Returns:
            (allowed, current_usage, limit, reset_time)
        """
        limits = TIER_CONFIG[user_tier]

        async with get_db_session() as db:
            if quota_type == QuotaType.DAILY_PLANS:
                usage_stats = await db.get_user_usage_today(user_id)
                current = usage_stats.get("total_requests", 0)
                limit = limits.daily_plans
                reset_time = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)

            elif quota_type == QuotaType.MONTHLY_PLANS:
                # TODO: Implement monthly usage query
                current = 0  # Placeholder
                limit = limits.monthly_plans
                reset_time = None  # Calculate month reset

            elif quota_type == QuotaType.CONCURRENT_REQUESTS:
                current = self.concurrent_requests.get(user_id, 0)
                limit = limits.concurrent_requests
                reset_time = None

            else:
                # Static limits (per-plan limits)
                current = 0
                if quota_type == QuotaType.MAX_STEPS_PER_PLAN:
                    limit = limits.max_steps_per_plan
                elif quota_type == QuotaType.MAX_COMPONENTS_PER_PLAN:
                    limit = limits.max_components_per_plan
                else:
                    limit = 999999  # Unlimited for unknown quotas
                reset_time = None

        allowed = current < limit
        return allowed, current, limit, reset_time

    async def enforce_quota(
        self, user_id: UUID, user_tier: UserTier, quota_type: QuotaType
    ) -> None:
        """Enforce quota and raise exception if exceeded."""
        allowed, current, limit, reset_time = await self.check_quota(
            user_id, user_tier, quota_type
        )

        if not allowed:
            raise QuotaExceededError(quota_type.value, limit, current, reset_time)

    def check_feature(self, user_tier: UserTier, feature: FeatureFlag) -> bool:
        """Check if user's tier has access to a feature."""
        return feature in TIER_CONFIG[user_tier].features

    def enforce_feature(self, user_tier: UserTier, feature: FeatureFlag) -> None:
        """Enforce feature access and raise exception if not allowed."""
        if not self.check_feature(user_tier, feature):
            # Find the minimum tier that has this feature
            required_tier = UserTier.ENTERPRISE  # Default to highest
            for tier, limits in TIER_CONFIG.items():
                if feature in limits.features:
                    required_tier = tier
                    break

            raise FeatureNotAllowedError(feature, required_tier)

    async def start_request(self, user_id: UUID, user_tier: UserTier) -> None:
        """Start tracking a concurrent request."""
        await self.enforce_quota(user_id, user_tier, QuotaType.CONCURRENT_REQUESTS)
        self.concurrent_requests[user_id] = self.concurrent_requests.get(user_id, 0) + 1

    async def end_request(self, user_id: UUID) -> None:
        """End tracking a concurrent request."""
        if user_id in self.concurrent_requests:
            self.concurrent_requests[user_id] = max(
                0, self.concurrent_requests[user_id] - 1
            )
            if self.concurrent_requests[user_id] == 0:
                del self.concurrent_requests[user_id]

    def get_tier_limits(self, user_tier: UserTier) -> TierLimits:
        """Get limits for a specific tier."""
        return TIER_CONFIG[user_tier]

    def get_upgrade_cta(
        self, user_tier: UserTier, feature: Optional[FeatureFlag] = None
    ) -> Dict[str, str]:
        """Get upgrade call-to-action message."""
        current_limits = TIER_CONFIG[user_tier]

        if user_tier == UserTier.FREE:
            next_tier = UserTier.PREMIUM
            next_limits = TIER_CONFIG[next_tier]

            return {
                "message": f"Upgrade to {next_tier.value.title()} for {next_limits.daily_plans} daily plans!",
                "cta": f"🚀 Upgrade to {next_tier.value.title()}",
                "features": [
                    f.value.replace("_", " ").title() for f in next_limits.features[:3]
                ],
                "sprite": next_limits.sprite_character,
            }

        elif user_tier == UserTier.PREMIUM:
            next_tier = UserTier.ENTERPRISE
            next_limits = TIER_CONFIG[next_tier]

            return {
                "message": f"Upgrade to {next_tier.value.title()} for unlimited scale!",
                "cta": f"💼 Upgrade to {next_tier.value.title()}",
                "features": [
                    "SSO Integration",
                    "On-Prem Deployment",
                    "Custom Branding",
                ],
                "sprite": next_limits.sprite_character,
            }

        else:
            return {
                "message": "You have the highest tier! 🎉",
                "cta": "Contact us for custom enterprise features",
                "features": [
                    "Custom Integrations",
                    "Dedicated Support",
                    "SLA Guarantees",
                ],
                "sprite": current_limits.sprite_character,
            }


class RequestContext:
    """Context manager for tracking concurrent requests."""

    def __init__(self, guard: TierGuard, user_id: UUID, user_tier: UserTier):
        self.guard = guard
        self.user_id = user_id
        self.user_tier = user_tier

    async def __aenter__(self):
        await self.guard.start_request(self.user_id, self.user_tier)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.guard.end_request(self.user_id)


# Global tier guard instance
_tier_guard: Optional[TierGuard] = None


def get_tier_guard() -> TierGuard:
    """Get global tier guard instance."""
    global _tier_guard
    if _tier_guard is None:
        _tier_guard = TierGuard()
    return _tier_guard


async def check_plan_quota(user_id: UUID, user_tier: UserTier) -> None:
    """Convenient function to check daily plan quota."""
    guard = get_tier_guard()
    await guard.enforce_quota(user_id, user_tier, QuotaType.DAILY_PLANS)


async def check_feature_access(user_tier: UserTier, feature: FeatureFlag) -> None:
    """Convenient function to check feature access."""
    guard = get_tier_guard()
    guard.enforce_feature(user_tier, feature)
