"""Authentication module for Kagura AI.

Provides unified authentication for MCP, API, and CLI:
- Unified authentication manager (recommended)
- OAuth2 authentication (optional, requires google-auth-oauthlib)
- API key authentication
"""

from kagura.auth.config import AuthConfig
from kagura.auth.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    NotAuthenticatedError,
    TokenRefreshError,
)
from kagura.auth.unified_auth import (
    AuthMethod,
    AuthResult,
    UnifiedAuthManager,
    get_unified_auth_manager,
)

# OAuth2Manager is optional (requires google-auth-oauthlib)
try:
    from kagura.auth.oauth2 import OAuth2Manager

    _OAUTH2_AVAILABLE = True
except ImportError:
    OAuth2Manager = None  # type: ignore
    _OAUTH2_AVAILABLE = False

__all__ = [
    # Unified authentication (recommended)
    "UnifiedAuthManager",
    "get_unified_auth_manager",
    "AuthMethod",
    "AuthResult",
    # Legacy (optional)
    "OAuth2Manager",
    "AuthConfig",
    # Exceptions
    "AuthenticationError",
    "NotAuthenticatedError",
    "InvalidCredentialsError",
    "TokenRefreshError",
]
