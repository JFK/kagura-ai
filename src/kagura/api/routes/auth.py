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

from fastapi import APIRouter, HTTPException, Query, Request
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
async def google_login(
    return_to: Optional[str] = Query(None, description="URL to return to after login"),
):
    """Initiate Google OAuth2 login flow.

    Generates OAuth2 authorization URL with CSRF state token.

    Args:
        return_to: Optional URL to redirect to after successful login (for OAuth2 authorize flow)

    Returns:
        OAuth2 authorization URL and state token

    Example:
        GET /api/v1/auth/google/login?return_to=/api/v1/oauth/authorize?client_id=...
        Response: {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
            "state": "random_csrf_token"
        }

    Note:
        Frontend should redirect user to authorization_url.
        State token is stored in Redis for CSRF validation.
        If return_to is provided, user will be redirected there after login instead of default page.
    """
    if not _oauth2_manager:
        raise HTTPException(status_code=500, detail="OAuth2 manager not initialized")

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)

    # Store state + return_to in Redis (5 minute TTL)
    if _session_manager:
        import json

        state_data = {"status": "pending"}
        if return_to:
            state_data["return_to"] = return_to

        _session_manager._redis.setex(
            f"oauth2_state:{state}", 300, json.dumps(state_data)
        )

    # Get authorization URL (always use configured GOOGLE_REDIRECT_URI)
    # IMPORTANT: This is Kagura's callback URL, NOT the client's redirect_uri
    redirect = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect:
        raise HTTPException(status_code=500, detail="GOOGLE_REDIRECT_URI not configured")

    auth_url = _oauth2_manager.get_authorization_url_web(redirect, state)

    # If return_to is provided (OAuth2 authorize flow), redirect directly to Google
    # Otherwise, return JSON for API clients (backward compatibility)
    if return_to:
        logger.info(f"OAuth authorize flow: Redirecting to Google (return_to={return_to})")
        return RedirectResponse(url=auth_url, status_code=302)
    else:
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
    import json

    stored_state_raw = _session_manager._redis.get(f"oauth2_state:{state}")
    if not stored_state_raw:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token (CSRF protection)",
        )

    # Parse state data (may be JSON or plain string for backward compatibility)
    try:
        stored_state = json.loads(stored_state_raw)
        return_to = stored_state.get("return_to")
    except (json.JSONDecodeError, AttributeError):
        # Backward compatibility: old states were plain strings
        stored_state = {"status": "pending"}
        return_to = None

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

        # 6. Set HttpOnly cookie and redirect
        # Use return_to if provided (OAuth2 authorize flow), otherwise default to memory overview
        redirect_url = return_to if return_to else "/memory/overview"
        redirect = RedirectResponse(url=redirect_url, status_code=303)
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
        User information from session (wrapped in "user" object for frontend compatibility)

    Raises:
        HTTPException(401): Not authenticated

    Example:
        GET /api/v1/auth/me
        Cookie: session_id=...
        Response: {
            "user": {
                "id": "google_123",
                "email": "user@example.com",
                "name": "Example User",
                "role": "admin"
            }
        }

    Note:
        Frontend expects {user: {...}} format (Issue #664).
        Response wrapped in "user" object for compatibility.
    """
    # Get user from request.state (injected by SessionMiddleware)
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_data = request.state.user

    # Return wrapped in "user" object for frontend compatibility
    return {
        "user": {
            "id": user_data.get("sub"),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture"),
            "role": user_data.get("role", "user"),
        }
    }


# Include Google OAuth2 subrouter
router.include_router(google_router)
