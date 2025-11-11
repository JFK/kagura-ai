"""Role-based access control for Kagura Memory Cloud.

Issue #650 - OAuth2 Web Login & API Key Management

This module provides role definitions and management for user authorization.
Roles determine what actions users can perform in the system.

Example:
    >>> from kagura.auth.roles import Role, RoleManager
    >>> role_manager = RoleManager()
    >>> role_manager.assign_role("user@example.com", Role.ADMIN)
    >>> role_manager.has_role("user@example.com", Role.ADMIN)
    True
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    """User roles for access control.

    Attributes:
        ADMIN: Full system access (config, users, all APIs)
        USER: Standard user access (memory APIs, own API keys)
        READ_ONLY: Read-only access (view only, no modifications)
    """

    ADMIN = "admin"
    USER = "user"
    READ_ONLY = "read_only"

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return {
            Role.ADMIN: "Administrator",
            Role.USER: "User",
            Role.READ_ONLY: "Read-Only",
        }[self]

    @property
    def description(self) -> str:
        """Role description."""
        return {
            Role.ADMIN: "Full system access including configuration and user management",
            Role.USER: "Standard user access to memory APIs and API keys",
            Role.READ_ONLY: "Read-only access to own data",
        }[self]


class UserRole(BaseModel):
    """User role assignment.

    Attributes:
        email: User email address (from OAuth2)
        user_id: User ID (Google sub claim)
        role: Assigned role
        assigned_at: Role assignment timestamp
        assigned_by: Email of user who assigned this role (for audit)
    """

    email: str = Field(..., description="User email address")
    user_id: str = Field(..., description="User ID (OAuth2 sub)")
    role: Role = Field(default=Role.USER, description="Assigned role")
    assigned_at: str = Field(..., description="ISO 8601 timestamp")
    assigned_by: Optional[str] = Field(
        None, description="Email of user who assigned this role"
    )


class RoleManager:
    """Manage user roles and permissions.

    Uses PostgreSQL for persistent storage of user roles.
    First user to log in is automatically assigned ADMIN role.

    Example:
        >>> role_manager = RoleManager(db_url="postgresql://...")
        >>> # First login - auto ADMIN
        >>> role_manager.ensure_user("user1@example.com", "google-sub-123")
        >>> role_manager.get_role("user1@example.com")
        <Role.ADMIN: 'admin'>
        >>>
        >>> # Second login - default USER
        >>> role_manager.ensure_user("user2@example.com", "google-sub-456")
        >>> role_manager.get_role("user2@example.com")
        <Role.USER: 'user'>
        >>>
        >>> # Check permissions
        >>> role_manager.has_role("user1@example.com", Role.ADMIN)
        True
    """

    def __init__(self, db_url: str):
        """Initialize role manager.

        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        # TODO: Initialize database connection
        # For now, use in-memory dict (will be replaced with SQLAlchemy)
        self._roles: dict[str, Role] = {}

    def ensure_user(
        self, email: str, user_id: str, name: Optional[str] = None
    ) -> Role:
        """Ensure user exists, create if first user or new.

        First user is automatically assigned ADMIN role.
        Subsequent users are assigned USER role by default.

        Args:
            email: User email address
            user_id: User ID (OAuth2 sub claim)
            name: User display name (optional)

        Returns:
            Assigned role

        Example:
            >>> role = role_manager.ensure_user("user@example.com", "google-123")
        """
        # Check if user already exists
        if email in self._roles:
            return self._roles[email]

        # First user becomes ADMIN
        if len(self._roles) == 0:
            role = Role.ADMIN
        else:
            role = Role.USER

        self._roles[email] = role

        # TODO: Insert into PostgreSQL users table
        # INSERT INTO users (email, user_id, name, role, created_at)
        # VALUES (?, ?, ?, ?, NOW())
        # ON CONFLICT (email) DO NOTHING

        return role

    def get_role(self, email: str) -> Optional[Role]:
        """Get user's role.

        Args:
            email: User email address

        Returns:
            User's role or None if user not found

        Example:
            >>> role = role_manager.get_role("user@example.com")
        """
        # TODO: SELECT role FROM users WHERE email = ?
        return self._roles.get(email)

    def has_role(self, email: str, required_role: Role) -> bool:
        """Check if user has required role or higher.

        Role hierarchy: ADMIN > USER > READ_ONLY

        Args:
            email: User email address
            required_role: Required role level

        Returns:
            True if user has required role or higher

        Example:
            >>> role_manager.has_role("admin@example.com", Role.ADMIN)
            True
            >>> role_manager.has_role("user@example.com", Role.ADMIN)
            False
        """
        user_role = self.get_role(email)
        if not user_role:
            return False

        # Role hierarchy
        role_levels = {Role.ADMIN: 3, Role.USER: 2, Role.READ_ONLY: 1}

        return role_levels.get(user_role, 0) >= role_levels.get(required_role, 0)

    def assign_role(
        self, email: str, role: Role, assigned_by: Optional[str] = None
    ) -> None:
        """Assign role to user.

        Args:
            email: User email address
            role: Role to assign
            assigned_by: Email of user assigning the role (for audit)

        Raises:
            ValueError: If user not found

        Example:
            >>> role_manager.assign_role("user@example.com", Role.ADMIN)
        """
        if email not in self._roles:
            raise ValueError(f"User {email} not found")

        self._roles[email] = role

        # TODO: UPDATE users SET role = ?, updated_at = NOW()
        # WHERE email = ?
        # TODO: INSERT INTO audit_logs (user_email, action, resource, ...)

    def list_users(self) -> list[UserRole]:
        """List all users and their roles.

        Returns:
            List of UserRole objects

        Example:
            >>> users = role_manager.list_users()
        """
        # TODO: SELECT * FROM users ORDER BY created_at
        return []

    def is_admin(self, email: str) -> bool:
        """Check if user is admin.

        Args:
            email: User email address

        Returns:
            True if user has ADMIN role
        """
        return self.has_role(email, Role.ADMIN)


# Global singleton instance (will be initialized with DB URL from config)
_role_manager: Optional[RoleManager] = None


def get_role_manager() -> RoleManager:
    """Get global RoleManager instance.

    Returns:
        Global RoleManager singleton

    Raises:
        RuntimeError: If role manager not initialized

    Example:
        >>> from kagura.auth.roles import get_role_manager
        >>> role_manager = get_role_manager()
    """
    if _role_manager is None:
        raise RuntimeError(
            "RoleManager not initialized. "
            "Call initialize_role_manager(db_url) first."
        )
    return _role_manager


def initialize_role_manager(db_url: str) -> RoleManager:
    """Initialize global RoleManager.

    Args:
        db_url: PostgreSQL connection URL

    Returns:
        Initialized RoleManager instance

    Example:
        >>> from kagura.auth.roles import initialize_role_manager
        >>> role_manager = initialize_role_manager("postgresql://...")
    """
    global _role_manager
    _role_manager = RoleManager(db_url)
    return _role_manager
