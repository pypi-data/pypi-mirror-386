"""Billing manager for Doorman subscriptions and usage tracking."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# from doorman.core.database import get_database  # Disable for now
from .models import (
    BillingConfig,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    UsageEntry,
)
from .providers import (
    MockBillingProvider,
    SimpleLicenseProvider,
    StripeBillingProvider,
)

# Re-export for convenience

logger = logging.getLogger(__name__)


class SimpleBillingDB:
    """Simple file-based database for billing (MVP implementation)."""

    def __init__(self):
        self.data_dir = Path.home() / ".doorman" / "billing"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, table: str) -> Path:
        return self.data_dir / f"{table}.json"

    def _load_table(self, table: str) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(table)
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return []

    def _save_table(self, table: str, data: List[Dict[str, Any]]):
        file_path = self._get_file_path(table)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        records = self._load_table(table)
        data["id"] = len(records) + 1
        data["created_at"] = datetime.now().isoformat()
        records.append(data)
        self._save_table(table, records)
        return data

    async def select(self, table: str, condition: str = None) -> List[Dict[str, Any]]:
        records = self._load_table(table)
        # Simple condition parsing for user_id
        if condition and "user_id" in condition:
            user_id = condition.split("'")[1]  # Extract user_id from condition
            return [r for r in records if r.get("user_id") == user_id]
        return records

    async def update(
        self, table: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        records = self._load_table(table)
        for i, record in enumerate(records):
            if str(record.get("id")) == str(record_id):
                records[i].update(data)
                self._save_table(table, records)
                return records[i]
        return {}

    async def query(
        self, sql: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        # Simple query implementation for usage tracking
        if "usage_entries" in sql and "COUNT(*)" in sql:
            records = self._load_table("usage_entries")
            user_id = params.get("user_id") if params else None
            resource_type = params.get("resource_type") if params else None

            filtered = records
            if user_id:
                filtered = [r for r in filtered if r.get("user_id") == user_id]
            if resource_type:
                filtered = [
                    r for r in filtered if r.get("resource_type") == resource_type
                ]

            # Simple date filtering
            if "DATE(timestamp)" in sql and params.get("date"):
                date_str = params["date"]
                filtered = [
                    r for r in filtered if r.get("timestamp", "").startswith(date_str)
                ]

            if "timestamp >=" in sql and params.get("start_date"):
                start_date = params["start_date"]
                filtered = [r for r in filtered if r.get("timestamp", "") >= start_date]

            return [{"count": len(filtered)}]

        return []


class UsageTracker:
    """Tracks usage against subscription quotas."""

    def __init__(self, db):
        self.db = db

    async def record_usage(
        self,
        user_id: str,
        resource_type: str,
        tokens_consumed: int = 0,
        cost_usd: float = 0.0,
        metadata: Dict[str, Any] = None,
    ) -> UsageEntry:
        """Record usage of a resource."""

        entry = UsageEntry(
            user_id=user_id,
            subscription_id=user_id,  # Simplified for MVP
            resource_type=resource_type,
            tokens_consumed=tokens_consumed,
            cost_usd=cost_usd,
            metadata=metadata or {},
        )

        # Store in database
        await self.db.create("usage_entries", entry.model_dump())

        logger.info(f"Recorded usage: {resource_type} for user {user_id}")
        return entry

    async def get_daily_usage(self, user_id: str, resource_type: str) -> int:
        """Get daily usage count for a resource type."""

        today = datetime.now().date()
        query = """
        SELECT COUNT(*) as count FROM usage_entries 
        WHERE user_id = $user_id 
        AND resource_type = $resource_type
        AND DATE(timestamp) = $date
        """

        result = await self.db.query(
            query,
            {
                "user_id": user_id,
                "resource_type": resource_type,
                "date": today.isoformat(),
            },
        )

        return result[0]["count"] if result else 0

    async def get_monthly_usage(self, user_id: str, resource_type: str) -> int:
        """Get monthly usage count for a resource type."""

        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = """
        SELECT COUNT(*) as count FROM usage_entries 
        WHERE user_id = $user_id 
        AND resource_type = $resource_type
        AND timestamp >= $start_date
        """

        result = await self.db.query(
            query,
            {
                "user_id": user_id,
                "resource_type": resource_type,
                "start_date": start_of_month.isoformat(),
            },
        )

        return result[0]["count"] if result else 0

    async def check_quota(
        self, user_id: str, subscription: Subscription, resource_type: str
    ) -> bool:
        """Check if user has quota remaining for resource type."""

        quota = subscription.get_quota()

        if resource_type == "plan":
            daily_count = await self.get_daily_usage(user_id, resource_type)
            monthly_count = await self.get_monthly_usage(user_id, resource_type)

            return (
                daily_count < quota.plans_per_day
                and monthly_count < quota.plans_per_month
            )

        elif resource_type == "custom_agent":
            return quota.custom_agents

        elif resource_type == "custom_pattern":
            return quota.custom_patterns

        # Default to allowing for unknown resource types
        return True


class BillingManager:
    """Main billing manager for Doorman."""

    def __init__(self, config: Optional[BillingConfig] = None):
        self.config = config or BillingConfig()
        self.db = None
        self.usage_tracker = None

        # Initialize billing provider
        if self.config.provider == "stripe":
            self.provider = StripeBillingProvider(self.config)
        elif self.config.provider == "mock":
            self.provider = MockBillingProvider(self.config)
        else:
            self.provider = SimpleLicenseProvider(self.config)

        # Cache for subscription data
        self._subscription_cache: Dict[str, Subscription] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    async def initialize(self):
        """Initialize the billing manager."""
        # Use simple file-based storage for now
        self.db = SimpleBillingDB()
        self.usage_tracker = UsageTracker(self.db)
        logger.info(f"Initialized BillingManager with provider: {self.config.provider}")

    async def get_subscription(
        self,
        user_id: str,
        license_key: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Subscription:
        """Get user subscription with caching."""

        cache_key = f"{user_id}:{license_key or 'none'}"

        # Check cache first
        if not force_refresh and cache_key in self._subscription_cache:
            cached_subscription = self._subscription_cache[cache_key]
            cache_expiry = self._cache_expiry.get(cache_key, datetime.min)

            # Use cached if still valid and doesn't need verification
            if (
                datetime.now() < cache_expiry
                and not cached_subscription.needs_verification
                and (
                    cached_subscription.is_active
                    or cached_subscription.is_in_grace_period
                )
            ):
                return cached_subscription

        # Try to load from database first
        try:
            db_subscriptions = await self.db.select(
                "subscriptions", f"user_id = '{user_id}'"
            )
            if db_subscriptions:
                stored_subscription = Subscription(**db_subscriptions[0])

                # If stored subscription is recent and valid, use it
                if (
                    stored_subscription.last_verified
                    and not stored_subscription.needs_verification
                    and (
                        stored_subscription.is_active
                        or stored_subscription.is_in_grace_period
                    )
                ):
                    self._subscription_cache[cache_key] = stored_subscription
                    self._cache_expiry[cache_key] = datetime.now() + timedelta(
                        hours=self.config.cache_duration_hours
                    )
                    return stored_subscription

        except Exception as e:
            logger.warning(f"Failed to load subscription from database: {e}")

        # Validate with provider
        try:
            if license_key:
                subscription = await self.provider.validate_subscription(
                    user_id, license_key
                )
            else:
                # Create free subscription
                subscription = await self.provider.create_subscription(
                    user_id, SubscriptionTier.FREE
                )

            # Store in database
            await self._store_subscription(subscription)

            # Cache the result
            self._subscription_cache[cache_key] = subscription
            self._cache_expiry[cache_key] = datetime.now() + timedelta(
                hours=self.config.cache_duration_hours
            )

            return subscription

        except Exception as e:
            logger.error(f"Failed to validate subscription: {e}")

            # Return a free subscription as fallback
            fallback_subscription = Subscription(
                user_id=user_id,
                tier=SubscriptionTier.FREE,
                status=SubscriptionStatus.ACTIVE,
                metadata={"error": str(e), "fallback": True},
            )

            return fallback_subscription

    async def _store_subscription(self, subscription: Subscription):
        """Store subscription in database."""
        try:
            # Use upsert operation
            existing = await self.db.select(
                "subscriptions", f"user_id = '{subscription.user_id}'"
            )

            if existing:
                await self.db.update(
                    "subscriptions", existing[0]["id"], subscription.model_dump()
                )
            else:
                await self.db.create("subscriptions", subscription.model_dump())

        except Exception as e:
            logger.error(f"Failed to store subscription: {e}")

    async def check_feature_access(
        self, user_id: str, feature: str, license_key: Optional[str] = None
    ) -> bool:
        """Check if user has access to a specific feature."""

        subscription = await self.get_subscription(user_id, license_key)
        quota = subscription.get_quota()

        feature_mapping = {
            "custom_agents": quota.custom_agents,
            "custom_patterns": quota.custom_patterns,
            "priority_queue": quota.priority_queue,
            "team_spaces": quota.team_spaces,
            "sprite_customization": quota.sprite_customization,
        }

        return feature_mapping.get(
            feature, True
        )  # Default to allowing unknown features

    async def check_usage_quota(
        self, user_id: str, resource_type: str, license_key: Optional[str] = None
    ) -> bool:
        """Check if user has quota remaining for a resource."""

        subscription = await self.get_subscription(user_id, license_key)
        return await self.usage_tracker.check_quota(
            user_id, subscription, resource_type
        )

    async def record_usage(
        self,
        user_id: str,
        resource_type: str,
        tokens_consumed: int = 0,
        cost_usd: float = 0.0,
        metadata: Dict[str, Any] = None,
    ) -> UsageEntry:
        """Record usage of a resource."""
        return await self.usage_tracker.record_usage(
            user_id, resource_type, tokens_consumed, cost_usd, metadata
        )

    async def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Get usage summary for a user."""

        subscription = await self.get_subscription(user_id)
        quota = subscription.get_quota()

        # Get current usage
        daily_plans = await self.usage_tracker.get_daily_usage(user_id, "plan")
        monthly_plans = await self.usage_tracker.get_monthly_usage(user_id, "plan")

        return {
            "subscription": {
                "tier": subscription.tier.value,
                "status": subscription.status.value,
                "expires_at": subscription.expires_at.isoformat()
                if subscription.expires_at
                else None,
                "is_active": subscription.is_active,
            },
            "quota": {
                "plans_per_day": quota.plans_per_day,
                "plans_per_month": quota.plans_per_month,
                "custom_agents": quota.custom_agents,
                "custom_patterns": quota.custom_patterns,
                "priority_queue": quota.priority_queue,
                "team_spaces": quota.team_spaces,
            },
            "usage": {
                "plans_today": daily_plans,
                "plans_this_month": monthly_plans,
                "plans_remaining_today": max(0, quota.plans_per_day - daily_plans),
                "plans_remaining_month": max(0, quota.plans_per_month - monthly_plans),
            },
        }

    def get_upgrade_url(self, user_id: str, target_tier: SubscriptionTier) -> str:
        """Get URL for upgrading subscription."""
        return self.provider.get_upgrade_url(user_id, target_tier)

    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user subscription."""

        try:
            subscription = await self.get_subscription(user_id)

            # Cancel with provider
            success = await self.provider.cancel_subscription(subscription.user_id)

            if success:
                # Update local subscription
                subscription.status = SubscriptionStatus.CANCELLED
                await self._store_subscription(subscription)

                # Clear cache
                cache_keys_to_remove = [
                    key
                    for key in self._subscription_cache.keys()
                    if key.startswith(f"{user_id}:")
                ]
                for key in cache_keys_to_remove:
                    del self._subscription_cache[key]
                    del self._cache_expiry[key]

            return success

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False


# Global billing manager instance
_billing_manager: Optional[BillingManager] = None


async def get_billing_manager(config: Optional[BillingConfig] = None) -> BillingManager:
    """Get global billing manager instance."""
    global _billing_manager

    if _billing_manager is None:
        _billing_manager = BillingManager(config)
        await _billing_manager.initialize()

    return _billing_manager
