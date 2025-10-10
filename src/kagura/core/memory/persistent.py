"""Persistent memory for long-term storage."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class PersistentMemory:
    """Long-term persistent memory using SQLite.

    Stores key-value pairs with optional agent scoping and metadata.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize persistent memory.

        Args:
            db_path: Path to SQLite database (default: ~/.kagura/memory.db)
        """
        self.db_path = db_path or Path.home() / ".kagura" / "memory.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    agent_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_key ON memories(key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_name)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_key_agent ON memories(key, agent_name)"
            )

    def store(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store persistent memory.

        Args:
            key: Memory key
            value: Value to store (will be JSON serialized)
            agent_name: Optional agent name for scoping
            metadata: Optional metadata
        """
        value_json = json.dumps(value)
        metadata_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            # Check if exists
            cursor = conn.execute(
                """
                SELECT id FROM memories
                WHERE key = ? AND (agent_name = ? OR (agent_name IS NULL AND ? IS NULL))
                """,
                (key, agent_name, agent_name),
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
                    INSERT INTO memories (key, value, agent_name, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, value_json, agent_name, metadata_json),
                )

    def recall(self, key: str, agent_name: Optional[str] = None) -> Optional[Any]:
        """Retrieve persistent memory.

        Args:
            key: Memory key
            agent_name: Optional agent name for scoping

        Returns:
            Stored value or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value FROM memories
                WHERE key = ? AND (agent_name = ? OR agent_name IS NULL)
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (key, agent_name),
            )

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])

        return None

    def search(
        self, query: str, agent_name: Optional[str] = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search memories by key pattern.

        Args:
            query: Search pattern (SQL LIKE pattern)
            agent_name: Optional agent name filter
            limit: Maximum results

        Returns:
            List of memory dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT key, value, created_at, updated_at, metadata
                FROM memories
                WHERE key LIKE ?
                  AND (agent_name = ? OR (agent_name IS NULL AND ? IS NULL))
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (f"%{query}%", agent_name, agent_name, limit),
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
                    }
                )

            return results

    def forget(self, key: str, agent_name: Optional[str] = None) -> None:
        """Delete memory.

        Args:
            key: Memory key to delete
            agent_name: Optional agent name for scoping
        """
        with sqlite3.connect(self.db_path) as conn:
            if agent_name:
                conn.execute(
                    "DELETE FROM memories WHERE key = ? AND agent_name = ?",
                    (key, agent_name),
                )
            else:
                conn.execute("DELETE FROM memories WHERE key = ?", (key,))

    def prune(self, older_than_days: int = 90, agent_name: Optional[str] = None) -> int:
        """Remove old memories.

        Args:
            older_than_days: Delete memories older than this many days
            agent_name: Optional agent name filter

        Returns:
            Number of deleted memories
        """
        with sqlite3.connect(self.db_path) as conn:
            if agent_name:
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

    def count(self, agent_name: Optional[str] = None) -> int:
        """Count stored memories.

        Args:
            agent_name: Optional agent name filter

        Returns:
            Number of memories
        """
        with sqlite3.connect(self.db_path) as conn:
            if agent_name:
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
