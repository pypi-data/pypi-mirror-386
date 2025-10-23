"""Models for the Doorman web server."""

import secrets
import string
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class DeviceAuthStatus(str, Enum):
    """Device authentication status."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    EXPIRED = "expired"
    DENIED = "denied"


class DeviceAuth(BaseModel):
    """Device authentication session."""

    device_code: str = Field(description="Device code for polling")
    user_code: str = Field(description="User-friendly code for display")
    verification_uri: str = Field(description="URL for user to visit")
    verification_uri_complete: str = Field(description="Complete URL with user_code")
    expires_in: int = Field(default=1800, description="Expiration time in seconds")
    interval: int = Field(default=5, description="Polling interval in seconds")

    # Internal fields
    status: DeviceAuthStatus = DeviceAuthStatus.PENDING
    user_id: Optional[str] = None
    email: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    authorized_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        """Check if device auth session has expired."""
        return datetime.now() > (self.created_at + timedelta(seconds=self.expires_in))

    @property
    def expires_at(self) -> datetime:
        """Get expiration timestamp."""
        return self.created_at + timedelta(seconds=self.expires_in)

    @classmethod
    def create_new(cls, base_url: str) -> "DeviceAuth":
        """Create a new device auth session."""
        # Generate device code (long, secure)
        device_code = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(32)
        )

        # Generate user code (short, human-readable)
        user_code = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )

        verification_uri = f"{base_url}/device"
        verification_uri_complete = f"{verification_uri}?user_code={user_code}"

        return cls(
            device_code=device_code,
            user_code=user_code,
            verification_uri=verification_uri,
            verification_uri_complete=verification_uri_complete,
        )


class StripeSubscription(BaseModel):
    """Stripe subscription details."""

    stripe_subscription_id: str
    stripe_customer_id: str
    user_id: str
    email: str
    status: str  # active, canceled, incomplete, etc.
    current_period_start: datetime
    current_period_end: datetime
    plan_id: str
    plan_name: str
    seats: int = 1
    cancel_at_period_end: bool = False
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == "active" and datetime.now() < self.current_period_end

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.now() < self.trial_end

    @property
    def days_until_renewal(self) -> int:
        """Days until next billing cycle."""
        return max(0, (self.current_period_end - datetime.now()).days)


class JWTToken(BaseModel):
    """JWT token for authenticated sessions."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(default=86400, description="Token lifetime in seconds")
    refresh_token: Optional[str] = None
    scope: str = "doorman:full"

    # User info embedded in token
    user_id: str
    email: str
    tier: str
    subscription_id: Optional[str] = None
    features: list[str] = Field(default_factory=list)
    issued_at: datetime = Field(default_factory=datetime.now)

    @property
    def expires_at(self) -> datetime:
        """Get token expiration timestamp."""
        return self.issued_at + timedelta(seconds=self.expires_in)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() > self.expires_at


class WebhookEvent(BaseModel):
    """Stripe webhook event."""

    event_id: str
    event_type: str
    object_id: str
    object_type: str
    data: Dict[str, Any]
    created: datetime
    processed_at: Optional[datetime] = None
    processing_attempts: int = 0
    status: str = "pending"  # pending, processed, failed
    error_message: Optional[str] = None
