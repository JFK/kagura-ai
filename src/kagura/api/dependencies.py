"""FastAPI dependencies.

Dependency injection for MemoryManager and other shared resources.

Issue #650: Added OAuth2 session-based authentication dependencies:
- get_current_user(): Get authenticated user from session (raises 401 if not logged in)
- get_current_user_optional(): Get user or None
- require_admin(): Require ADMIN role (raises 403 if not admin)
"""

import warnings
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request

from kagura.auth.roles import Role, get_role_manager
from kagura.config.paths import get_data_dir
from kagura.core.memory import MemoryManager

# Global MemoryManager instances (user_id -> MemoryManager)
# Each user gets their own MemoryManager instance
_memory_managers: dict[str, MemoryManager] = {}


def get_user_id(x_user_id: str | None = Header(None)) -> str:
    """[DEPRECATED] Extract user_id from X-User-ID header.

    Args:
        x_user_id: User ID from X-User-ID header (deprecated, ignored)

    Returns:
        Always returns "default_user" (X-User-ID header is no longer trusted)

    Warning:
        X-User-ID header is deprecated due to security concerns (impersonation risk).
        Use API key authentication instead. This function always returns "default_user"
        regardless of the header value.

    See Also:
        - Issue #436: Security vulnerability fix
        - Use verify_api_key() from kagura.api.auth for proper authentication
    """
    if x_user_id:
        warnings.warn(
            "X-User-ID header is deprecated and ignored for security reasons. "
            "Use API key authentication (Authorization: Bearer <api_key>) instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    return "default_user"


def get_memory_manager(user_id: str = Depends(get_user_id)) -> MemoryManager:
    """Get or create MemoryManager instance for user.

    Args:
        user_id: User identifier (from get_user_id dependency)

    Returns:
        MemoryManager instance for this user

    Note:
        Each user_id gets a separate MemoryManager instance with
        isolated storage to ensure data isolation.
    """
    if user_id not in _memory_managers:
        # Initialize MemoryManager for this user
        # Each user gets their own persist directory in XDG data dir
        persist_dir = get_data_dir() / "api" / user_id
        persist_dir.mkdir(parents=True, exist_ok=True)

        _memory_managers[user_id] = MemoryManager(
            user_id=user_id,
            agent_name="api",
            persist_dir=persist_dir,
            max_messages=100,
            enable_rag=True,  # Enable semantic search
            enable_compression=False,  # Disable for API (stateless)
        )

    return _memory_managers[user_id]


# Type alias for dependency injection
MemoryManagerDep = Annotated[MemoryManager, Depends(get_memory_manager)]


# ============================================================================
# OAuth2 Session-based Authentication (Issue #650)
# ============================================================================


def get_current_user(request: Request) -> dict:
    """Get current authenticated user from session.

    Dependency that extracts user from request.state (injected by SessionMiddleware).

    Args:
        request: FastAPI request (with SessionMiddleware applied)

    Returns:
        User session data: {"sub": ..., "email": ..., "role": ...}

    Raises:
        HTTPException(401): If not authenticated

    Example:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            return {"user_email": user["email"]}
    """
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in via /auth/login",
        )

    return user


def get_current_user_optional(request: Request) -> Optional[dict]:
    """Get current user or None if not authenticated.

    Args:
        request: FastAPI request

    Returns:
        User session data or None

    Example:
        @router.get("/optional-auth")
        async def optional_auth(user: dict | None = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello anonymous"}
    """
    return getattr(request.state, "user", None)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require ADMIN role for endpoint access.

    Dependency that checks if authenticated user has ADMIN role.

    Args:
        user: Current authenticated user (from get_current_user)

    Returns:
        User data (if admin)

    Raises:
        HTTPException(403): If user is not ADMIN

    Example:
        @router.put("/api/v1/config/{key}")
        async def update_config(
            key: str,
            value: str,
            admin_user: dict = Depends(require_admin)
        ):
            # Only admins can reach here
            return {"updated": key}
    """
    user_role = user.get("role", "user")

    if user_role != Role.ADMIN.value:
        raise HTTPException(
            status_code=403,
            detail=f"Admin role required. Your role: {user_role}",
        )

    return user


# Type aliases
CurrentUser = Annotated[dict, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[dict], Depends(get_current_user_optional)]
AdminUser = Annotated[dict, Depends(require_admin)]
