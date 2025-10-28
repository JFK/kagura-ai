"""FastAPI dependencies.

Dependency injection for MemoryManager and other shared resources.
"""

import warnings
from typing import Annotated

from fastapi import Depends, Header

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
