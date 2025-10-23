"""Clerk Commerce billing integration for Doorman subscriptions."""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Available subscription tiers."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class UserBilling:
    """User billing information."""

    user_id: str
    clerk_user_id: Optional[str]
    subscription_tier: SubscriptionTier
    subscription_id: Optional[str]
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    usage_limits: Dict[str, int]
    current_usage: Dict[str, int]
    monthly_spend: float
    total_spend: float


@dataclass
class PlanFeatures:
    """Features available for each plan."""

    tier: SubscriptionTier
    name: str
    price_monthly: float
    max_plans_per_day: int
    max_plans_per_month: int
    max_cost_per_plan: float
    custom_agents: bool
    priority_queue: bool
    team_spaces: bool
    advanced_analytics: bool
    api_access: bool
    support_level: str


class ClerkCommerceClient:
    """Client for Clerk Commerce API integration."""

    def __init__(self):
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.publishable_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")

        if not self.secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable required")

        self.base_url = "https://api.clerk.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        # Define plan features
        self.plan_features = {
            SubscriptionTier.FREE: PlanFeatures(
                tier=SubscriptionTier.FREE,
                name="Free Developer",
                price_monthly=0.0,
                max_plans_per_day=10,
                max_plans_per_month=100,
                max_cost_per_plan=0.05,  # $0.05 per plan
                custom_agents=False,
                priority_queue=False,
                team_spaces=False,
                advanced_analytics=False,
                api_access=False,
                support_level="community",
            ),
            SubscriptionTier.PREMIUM: PlanFeatures(
                tier=SubscriptionTier.PREMIUM,
                name="Premium Pro",
                price_monthly=29.0,
                max_plans_per_day=1000,
                max_plans_per_month=10000,
                max_cost_per_plan=2.0,  # $2 per plan
                custom_agents=True,
                priority_queue=True,
                team_spaces=False,
                advanced_analytics=True,
                api_access=True,
                support_level="email",
            ),
            SubscriptionTier.ENTERPRISE: PlanFeatures(
                tier=SubscriptionTier.ENTERPRISE,
                name="Enterprise Team",
                price_monthly=299.0,
                max_plans_per_day=10000,
                max_plans_per_month=100000,
                max_cost_per_plan=10.0,  # $10 per plan
                custom_agents=True,
                priority_queue=True,
                team_spaces=True,
                advanced_analytics=True,
                api_access=True,
                support_level="priority",
            ),
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to Clerk API."""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Clerk API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def list_plans(self) -> List[Dict[str, Any]]:
        """List available subscription plans."""
        try:
            # Try to get plans from Clerk Commerce
            response = self._make_request("GET", "/commerce/plans")
            return response.get("data", [])
        except Exception as e:
            logger.warning(f"Failed to fetch Clerk Commerce plans: {e}")
            # Fallback to our internal plan definitions
            return [
                {
                    "id": f"doorman_{tier.value}",
                    "name": features.name,
                    "price": features.price_monthly,
                    "interval": "month",
                    "features": {
                        "max_plans_per_day": features.max_plans_per_day,
                        "max_plans_per_month": features.max_plans_per_month,
                        "max_cost_per_plan": features.max_cost_per_plan,
                        "custom_agents": features.custom_agents,
                        "priority_queue": features.priority_queue,
                        "team_spaces": features.team_spaces,
                        "advanced_analytics": features.advanced_analytics,
                        "api_access": features.api_access,
                        "support_level": features.support_level,
                    },
                }
                for tier, features in self.plan_features.items()
            ]

    def get_user_billing(self, user_id: str) -> UserBilling:
        """Get billing information for a user."""
        try:
            # Try to get user from Clerk
            user_response = self._make_request("GET", f"/users/{user_id}")
            clerk_user_id = user_response.get("id")

            # Try to get subscription information
            subscriptions = self._make_request(
                "GET", f"/commerce/subscriptions?user_id={clerk_user_id}"
            )

            if subscriptions.get("data"):
                subscription = subscriptions["data"][0]  # Get first active subscription
                tier_name = subscription.get("plan", {}).get("name", "free")

                # Map plan name to tier
                tier = SubscriptionTier.FREE
                if "premium" in tier_name.lower():
                    tier = SubscriptionTier.PREMIUM
                elif "enterprise" in tier_name.lower():
                    tier = SubscriptionTier.ENTERPRISE

                features = self.plan_features[tier]

                return UserBilling(
                    user_id=user_id,
                    clerk_user_id=clerk_user_id,
                    subscription_tier=tier,
                    subscription_id=subscription.get("id"),
                    current_period_start=datetime.fromisoformat(
                        subscription.get("current_period_start", "")
                    ),
                    current_period_end=datetime.fromisoformat(
                        subscription.get("current_period_end", "")
                    ),
                    usage_limits={
                        "plans_per_day": features.max_plans_per_day,
                        "plans_per_month": features.max_plans_per_month,
                        "cost_per_plan": features.max_cost_per_plan,
                    },
                    current_usage={
                        "plans_today": 0,  # Would come from our database
                        "plans_this_month": 0,  # Would come from our database
                        "tokens_this_month": 0,  # Would come from our database
                    },
                    monthly_spend=0.0,  # Would come from our database
                    total_spend=0.0,  # Would come from our database
                )

        except Exception as e:
            logger.warning(f"Failed to get user billing from Clerk: {e}")

        # Fallback to free tier
        features = self.plan_features[SubscriptionTier.FREE]
        return UserBilling(
            user_id=user_id,
            clerk_user_id=None,
            subscription_tier=SubscriptionTier.FREE,
            subscription_id=None,
            current_period_start=None,
            current_period_end=None,
            usage_limits={
                "plans_per_day": features.max_plans_per_day,
                "plans_per_month": features.max_plans_per_month,
                "cost_per_plan": features.max_cost_per_plan,
            },
            current_usage={
                "plans_today": 0,
                "plans_this_month": 0,
                "tokens_this_month": 0,
            },
            monthly_spend=0.0,
            total_spend=0.0,
        )

    def create_subscription(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Create a new subscription for a user."""
        try:
            subscription_data = {
                "user_id": user_id,
                "plan_id": plan_id,
                "payment_method_required": True,
            }

            response = self._make_request(
                "POST", "/commerce/subscriptions", subscription_data
            )
            return response

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            response = self._make_request(
                "DELETE", f"/commerce/subscriptions/{subscription_id}"
            )
            return response

        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise

    def update_subscription(self, subscription_id: str, plan_id: str) -> Dict[str, Any]:
        """Update a subscription to a new plan."""
        try:
            update_data = {"plan_id": plan_id}

            response = self._make_request(
                "PUT", f"/commerce/subscriptions/{subscription_id}", update_data
            )
            return response

        except Exception as e:
            logger.error(f"Failed to update subscription: {e}")
            raise

    def get_usage_limits(self, user_id: str) -> Dict[str, Any]:
        """Get usage limits for a user based on their subscription."""
        billing = self.get_user_billing(user_id)
        features = self.plan_features[billing.subscription_tier]

        return {
            "tier": billing.subscription_tier.value,
            "limits": billing.usage_limits,
            "current_usage": billing.current_usage,
            "features": {
                "custom_agents": features.custom_agents,
                "priority_queue": features.priority_queue,
                "team_spaces": features.team_spaces,
                "advanced_analytics": features.advanced_analytics,
                "api_access": features.api_access,
            },
            "percentage_used": {
                "daily_plans": (
                    billing.current_usage.get("plans_today", 0)
                    / billing.usage_limits["plans_per_day"]
                )
                * 100,
                "monthly_plans": (
                    billing.current_usage.get("plans_this_month", 0)
                    / billing.usage_limits["plans_per_month"]
                )
                * 100,
            },
        }

    def check_feature_access(self, user_id: str, feature_name: str) -> bool:
        """Check if user has access to a specific feature."""
        billing = self.get_user_billing(user_id)
        features = self.plan_features[billing.subscription_tier]

        feature_map = {
            "custom_agents": features.custom_agents,
            "priority_queue": features.priority_queue,
            "team_spaces": features.team_spaces,
            "advanced_analytics": features.advanced_analytics,
            "api_access": features.api_access,
        }

        return feature_map.get(feature_name, False)

    def check_usage_quota(self, user_id: str, operation_type: str = "plan"):
        """
        Check if user is within usage quota.

        Returns (allowed, quota_info)
        """
        billing = self.get_user_billing(user_id)

        # Get current date for daily/monthly calculations
        today = datetime.now().date()
        current_month = today.replace(day=1)

        # This would normally query our database for actual usage
        # For now, using the billing.current_usage placeholder values
        plans_today = billing.current_usage.get("plans_today", 0)
        plans_this_month = billing.current_usage.get("plans_this_month", 0)

        daily_allowed = plans_today < billing.usage_limits["plans_per_day"]
        monthly_allowed = plans_this_month < billing.usage_limits["plans_per_month"]

        allowed = daily_allowed and monthly_allowed

        quota_info = {
            "allowed": allowed,
            "tier": billing.subscription_tier.value,
            "daily_usage": {
                "used": plans_today,
                "limit": billing.usage_limits["plans_per_day"],
                "remaining": billing.usage_limits["plans_per_day"] - plans_today,
                "percentage": (plans_today / billing.usage_limits["plans_per_day"])
                * 100,
            },
            "monthly_usage": {
                "used": plans_this_month,
                "limit": billing.usage_limits["plans_per_month"],
                "remaining": billing.usage_limits["plans_per_month"] - plans_this_month,
                "percentage": (
                    plans_this_month / billing.usage_limits["plans_per_month"]
                )
                * 100,
            },
            "upgrade_required": not allowed,
        }

        return allowed, quota_info


# Global client instance
_clerk_client: Optional[ClerkCommerceClient] = None


def get_clerk_client() -> ClerkCommerceClient:
    """Get the global Clerk Commerce client."""
    global _clerk_client
    if _clerk_client is None:
        _clerk_client = ClerkCommerceClient()
    return _clerk_client


def get_user_billing_info(user_id: str) -> UserBilling:
    """Get billing information for a user."""
    client = get_clerk_client()
    return client.get_user_billing(user_id)


def check_feature_gate(user_id: str, feature_name: str) -> bool:
    """Check if user has access to a premium feature."""
    client = get_clerk_client()
    return client.check_feature_access(user_id, feature_name)


def check_quota_limit(user_id: str):
    """Check if user is within usage quota."""
    client = get_clerk_client()
    return client.check_usage_quota(user_id)
