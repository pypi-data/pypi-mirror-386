"""Stripe integration service for Doorman subscriptions."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .models import StripeSubscription

logger = logging.getLogger(__name__)


class StripeService:
    """Stripe integration service for subscription management."""

    def __init__(self, stripe_secret_key: str, webhook_secret: Optional[str] = None):
        self.stripe_secret_key = stripe_secret_key
        self.webhook_secret = webhook_secret

        # Would import stripe here in production
        # import stripe
        # stripe.api_key = stripe_secret_key

    def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify and parse Stripe webhook."""
        # In production, would use stripe.Webhook.construct_event()
        # For now, return mock event

        return {
            "id": "evt_test123",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test123",
                    "customer": "cus_test123",
                    "status": "active",
                    "current_period_start": 1640995200,
                    "current_period_end": 1643673600,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_premium_monthly",
                                    "nickname": "Premium Monthly",
                                }
                            }
                        ]
                    },
                    "metadata": {
                        "user_id": "user_test123",
                        "email": "test@example.com",
                    },
                }
            },
        }

    async def process_webhook_event(self, event: Dict[str, Any]):
        """Process a Stripe webhook event."""
        event_type = event.get("type")

        if event_type in [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ]:
            await self._handle_subscription_event(event)

        elif event_type == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(event)

        elif event_type == "invoice.payment_failed":
            await self._handle_payment_failed(event)

        logger.info(f"Processed Stripe webhook: {event_type}")

    async def _handle_subscription_event(self, event: Dict[str, Any]):
        """Handle subscription creation, update, or deletion."""
        subscription_data = event["data"]["object"]

        # Extract subscription details
        subscription = StripeSubscription(
            stripe_subscription_id=subscription_data["id"],
            stripe_customer_id=subscription_data["customer"],
            user_id=subscription_data["metadata"].get("user_id", ""),
            email=subscription_data["metadata"].get("email", ""),
            status=subscription_data["status"],
            current_period_start=datetime.fromtimestamp(
                subscription_data["current_period_start"]
            ),
            current_period_end=datetime.fromtimestamp(
                subscription_data["current_period_end"]
            ),
            plan_id=subscription_data["items"]["data"][0]["price"]["id"],
            plan_name=subscription_data["items"]["data"][0]["price"].get(
                "nickname", "Premium"
            ),
            seats=subscription_data.get("quantity", 1),
            cancel_at_period_end=subscription_data.get("cancel_at_period_end", False),
            metadata=subscription_data.get("metadata", {}),
            updated_at=datetime.now(),
        )

        # Store subscription in database (would use actual database in production)
        logger.info(
            f"Updated subscription: {subscription.stripe_subscription_id} -> {subscription.status}"
        )

    async def _handle_payment_succeeded(self, event: Dict[str, Any]):
        """Handle successful payment."""
        invoice_data = event["data"]["object"]
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")

        logger.info(
            f"Payment succeeded for customer {customer_id}, subscription {subscription_id}"
        )

    async def _handle_payment_failed(self, event: Dict[str, Any]):
        """Handle failed payment."""
        invoice_data = event["data"]["object"]
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")

        logger.warning(
            f"Payment failed for customer {customer_id}, subscription {subscription_id}"
        )

    def create_checkout_session(
        self,
        price_id: str,
        customer_email: str,
        user_id: str,
        success_url: str,
        cancel_url: str,
    ) -> Dict[str, Any]:
        """Create a Stripe Checkout session."""
        # In production, would use stripe.checkout.Session.create()

        return {
            "id": "cs_test123",
            "url": f"https://checkout.stripe.com/c/pay/cs_test123#{user_id}",
            "customer": "cus_test123",
            "payment_status": "unpaid",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }

    def create_customer_portal_session(
        self, customer_id: str, return_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session."""
        # In production, would use stripe.billing_portal.Session.create()

        return {
            "id": "bps_test123",
            "url": "https://billing.stripe.com/session/bps_test123",
            "customer": customer_id,
            "return_url": return_url,
        }

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription details from Stripe."""
        # In production, would use stripe.Subscription.retrieve()

        return {
            "id": subscription_id,
            "customer": "cus_test123",
            "status": "active",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "plan": {"id": "price_premium_monthly", "nickname": "Premium Monthly"},
            "metadata": {"user_id": "test_user", "email": "test@example.com"},
        }

    def cancel_subscription(
        self, subscription_id: str, at_period_end: bool = True
    ) -> Dict[str, Any]:
        """Cancel a Stripe subscription."""
        # In production, would use stripe.Subscription.modify()

        return {
            "id": subscription_id,
            "status": "active" if at_period_end else "canceled",
            "cancel_at_period_end": at_period_end,
            "canceled_at": None if at_period_end else int(datetime.now().timestamp()),
        }
