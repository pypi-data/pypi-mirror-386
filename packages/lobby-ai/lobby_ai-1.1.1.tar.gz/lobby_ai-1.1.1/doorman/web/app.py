"""FastAPI web application for Doorman billing and authentication."""

import logging
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Request/Response models
class DeviceAuthRequest(BaseModel):
    client_id: str = "doorman-cli"


class DeviceAuthResponse(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


class DeviceTokenRequest(BaseModel):
    grant_type: str = "urn:ietf:params:oauth:grant-type:device_code"
    device_code: str


class AuthorizeDeviceRequest(BaseModel):
    user_code: str
    email: str
    consent: bool = True


class SubscriptionInfo(BaseModel):
    tier: str
    status: str
    seats: int
    renews_at: Optional[str] = None
    features: list[str]


class CheckoutRequest(BaseModel):
    price_id: str
    email: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    from .device_auth import DeviceAuthManager

    app = FastAPI(
        title="Doorman API",
        description="Authentication and billing API for Doorman CLI",
        version="1.0.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://doorman.dev"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize device auth manager
    jwt_secret = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    device_auth_manager = DeviceAuthManager(jwt_secret, base_url)

    # Initialize Stripe service
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_demo")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    from .stripe_service import StripeService

    stripe_service = StripeService(stripe_secret_key, webhook_secret)

    security = HTTPBearer()

    # Authentication dependency
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> Dict[str, Any]:
        payload = device_auth_manager.verify_jwt_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return payload

    @app.post("/device/start", response_model=DeviceAuthResponse)
    async def start_device_flow(request: DeviceAuthRequest):
        """Start device authentication flow."""
        session = device_auth_manager.start_device_flow()

        return DeviceAuthResponse(
            device_code=session.device_code,
            user_code=session.user_code,
            verification_uri=session.verification_uri,
            verification_uri_complete=session.verification_uri_complete,
            expires_in=session.expires_in,
            interval=session.interval,
        )

    @app.post("/device/poll")
    async def poll_device_authorization(request: DeviceTokenRequest):
        """Poll for device authorization completion."""

        token = device_auth_manager.poll_device_authorization(request.device_code)

        if not token:
            # Check session status for better error messages
            session = device_auth_manager.get_session_by_device_code(
                request.device_code
            )
            if not session:
                raise HTTPException(status_code=404, detail="Invalid device code")
            elif session.is_expired:
                raise HTTPException(status_code=400, detail="Device code expired")
            elif session.status.value == "denied":
                raise HTTPException(status_code=403, detail="Authorization denied")
            else:
                raise HTTPException(status_code=428, detail="Authorization pending")

        return token

    @app.get("/device", response_class=HTMLResponse)
    async def device_authorization_page(user_code: Optional[str] = None):
        """Device authorization web page."""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Doorman - Device Authorization</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px; margin: 50px auto; padding: 20px; 
            background: #0a0a0a; color: #00ff41;
        }}
        .container {{ background: #111; padding: 30px; border-radius: 8px; border: 2px solid #00ff41; }}
        .logo {{ text-align: center; font-size: 2em; margin-bottom: 30px; }}
        .code {{ font-size: 2em; text-align: center; letter-spacing: 0.2em; 
                 background: #222; padding: 15px; border-radius: 4px; margin: 20px 0; }}
        button {{ background: #00ff41; color: #000; border: none; padding: 12px 24px; 
                 border-radius: 4px; font-size: 16px; cursor: pointer; }}
        button:hover {{ background: #00cc33; }}
        .form {{ margin-top: 30px; }}
        input {{ width: 100%; padding: 10px; margin: 10px 0; background: #222; 
                border: 1px solid #444; color: #00ff41; border-radius: 4px; }}
        .error {{ color: #ff4444; margin-top: 10px; }}
        .success {{ color: #44ff44; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🚪 DOORMAN</div>
        <h2>Authorize Device Access</h2>
        
        {f'<div class="code">{user_code}</div>' if user_code else ""}
        
        <p>To continue, please confirm this is your device code and enter your email address:</p>
        
        <form class="form" id="authForm">
            <input type="text" id="userCode" placeholder="Enter device code" 
                   value="{user_code or ""}" required>
            <input type="email" id="email" placeholder="Enter your email address" required>
            <button type="submit">Authorize Device</button>
        </form>
        
        <div id="message"></div>
    </div>
    
    <script>
        document.getElementById('authForm').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const userCode = document.getElementById('userCode').value;
            const email = document.getElementById('email').value;
            const messageEl = document.getElementById('message');
            
            try {{
                const response = await fetch('/device/authorize', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        user_code: userCode,
                        email: email,
                        consent: true
                    }})
                }});
                
                if (response.ok) {{
                    messageEl.innerHTML = '<div class="success">✅ Device authorized successfully! You can now close this window and return to your CLI.</div>';
                }} else {{
                    const error = await response.json();
                    messageEl.innerHTML = `<div class="error">❌ ${{error.detail || 'Authorization failed'}}</div>`;
                }}
            }} catch (error) {{
                messageEl.innerHTML = '<div class="error">❌ Network error. Please try again.</div>';
            }}
        }});
    </script>
</body>
</html>"""

        return HTMLResponse(content=html_content)

    @app.post("/device/authorize")
    async def authorize_device(request: AuthorizeDeviceRequest, http_request: Request):
        """Authorize a device with user consent."""
        if not request.consent:
            device_auth_manager.deny_device(request.user_code)
            raise HTTPException(status_code=403, detail="Authorization denied")

        # Simple user ID generation from email
        user_id = request.email.split("@")[0]

        success = device_auth_manager.authorize_device(
            user_code=request.user_code,
            user_id=user_id,
            email=request.email,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Invalid user code or authorization failed"
            )

        return {"message": "Device authorized successfully"}

    @app.get("/me/subscription", response_model=SubscriptionInfo)
    async def get_user_subscription(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Get current user's subscription information."""

        # For demo, return subscription info from JWT token
        tier = current_user.get("tier", "free")
        features = current_user.get("features", [])

        return SubscriptionInfo(
            tier=tier,
            status="active",
            seats=1,
            features=features,
            renews_at=None,  # Would come from Stripe
        )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        stats = device_auth_manager.get_session_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "auth_sessions": stats,
        }

    @app.post("/webhooks/stripe")
    async def stripe_webhook(request: Request):
        """Handle Stripe webhooks."""
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")

        try:
            event = stripe_service.verify_webhook(payload, signature)
            await stripe_service.process_webhook_event(event)
            return {"received": True}
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook")

    @app.post("/checkout")
    async def create_checkout_session(
        request: CheckoutRequest,
        current_user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Create Stripe checkout session."""

        success_url = request.success_url or f"{base_url}/checkout/success"
        cancel_url = request.cancel_url or f"{base_url}/checkout/cancel"

        session = stripe_service.create_checkout_session(
            price_id=request.price_id,
            customer_email=request.email,
            user_id=current_user["sub"],
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return {"checkout_url": session["url"], "session_id": session["id"]}

    @app.post("/billing/portal")
    async def create_billing_portal_session(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ):
        """Create Stripe customer portal session."""

        # Would get customer_id from database in production
        customer_id = "cus_test123"  # Mock for now
        return_url = f"{base_url}/me/subscription"

        session = stripe_service.create_customer_portal_session(
            customer_id=customer_id, return_url=return_url
        )

        return {"portal_url": session["url"]}

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
