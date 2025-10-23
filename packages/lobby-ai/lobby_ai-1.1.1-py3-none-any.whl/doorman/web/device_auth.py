"""Device authentication manager for Doorman CLI authentication."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import jwt

from .models import DeviceAuth, DeviceAuthStatus, JWTToken


class DeviceAuthManager:
    """Manages device authentication sessions for CLI login."""

    def __init__(self, jwt_secret: str, base_url: str = "https://api.doorman.dev"):
        self.jwt_secret = jwt_secret
        self.base_url = base_url
        self.data_dir = Path.home() / ".doorman" / "web_auth"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # In-memory storage for demo (would use Redis/database in production)
        self._sessions: Dict[str, DeviceAuth] = {}
        self._user_code_to_device_code: Dict[str, str] = {}

        # Load persisted sessions
        self._load_sessions()

    def _get_sessions_file(self) -> Path:
        return self.data_dir / "device_sessions.json"

    def _load_sessions(self):
        """Load device auth sessions from file."""
        sessions_file = self._get_sessions_file()
        if sessions_file.exists():
            try:
                with open(sessions_file) as f:
                    data = json.load(f)
                    for device_code, session_data in data.items():
                        session = DeviceAuth(**session_data)
                        self._sessions[device_code] = session
                        self._user_code_to_device_code[session.user_code] = device_code
            except Exception as e:
                print(f"Failed to load device sessions: {e}")

    def _save_sessions(self):
        """Save device auth sessions to file."""
        sessions_file = self._get_sessions_file()
        try:
            data = {}
            for device_code, session in self._sessions.items():
                data[device_code] = session.model_dump()

            with open(sessions_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save device sessions: {e}")

    def start_device_flow(self) -> DeviceAuth:
        """Start a new device authentication flow."""
        session = DeviceAuth.create_new(self.base_url)

        self._sessions[session.device_code] = session
        self._user_code_to_device_code[session.user_code] = session.device_code

        self._save_sessions()

        return session

    def get_session_by_device_code(self, device_code: str) -> Optional[DeviceAuth]:
        """Get device auth session by device code."""
        session = self._sessions.get(device_code)
        if session and session.is_expired:
            session.status = DeviceAuthStatus.EXPIRED
            self._save_sessions()
        return session

    def get_session_by_user_code(self, user_code: str) -> Optional[DeviceAuth]:
        """Get device auth session by user code."""
        device_code = self._user_code_to_device_code.get(user_code)
        if device_code:
            return self.get_session_by_device_code(device_code)
        return None

    def authorize_device(
        self,
        user_code: str,
        user_id: str,
        email: str,
        stripe_customer_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Authorize a device with user credentials."""
        session = self.get_session_by_user_code(user_code)

        if not session or session.status != DeviceAuthStatus.PENDING:
            return False

        if session.is_expired:
            session.status = DeviceAuthStatus.EXPIRED
            self._save_sessions()
            return False

        # Authorize the session
        session.status = DeviceAuthStatus.AUTHORIZED
        session.user_id = user_id
        session.email = email
        session.stripe_customer_id = stripe_customer_id
        session.authorized_at = datetime.now()
        session.ip_address = ip_address
        session.user_agent = user_agent

        self._save_sessions()

        return True

    def deny_device(self, user_code: str) -> bool:
        """Deny device authorization."""
        session = self.get_session_by_user_code(user_code)

        if not session or session.status != DeviceAuthStatus.PENDING:
            return False

        session.status = DeviceAuthStatus.DENIED
        self._save_sessions()

        return True

    def poll_device_authorization(self, device_code: str) -> Optional[JWTToken]:
        """Poll for device authorization status."""
        session = self.get_session_by_device_code(device_code)

        if not session:
            return None

        if session.status == DeviceAuthStatus.AUTHORIZED and session.user_id:
            # Generate JWT token
            return self._create_jwt_token(
                user_id=session.user_id,
                email=session.email or f"user_{session.user_id}@doorman.dev",
                tier="premium",  # Would come from Stripe subscription
                features=["unlimited_plans", "custom_agents", "priority_queue"],
            )

        return None

    def _create_jwt_token(
        self,
        user_id: str,
        email: str,
        tier: str,
        features: list[str],
        subscription_id: Optional[str] = None,
    ) -> JWTToken:
        """Create a JWT token for authenticated user."""

        # Create JWT payload
        now = datetime.now()
        expires_in = 86400  # 24 hours

        payload = {
            "sub": user_id,  # subject (user ID)
            "email": email,
            "tier": tier,
            "features": features,
            "subscription_id": subscription_id,
            "iat": int(now.timestamp()),  # issued at
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),  # expires
            "iss": "doorman-auth",  # issuer
            "aud": "doorman-cli",  # audience
        }

        # Generate access token
        access_token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        # Generate refresh token (optional)
        refresh_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp()),  # 30 days for refresh
        }
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm="HS256")

        return JWTToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user_id=user_id,
            email=email,
            tier=tier,
            subscription_id=subscription_id,
            features=features,
        )

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=["HS256"], audience="doorman-cli"
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def refresh_token(self, refresh_token: str) -> Optional[JWTToken]:
        """Refresh an access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=["HS256"])

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Would fetch current user info from database
            # For now, return new token with same permissions
            return self._create_jwt_token(
                user_id=user_id,
                email=f"user_{user_id}@doorman.dev",
                tier="premium",
                features=["unlimited_plans", "custom_agents", "priority_queue"],
            )

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def cleanup_expired_sessions(self):
        """Remove expired device auth sessions."""
        expired_devices = []

        for device_code, session in self._sessions.items():
            if session.is_expired or session.status in [
                DeviceAuthStatus.AUTHORIZED,
                DeviceAuthStatus.DENIED,
            ]:
                # Clean up sessions that are expired or completed
                if session.authorized_at and (
                    datetime.now() - session.authorized_at
                ) > timedelta(hours=1):
                    expired_devices.append(device_code)

        for device_code in expired_devices:
            session = self._sessions.pop(device_code, None)
            if session:
                self._user_code_to_device_code.pop(session.user_code, None)

        if expired_devices:
            self._save_sessions()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about device auth sessions."""
        total_sessions = len(self._sessions)
        pending_sessions = sum(
            1 for s in self._sessions.values() if s.status == DeviceAuthStatus.PENDING
        )
        authorized_sessions = sum(
            1
            for s in self._sessions.values()
            if s.status == DeviceAuthStatus.AUTHORIZED
        )
        expired_sessions = sum(1 for s in self._sessions.values() if s.is_expired)

        return {
            "total_sessions": total_sessions,
            "pending_sessions": pending_sessions,
            "authorized_sessions": authorized_sessions,
            "expired_sessions": expired_sessions,
        }
