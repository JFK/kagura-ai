"""API Key authentication for Kagura Memory API.

Provides API Key generation, validation, and management for remote access.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from kagura.config.paths import get_data_dir

# API Key prefix for easy identification
API_KEY_PREFIX = "kagura_"

# Security scheme for FastAPI
security = HTTPBearer(auto_error=False)


class APIKeyManager:
    """Manages API keys for authentication.

    Stores API keys securely in SQLite database with hashing.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize API Key manager.

        Args:
            db_path: Path to SQLite database
                (default: XDG data dir or ~/.local/share/kagura/api_keys.db)
        """
        self.db_path = db_path or get_data_dir() / "api_keys.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT NOT NULL UNIQUE,
                    key_prefix TEXT NOT NULL,
                    name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    revoked_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON api_keys(user_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_name ON api_keys(name, user_id)"
            )

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
        # Check if name already exists for this user
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id FROM api_keys
                WHERE name = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (name, user_id),
            )
            if cursor.fetchone():
                raise ValueError(f"API key with name '{name}' already exists")

        # Generate new key
        api_key = self._generate_key()
        key_hash = self._hash_key(api_key)
        key_prefix = api_key[:16]  # Store first 16 chars for display

        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_keys
                (key_hash, key_prefix, name, user_id, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key_hash, key_prefix, name, user_id, expires_at),
            )

        return api_key

    def verify_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return associated user_id.

        Args:
            api_key: Plaintext API key to verify

        Returns:
            user_id if valid, None otherwise

        Side effects:
            Updates last_used_at timestamp on successful verification
        """
        key_hash = self._hash_key(api_key)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT user_id, expires_at, revoked_at FROM api_keys
                WHERE key_hash = ?
                """,
                (key_hash,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            user_id, expires_at, revoked_at = row

            # Check if revoked
            if revoked_at:
                return None

            # Check if expired
            if expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
                if datetime.now() > expires_dt:
                    return None

            # Update last_used_at
            conn.execute(
                """
                UPDATE api_keys
                SET last_used_at = ?
                WHERE key_hash = ?
                """,
                (datetime.now(), key_hash),
            )

            return user_id

    def list_keys(self, user_id: Optional[str] = None) -> list[dict]:
        """List all API keys (optionally filtered by user).

        Args:
            user_id: Optional user_id filter

        Returns:
            List of API key metadata dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if user_id:
                cursor = conn.execute(
                    """
                    SELECT id, key_prefix, name, user_id, created_at,
                           last_used_at, revoked_at, expires_at
                    FROM api_keys
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, key_prefix, name, user_id, created_at,
                           last_used_at, revoked_at, expires_at
                    FROM api_keys
                    ORDER BY created_at DESC
                    """
                )

            return [dict(row) for row in cursor.fetchall()]

    def revoke_key(self, name: str, user_id: str) -> bool:
        """Revoke an API key.

        Args:
            name: Name of the key to revoke
            user_id: User ID that owns the key

        Returns:
            True if revoked, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE api_keys
                SET revoked_at = ?
                WHERE name = ? AND user_id = ? AND revoked_at IS NULL
                """,
                (datetime.now(), name, user_id),
            )
            return cursor.rowcount > 0

    def delete_key(self, name: str, user_id: str) -> bool:
        """Permanently delete an API key.

        Args:
            name: Name of the key to delete
            user_id: User ID that owns the key

        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM api_keys
                WHERE name = ? AND user_id = ?
                """,
                (name, user_id),
            )
            return cursor.rowcount > 0


# Global API Key manager instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create global API Key manager instance.

    Returns:
        APIKeyManager instance
    """
    global _api_key_manager

    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()

    return _api_key_manager


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[str]:
    """Verify API key from Authorization header (optional).

    Args:
        credentials: Authorization credentials from header

    Returns:
        user_id if authenticated, None if no credentials provided

    Raises:
        HTTPException: If invalid API key provided
    """
    if not credentials:
        # No authentication provided - return None (use default user)
        return None

    api_key = credentials.credentials
    manager = get_api_key_manager()

    user_id = manager.verify_key(api_key)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
