"""Persistent memory for long-term storage.

Issue #554: Added PostgreSQL support via SQLAlchemy backend.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from kagura.config.paths import get_data_dir

logger = logging.getLogger(__name__)


class PersistentMemory:
    """Long-term persistent memory using SQLite or PostgreSQL.

    Stores key-value pairs with optional agent scoping and metadata.

    Backends:
        - SQLite (default): File-based, single-instance
        - PostgreSQL (production): Cloud-native, multi-instance

    Args:
        db_path: Path to SQLite database (legacy, SQLite only)
        database_url: Database connection URL (SQLite or PostgreSQL)
            - SQLite: sqlite:///path/to/memory.db
            - PostgreSQL: postgresql://user:pass@host:5432/db
        use_sqlalchemy: Use SQLAlchemy backend (supports PostgreSQL)
            Auto-detected from DATABASE_URL or PERSISTENT_BACKEND env var

    Example:
        >>> # Legacy SQLite (sqlite3 module)
        >>> mem = PersistentMemory(db_path=Path("memory.db"))
        >>>
        >>> # SQLite with SQLAlchemy
        >>> mem = PersistentMemory(database_url="sqlite:///memory.db")
        >>>
        >>> # PostgreSQL (production)
        >>> mem = PersistentMemory(database_url="postgresql://localhost:5432/kagura")
        >>>
        >>> # Environment-based (recommended)
        >>> # Set PERSISTENT_BACKEND=postgres, DATABASE_URL=postgresql://...
        >>> mem = PersistentMemory()
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        database_url: Optional[str] = None,
        use_sqlalchemy: Optional[bool] = None,
    ) -> None:
        """Initialize persistent memory.

        Args:
            db_path: Path to SQLite database (legacy mode)
            database_url: Database connection URL (SQLAlchemy mode)
            use_sqlalchemy: Force SQLAlchemy backend (auto-detect if None)
        """
        # Determine backend mode
        if use_sqlalchemy is None:
            # Auto-detect from environment or database_url
            env_backend = os.getenv("PERSISTENT_BACKEND", "sqlite")
            use_sqlalchemy = (
                env_backend == "postgres"
                or (database_url is not None)
                # Note: Don't auto-enable SQLAlchemy just because DATABASE_URL exists
                # Only use it if explicitly requested via PERSISTENT_BACKEND=postgres
            )

        if use_sqlalchemy:
            # SQLAlchemy backend (supports PostgreSQL)
            from .backends import SQLAlchemyPersistentBackend

            # Determine database URL
            if database_url:
                self._database_url = database_url
            else:
                env_db_url = os.getenv("DATABASE_URL")
                if env_db_url:
                    self._database_url = env_db_url
                else:
                    # Default to SQLite via SQLAlchemy
                    db_path = db_path or get_data_dir() / "memory.db"
                    self._database_url = f"sqlite:///{db_path}"

            self._backend = SQLAlchemyPersistentBackend(self._database_url)
            self._use_sqlalchemy = True
            logger.info(f"Using SQLAlchemy backend: {self._backend._get_backend_type()}")

        else:
            # Legacy sqlite3 backend
            self.db_path = db_path or get_data_dir() / "memory.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_db()
            self._backend = None
            self._use_sqlalchemy = False
            logger.info("Using legacy sqlite3 backend")

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Migration: Add user_id column to existing tables (before creating indexes)
            try:
                conn.execute(
                    """ALTER TABLE memories ADD COLUMN user_id TEXT
                       NOT NULL DEFAULT 'default_user'"""
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Migration: Add access tracking columns (v4.0.0a0)
            try:
                conn.execute(
                    "ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0"
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                conn.execute(
                    "ALTER TABLE memories ADD COLUMN last_accessed_at TIMESTAMP"
                )
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Create indexes (after ensuring all columns exist)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON memories(key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_name)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_key_agent ON memories(key, agent_name)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON memories(user_id)")
            conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_user_agent
                   ON memories(user_id, agent_name)"""
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_key ON memories(user_id, key)"
            )

    def store(
        self,
        key: str,
        value: Any,
        user_id: str,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store persistent memory.

        Args:
            key: Memory key
            value: Value to store (will be JSON serialized)
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
            metadata: Optional metadata
        """
        if self._use_sqlalchemy and self._backend:
            # Use SQLAlchemy backend (PostgreSQL or SQLite)
            self._backend.store(key, value, user_id, agent_name, metadata)
            return

        # Legacy sqlite3 implementation
        value_json = json.dumps(value)
        metadata_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            # Check if exists (user_id + key + agent_name combination)
            cursor = conn.execute(
                """
                SELECT id FROM memories
                WHERE key = ? AND user_id = ?
                  AND (agent_name = ? OR (agent_name IS NULL AND ? IS NULL))
                """,
                (key, user_id, agent_name, agent_name),
            )
            existing = cursor.fetchone()

            if existing:
                # Update
                conn.execute(
                    """
                    UPDATE memories
                    SET value = ?, updated_at = ?, metadata = ?
                    WHERE id = ?
                    """,
                    (value_json, datetime.now(), metadata_json, existing[0]),
                )
            else:
                # Insert
                conn.execute(
                    """
                    INSERT INTO memories (key, value, user_id, agent_name, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (key, value_json, user_id, agent_name, metadata_json),
                )

    def recall(
        self,
        key: str,
        user_id: str,
        agent_name: Optional[str] = None,
        track_access: bool = False,
        include_metadata: bool = False,
    ) -> Optional[Any]:
        """Retrieve persistent memory.

        Args:
            key: Memory key
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
            track_access: If True, record access for frequency tracking
            include_metadata: If True, return tuple of (value, metadata)

        Returns:
            Stored value or tuple of (value, metadata) if include_metadata is True.
        """
        if self._use_sqlalchemy and self._backend:
            # Use SQLAlchemy backend
            return self._backend.recall(key, user_id, agent_name, track_access, include_metadata)

        # Legacy sqlite3 implementation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value, metadata, agent_name
                FROM memories
                WHERE key = ? AND user_id = ?
                  AND (agent_name = ? OR agent_name IS NULL)
                ORDER BY CASE
                    WHEN agent_name = ? THEN 0
                    WHEN agent_name IS NULL THEN 1
                    ELSE 2
                END,
                updated_at DESC
                LIMIT 1
                """,
                (key, user_id, agent_name, agent_name),
            )

            row = cursor.fetchone()
            if row:
                value_json, metadata_json, row_agent_name = row
                value = json.loads(value_json)
                metadata = json.loads(metadata_json) if metadata_json else None

                # Track access if requested
                if track_access:
                    self.record_access(key, user_id, row_agent_name)

                if include_metadata:
                    return value, metadata
                return value

        if include_metadata:
            return None
        return None

    def record_access(
        self, key: str, user_id: str, agent_name: Optional[str] = None
    ) -> None:
        """Record memory access for frequency tracking.

        Updates access_count and last_accessed_at for the specified memory.
        Used by RecallScorer for multi-dimensional recall scoring.

        Args:
            key: Memory key
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping

        Note:
            This is called automatically by recall() when track_access=True.
        """
        if self._use_sqlalchemy and self._backend:
            # Use SQLAlchemy backend
            self._backend.record_access(key, user_id, agent_name)
            return

        # Legacy sqlite3 implementation
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE memories
                SET access_count = COALESCE(access_count, 0) + 1,
                    last_accessed_at = ?
                WHERE key = ? AND user_id = ?
                  AND (agent_name = ? OR (agent_name IS NULL AND ? IS NULL))
                """,
                (datetime.now().isoformat(), key, user_id, agent_name, agent_name),
            )

    def search(
        self,
        query: str,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memories by key pattern.

        Args:
            query: Search pattern (SQL LIKE pattern)
            user_id: User identifier (filter by owner)
            agent_name: Optional agent name filter
            limit: Maximum results

        Returns:
            List of memory dictionaries with access tracking info
        """
        # Use SQLAlchemy backend if enabled
        if self._use_sqlalchemy and self._backend:
            return self._backend.search(query, user_id, agent_name, limit)

        # Legacy sqlite3 implementation
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT key, value, created_at, updated_at, metadata,
                       access_count, last_accessed_at
                FROM memories
                WHERE key LIKE ? AND user_id = ?
                  AND (agent_name = ? OR (agent_name IS NULL AND ? IS NULL))
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f"%{query}%", user_id, agent_name, agent_name, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "key": row[0],
                        "value": json.loads(row[1]),
                        "created_at": row[2],
                        "updated_at": row[3],
                        "metadata": json.loads(row[4]) if row[4] else None,
                        "access_count": row[5] if row[5] is not None else 0,
                        "last_accessed_at": row[6],
                    }
                )

            return results

    def fetch_all(
        self,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Fetch all memories for a user (optionally scoped by agent).

        Args:
            user_id: User identifier (memory owner)
            agent_name: Optional agent name filter
            limit: Optional maximum number of results to return

        Returns:
            List of memory dictionaries ordered by updated_at descending
        """
        # Use backend if available (SQLAlchemy mode)
        if self._use_sqlalchemy and self._backend:
            return self._backend.fetch_all(user_id, agent_name, limit)

        # Legacy sqlite3 mode
        query_parts = [
            "SELECT key, value, created_at, updated_at, metadata,",
            "       access_count, last_accessed_at",
            "FROM memories",
            "WHERE user_id = ?",
        ]
        params: list[Any] = [user_id]

        if agent_name is not None:
            # Include both agent-scoped AND global (agent_name IS NULL) memories
            # This matches the logic in recall() and search()
            query_parts.append("  AND (agent_name = ? OR agent_name IS NULL)")
            params.append(agent_name)

        query_parts.append("ORDER BY updated_at DESC")
        if limit is not None:
            query_parts.append("LIMIT ?")
            params.append(limit)

        sql = "\n".join(query_parts)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(sql, tuple(params))

            results: list[dict[str, Any]] = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "key": row[0],
                        "value": json.loads(row[1]),
                        "created_at": row[2],
                        "updated_at": row[3],
                        "metadata": json.loads(row[4]) if row[4] else None,
                        "access_count": row[5] if row[5] is not None else 0,
                        "last_accessed_at": row[6],
                    }
                )

            return results

    def forget(self, key: str, user_id: str, agent_name: Optional[str] = None) -> None:
        """Delete memory.

        Args:
            key: Memory key to delete
            user_id: User identifier (memory owner)
            agent_name: Optional agent name for scoping
        """
        if self._use_sqlalchemy and self._backend:
            # Use SQLAlchemy backend
            self._backend.delete(key, user_id, agent_name)
            return

        # Legacy sqlite3 implementation
        with sqlite3.connect(self.db_path) as conn:
            if agent_name:
                conn.execute(
                    """DELETE FROM memories
                       WHERE key = ? AND user_id = ? AND agent_name = ?""",
                    (key, user_id, agent_name),
                )
            else:
                conn.execute(
                    "DELETE FROM memories WHERE key = ? AND user_id = ?",
                    (key, user_id),
                )

    def prune(
        self,
        older_than_days: int = 90,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> int:
        """Remove old memories.

        Args:
            older_than_days: Delete memories older than this many days
            user_id: Optional user identifier filter (None = all users)
            agent_name: Optional agent name filter

        Returns:
            Number of deleted memories
        """
        with sqlite3.connect(self.db_path) as conn:
            if user_id and agent_name:
                cursor = conn.execute(
                    """
                    DELETE FROM memories
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    AND user_id = ? AND agent_name = ?
                    """,
                    (older_than_days, user_id, agent_name),
                )
            elif user_id:
                cursor = conn.execute(
                    """
                    DELETE FROM memories
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    AND user_id = ?
                    """,
                    (older_than_days, user_id),
                )
            elif agent_name:
                cursor = conn.execute(
                    """
                    DELETE FROM memories
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    AND agent_name = ?
                    """,
                    (older_than_days, agent_name),
                )
            else:
                cursor = conn.execute(
                    """
                    DELETE FROM memories
                    WHERE updated_at < datetime('now', '-' || ? || ' days')
                    """,
                    (older_than_days,),
                )
            return cursor.rowcount

    def count(
        self, user_id: Optional[str] = None, agent_name: Optional[str] = None
    ) -> int:
        """Count stored memories.

        Args:
            user_id: Optional user identifier filter (None = all users)
            agent_name: Optional agent name filter

        Returns:
            Number of memories
        """
        # Use SQLAlchemy backend if available
        if self._use_sqlalchemy and self._backend:
            return self._backend.count(user_id, agent_name)

        # Fallback to direct SQLite access
        with sqlite3.connect(self.db_path) as conn:
            if user_id and agent_name:
                cursor = conn.execute(
                    """SELECT COUNT(*) FROM memories
                       WHERE user_id = ? AND agent_name = ?""",
                    (user_id, agent_name),
                )
            elif user_id:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)
                )
            elif agent_name:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE agent_name = ?",
                    (agent_name,),
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM memories")

            return cursor.fetchone()[0]

    def __repr__(self) -> str:
        """String representation."""
        return f"PersistentMemory(db={self.db_path}, count={self.count()})"
