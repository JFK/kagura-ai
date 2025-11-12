"""SQLAlchemy-based API Key Manager.

Issue #655 - API Key management with PostgreSQL/SQLite support.

Replaces the SQLite-only implementation in auth.py with a cloud-native
SQLAlchemy-based manager that supports both PostgreSQL and SQLite.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kagura.auth.models import APIKey, get_session, init_db
from kagura.config.env import get_env

logger = logging.getLogger(__name__)

# API Key prefix for easy identification
API_KEY_PREFIX = "kagura_"


class APIKeyManagerSQL:
    """Manages API keys using SQLAlchemy.

    Supports both PostgreSQL (production) and SQLite (development/local).
    """

    def __init__(self, database_url: Optional[str] = None) -> None:
        """Initialize API Key manager.

        Args:
            database_url: Database connection URL
                - PostgreSQL: postgresql://user:pass@host:5432/db
                - SQLite: sqlite:///path/to/api_keys.db
                - None: Uses DATABASE_URL from env (default)
        """
        if database_url:
            init_db(database_url)
        elif not self._is_db_initialized():
            # Auto-initialize with DATABASE_URL from environment
            db_url = get_env("DATABASE_URL")
            if not db_url:
                # Fallback to SQLite for local development
                from kagura.config.paths import get_data_dir
                db_path = get_data_dir() / "api_keys.db"
                db_url = f"sqlite:///{db_path}"
                logger.warning(
                    f"DATABASE_URL not set, using SQLite: {db_url}"
                )

            init_db(db_url)

    @staticmethod
    def _is_db_initialized() -> bool:
        """Check if database is initialized."""
        try:
            get_session()
            return True
        except RuntimeError:
            return False

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash API key using SHA256.

        Args:
            api_key: Plaintext API key

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _generate_key() -> str:
        """Generate a new API key.

        Returns:
            API key string (format: kagura_<random>)
        """
        # Generate 32 random bytes (256 bits)
        random_part = secrets.token_urlsafe(32)
        return f"{API_KEY_PREFIX}{random_part}"

    def create_key(
        self,
        name: str,
        user_id: str,
        expires_days: Optional[int] = None,
    ) -> str:
        """Create a new API key.

        Args:
            name: Friendly name for the key
            user_id: User ID that owns this key
            expires_days: Optional expiration in days (None = no expiration)

        Returns:
            Plaintext API key (only shown once)

        Raises:
            ValueError: If name already exists for user
        """
        session = get_session()

        try:
            # Check if name already exists for this user (non-revoked)
            existing = (
                session.query(APIKey)
                .filter(
                    and_(
                        APIKey.name == name,
                        APIKey.user_id == user_id,
                        APIKey.revoked_at.is_(None),
                    )
                )
                .first()
            )

            if existing:
                raise ValueError(f"API key with name '{name}' already exists")

            # Generate new key
            api_key = self._generate_key()
            key_hash = self._hash_key(api_key)
            key_prefix = api_key[:16]  # Store first 16 chars for display

            # Calculate expiration
            expires_at = None
            if expires_days:
                expires_at = datetime.now() + timedelta(days=expires_days)

            # Create database record
            new_key = APIKey(
                key_hash=key_hash,
                key_prefix=key_prefix,
                name=name,
                user_id=user_id,
                expires_at=expires_at,
            )

            session.add(new_key)
            session.commit()

            return api_key

        except IntegrityError as e:
            session.rollback()
            raise ValueError(f"Failed to create API key: {e}") from e
        finally:
            session.close()

    def verify_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return associated user_id.

        Args:
            api_key: Plaintext API key to verify

        Returns:
            user_id if valid, None otherwise

        Side effects:
            Updates last_used_at timestamp on successful verification
            Records usage statistics (if stats tracker is available)
        """
        key_hash = self._hash_key(api_key)
        session = get_session()

        try:
            # Query for key
            key_record = (
                session.query(APIKey).filter(APIKey.key_hash == key_hash).first()
            )

            if not key_record:
                return None

            # Check if revoked
            if key_record.revoked_at:
                return None

            # Check if expired
            if key_record.expires_at:
                if datetime.now() > key_record.expires_at:
                    return None

            # Update last_used_at
            key_record.last_used_at = datetime.now()
            session.commit()

            # Record usage statistics (best-effort)
            try:
                from kagura.core.memory.api_key_stats import get_stats_tracker

                stats_tracker = get_stats_tracker()
                stats_tracker.record_request(key_hash)
            except Exception as e:
                logger.debug(f"Failed to record API key stats: {e}")

            return key_record.user_id

        finally:
            session.close()

    def list_keys(self, user_id: Optional[str] = None) -> list[dict]:
        """List all API keys (optionally filtered by user).

        Args:
            user_id: Optional user_id filter

        Returns:
            List of API key metadata dicts (includes key_hash for stats lookup)
        """
        session = get_session()

        try:
            query = session.query(APIKey)

            if user_id:
                query = query.filter(APIKey.user_id == user_id)

            query = query.order_by(APIKey.created_at.desc())

            keys = query.all()

            # Convert to dict format
            return [
                {
                    "id": key.id,
                    "key_hash": key.key_hash,
                    "key_prefix": key.key_prefix,
                    "name": key.name,
                    "user_id": key.user_id,
                    "created_at": key.created_at.isoformat(),
                    "last_used_at": key.last_used_at.isoformat()
                    if key.last_used_at
                    else None,
                    "revoked_at": key.revoked_at.isoformat()
                    if key.revoked_at
                    else None,
                    "expires_at": key.expires_at.isoformat()
                    if key.expires_at
                    else None,
                }
                for key in keys
            ]

        finally:
            session.close()

    def revoke_key(self, name: str, user_id: str) -> bool:
        """Revoke an API key.

        Args:
            name: Name of the key to revoke
            user_id: User ID that owns the key

        Returns:
            True if revoked, False if not found
        """
        session = get_session()

        try:
            key_record = (
                session.query(APIKey)
                .filter(
                    and_(
                        APIKey.name == name,
                        APIKey.user_id == user_id,
                        APIKey.revoked_at.is_(None),
                    )
                )
                .first()
            )

            if not key_record:
                return False

            key_record.revoked_at = datetime.now()
            session.commit()

            return True

        finally:
            session.close()

    def delete_key(self, name: str, user_id: str) -> bool:
        """Permanently delete an API key.

        Args:
            name: Name of the key to delete
            user_id: User ID that owns the key

        Returns:
            True if deleted, False if not found
        """
        session = get_session()

        try:
            key_record = (
                session.query(APIKey)
                .filter(and_(APIKey.name == name, APIKey.user_id == user_id))
                .first()
            )

            if not key_record:
                return False

            session.delete(key_record)
            session.commit()

            return True

        finally:
            session.close()


# Global API Key manager instance
_api_key_manager: Optional[APIKeyManagerSQL] = None


def get_api_key_manager_sql() -> APIKeyManagerSQL:
    """Get or create global API Key manager instance.

    Returns:
        APIKeyManagerSQL instance
    """
    global _api_key_manager

    if _api_key_manager is None:
        _api_key_manager = APIKeyManagerSQL()

    return _api_key_manager
