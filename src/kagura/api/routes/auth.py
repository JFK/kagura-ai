"""OAuth2 Web Login endpoints for Kagura Memory Cloud.

Issue #650 - Google OAuth2 Web Login & API Key Management

Provides web-based OAuth2 authentication flow:
1. GET /auth/login - Redirect to Google OAuth2 consent screen
2. GET /auth/callback - Handle OAuth2 callback, create session
3. POST /auth/logout - Delete session and logout

Security features:
- CSRF protection via state parameter
- HttpOnly, Secure, SameSite cookies
- Session stored in Redis
- First user auto-assigned ADMIN role
"""

import logging
import os
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from kagura.auth.oauth2 import OAuth2Manager
from kagura.auth.roles import get_role_manager
from kagura.auth.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth2 subrouter (provider-specific endpoints)
google_router = APIRouter(prefix="/google", tags=["authentication", "google-oauth2"])

# Global instances (initialized on server startup)
_oauth2_manager: Optional[OAuth2Manager] = None
_session_manager: Optional[SessionManager] = None


def initialize_auth_routes(oauth2_manager: OAuth2Manager, session_manager: SessionManager):
    """Initialize auth routes with managers.

    Args:
        oauth2_manager: OAuth2 manager instance
        session_manager: Session manager instance
    """
    global _oauth2_manager, _session_manager
    _oauth2_manager = oauth2_manager
    _session_manager = session_manager


# Models
class LoginResponse(BaseModel):
    """OAuth2 login response."""

    authorization_url: str
    state: str


class CallbackResponse(BaseModel):
    """OAuth2 callback response."""

    success: bool
    user_id: str
    email: str
    role: str
    message: str


# ============================================================================
# OAuth2 Endpoints
# ============================================================================


@google_router.get("/login", response_model=LoginResponse)
async def google_login(redirect_uri: Optional[str] = None):
    """Initiate Google OAuth2 login flow.

    Generates OAuth2 authorization URL with CSRF state token.

    Args:
        redirect_uri: Optional custom redirect URI (defaults to configured URI)

    Returns:
        OAuth2 authorization URL and state token

    Example:
        GET /api/v1/auth/google/login
        Response: {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
            "state": "random_csrf_token"
        }

    Note:
        Frontend should redirect user to authorization_url.
        State token is stored in Redis for CSRF validation.
    """
    if not _oauth2_manager:
        raise HTTPException(status_code=500, detail="OAuth2 manager not initialized")

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Store state in Redis (5 minute TTL)
    if _session_manager:
        _session_manager._redis.setex(f"oauth2_state:{state}", 300, "pending")

    # Get authorization URL
    redirect = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

    auth_url = _oauth2_manager.get_authorization_url_web(redirect, state)

    return LoginResponse(authorization_url=auth_url, state=state)


@google_router.get("/callback")
async def google_callback(
    code: str = Query(..., description="OAuth2 authorization code"),
    state: str = Query(..., description="CSRF state token"),
):
    """Handle Google OAuth2 callback.

    Exchanges authorization code for access token, retrieves user info,
    creates session, and sets HttpOnly cookie.

    Args:
        code: OAuth2 authorization code from Google
        state: CSRF state token (must match stored state)
        response: FastAPI response object (for cookie setting)

    Returns:
        Redirect to dashboard with session cookie set

    Raises:
        HTTPException(400): Invalid state (CSRF attack)
        HTTPException(401): OAuth2 exchange failed
        HTTPException(500): Session creation failed

    Example:
        GET /api/v1/auth/google/callback?code=xxx&state=yyy
        → Sets cookie: session_id=...
        → Redirects to /dashboard

    Security:
        - State validation (CSRF protection)
        - HttpOnly cookie (XSS protection)
        - Secure cookie (HTTPS only)
        - SameSite=Lax (CSRF protection)
    """
    if not _oauth2_manager or not _session_manager:
        raise HTTPException(
            status_code=500, detail="Auth managers not initialized"
        )

    # 1. Validate CSRF state
    stored_state = _session_manager._redis.get(f"oauth2_state:{state}")
    if not stored_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token (CSRF protection)",
        )

    # Delete state (one-time use)
    _session_manager._redis.delete(f"oauth2_state:{state}")

    try:
        # 2. Exchange code for token
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        if not redirect_uri:
            raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

        credentials = _oauth2_manager.exchange_code_web(code, redirect_uri)

        # 3. Get user info from Google
        user_info = _oauth2_manager.get_user_info_web(credentials)

        # 4. Ensure user exists in database & assign role
        role_manager = get_role_manager()
        role = role_manager.ensure_user(
            email=user_info["email"],
            user_id=user_info["sub"],
            name=user_info.get("name"),
        )

        # 5. Create session
        session_data = {
            "sub": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "role": role.value,
        }
        session_id = _session_manager.create_session(session_data)

        # 6. Set HttpOnly cookie
        redirect = RedirectResponse(url="/dashboard", status_code=303)
        redirect.set_cookie(
            key="session_id",
            value=session_id,
            path="/",  # Available for all paths
            httponly=True,
            secure=True,  # HTTPS only
            samesite="lax",  # CSRF protection
            max_age=_session_manager.session_ttl,
        )

        logger.info(f"OAuth2 login successful: {user_info['email']} (role={role})")

        return redirect

    except Exception as e:
        logger.error(f"OAuth2 callback failed: {e}")
        raise HTTPException(
            status_code=401, detail=f"OAuth2 authentication failed: {str(e)}"
        )


@router.post("/logout")
async def logout(session_id: Optional[str] = None):
    """Logout user and delete session.

    Args:
        session_id: Session ID from cookie (auto-extracted by middleware)

    Returns:
        Success message

    Example:
        POST /auth/logout
        Cookie: session_id=...
        Response: {"success": true, "message": "Logged out"}
    """
    if not _session_manager:
        raise HTTPException(status_code=500, detail="Session manager not initialized")

    if session_id:
        _session_manager.delete_session(session_id)
        logger.info(f"User logged out: session={session_id[:8]}...")

    # TODO: Clear cookie in response
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current authenticated user info.

    Args:
        request: FastAPI request (session injected by SessionMiddleware)

    Returns:
        User information from session

    Raises:
        HTTPException(401): Not authenticated

    Example:
        GET /api/v1/auth/me
        Cookie: session_id=...
        Response: {
            "user_id": "google_123",
            "email": "user@example.com",
            "name": "Example User",
            "role": "admin"
        }
    """
    # Get user from request.state (injected by SessionMiddleware)
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = request.state.user

    return {
        "user_id": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "picture": user.get("picture"),
        "role": user.get("role", "user"),
    }


# Include Google OAuth2 subrouter
router.include_router(google_router)
