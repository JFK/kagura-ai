"""SQLAlchemy models for authentication and audit logging.

Issue #653 - PostgreSQL backend for roles and audit logs
Issue #655 - API Key management with PostgreSQL/SQLite support

Provides ORM models for:
- users table (OAuth2 users with role-based access control)
- audit_logs table (security audit trail for config changes, role assignments, etc.)
- api_keys table (API key management with expiration and usage tracking)

Example:
    >>> from kagura.auth.models import User, AuditLog, APIKey, get_session
    >>> session = get_session("postgresql://...")
    >>> user = session.query(User).filter_by(email="admin@example.com").first()
    >>> print(user.role)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

Base = declarative_base()


class User(Base):
    """User model for OAuth2 authentication and RBAC.

    Corresponds to migrations/001_users.sql users table.

    Attributes:
        id: Primary key
        email: User email (unique, from OAuth2)
        user_id: OAuth2 sub claim (unique, globally unique identifier)
        name: Display name
        picture: Profile picture URL
        role: Access control role (admin, user, read_only)
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
        last_login_at: Last login timestamp
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # OAuth2 Identity
    email = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=True)
    picture = Column(String(512), nullable=True)

    # Role & Permissions
    role = Column(String(50), nullable=False, default="user", index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)

    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'user', 'read_only')", name="valid_role"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(email='{self.email}', role='{self.role}')>"


class AuditLog(Base):
    """Audit log model for security-sensitive operations.

    Corresponds to migrations/001_users.sql audit_logs table.

    Stores audit trail for:
    - Configuration changes (OPENAI_API_KEY update, etc.)
    - Role assignments (user promoted to admin, etc.)
    - API key creation/revocation
    - System restarts

    Security:
        - old_value_hash/new_value_hash store SHA256 hashes, NOT plaintext
        - Enables audit queries without exposing secrets

    Attributes:
        id: Primary key
        user_email: Email of user who performed the action
        user_id: OAuth2 sub of user
        action: Action type (config_update, role_assign, api_key_create, etc.)
        resource: Resource identifier (e.g., "OPENAI_API_KEY", "user:admin@example.com")
        old_value_hash: SHA256 hash of old value (NOT plaintext)
        new_value_hash: SHA256 hash of new value (NOT plaintext)
        user_metadata: Additional context (JSON)
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Timestamp
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Who
    user_email = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)

    # What
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(255), nullable=False, index=True)

    # Details (SHA256 hashes, NOT plaintext!)
    old_value_hash = Column(String(64), nullable=True)
    new_value_hash = Column(String(64), nullable=True)
    user_metadata = Column(JSON, nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String, nullable=True)

    # Timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(action='{self.action}', resource='{self.resource}', user='{self.user_email}')>"


class APIKey(Base):
    """API Key model for programmatic access.

    Issue #655 - API Key management page with CRUD operations.

    Stores API keys securely with:
    - SHA256 hash (never stores plaintext after creation)
    - Optional expiration
    - Revocation support
    - Usage tracking

    Attributes:
        id: Primary key
        key_hash: SHA256 hash of API key (for verification)
        key_prefix: First 16 characters (for display only)
        name: Friendly name
        user_id: Owner user ID (OAuth2 sub)
        created_at: Creation timestamp
        last_used_at: Last usage timestamp
        revoked_at: Revocation timestamp (NULL = active)
        expires_at: Expiration timestamp (NULL = no expiration)
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # API Key Data
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False)
    name = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_user_name", "user_id", "name"),
        Index("idx_revoked", "revoked_at"),
        Index("idx_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<APIKey(name='{self.name}', prefix='{self.key_prefix}', user='{self.user_id}')>"


# ============================================================================
# Database Session Management
# ============================================================================

_engine = None
_SessionLocal = None


def init_db(database_url: str) -> None:
    """Initialize database engine and session factory.

    Args:
        database_url: PostgreSQL connection URL

    Example:
        >>> init_db("postgresql://user:pass@localhost/kagura")
    """
    global _engine, _SessionLocal

    _engine = create_engine(database_url, echo=False)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_session() -> Session:
    """Get database session.

    Returns:
        SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized

    Example:
        >>> session = get_session()
        >>> users = session.query(User).all()
        >>> session.close()
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    return _SessionLocal()


class ExternalAPIKey(Base):
    """External API Key model for third-party services.

    Issues #690, #692 - External API Keys management with encryption.

    Stores API keys for external services (OpenAI, Anthropic, Google, etc.) with:
    - Fernet symmetric encryption (can decrypt for usage)
    - Provider categorization
    - Admin-only access
    - Audit trail

    Attributes:
        id: Primary key
        key_name: Unique identifier (e.g., "OPENAI_API_KEY")
        provider: Service provider (e.g., "openai", "anthropic")
        encrypted_value: Fernet-encrypted API key value
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        updated_by: Email of admin who last modified
    """

    __tablename__ = "external_api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # API Key Identity
    key_name = Column(String(100), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, index=True)

    # Encrypted Value (Fernet)
    encrypted_value = Column(String, nullable=False)  # TEXT in PostgreSQL, TEXT in SQLite

    # Audit Trail
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), nullable=True)  # Email of admin

    # Indexes
    __table_args__ = (Index("idx_external_api_keys_updated", "updated_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ExternalAPIKey(key_name='{self.key_name}', provider='{self.provider}')>"


def create_tables(database_url: str) -> None:
    """Create all tables in database.

    Args:
        database_url: PostgreSQL connection URL

    Note:
        This is a convenience method for development/testing.
        In production, use migrations/001_users.sql via migration runner.

    Example:
        >>> create_tables("postgresql://user:pass@localhost/kagura")
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
