"""Database query helpers for consistent memory database access.

Shared database utilities for querying the Kagura AI memory database (SQLite).
These helpers eliminate duplicate SQL queries across CLI, API, and MCP layers.
"""

import sqlite3
from pathlib import Path
from typing import Any

from kagura.config.paths import get_data_dir


def get_db_path() -> Path:
    """Get the path to the memory database.

    Returns:
        Path to memory.db in the data directory

    Examples:
        >>> db_path = get_db_path()
        >>> db_path.name
        'memory.db'
    """
    return get_data_dir() / "memory.db"


def db_exists() -> bool:
    """Check if the memory database exists.

    Returns:
        True if memory.db exists, False otherwise

    Examples:
        >>> db_exists()
        True  # or False if not initialized
    """
    return get_db_path().exists()


class MemoryDatabaseQuery:
    """Shared database query utilities for memory system.

    Provides read-only query methods for common database operations.
    All methods use context managers to ensure proper connection cleanup.
    """

    @staticmethod
    def count_memories(user_id: str | None = None) -> int:
        """Count memories in the database.

        Args:
            user_id: Optional user ID filter. If None, counts all memories.

        Returns:
            Number of memories (0 if database doesn't exist)

        Examples:
            >>> MemoryDatabaseQuery.count_memories()
            1234

            >>> MemoryDatabaseQuery.count_memories(user_id="alice")
            42
        """
        if not db_exists():
            return 0

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                if user_id is None:
                    cursor = conn.execute("SELECT COUNT(*) FROM memories")
                else:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,)
                    )
                result = cursor.fetchone()
                return result[0] if result else 0
        except (sqlite3.Error, Exception):
            return 0

    @staticmethod
    def list_users() -> list[str]:
        """Get all unique user IDs from the database.

        Returns:
            List of user IDs (empty if database doesn't exist)

        Examples:
            >>> MemoryDatabaseQuery.list_users()
            ['alice', 'bob', 'charlie']
        """
        if not db_exists():
            return []

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    "SELECT DISTINCT user_id FROM memories WHERE user_id IS NOT NULL"
                )
                return [row[0] for row in cursor.fetchall()]
        except (sqlite3.Error, Exception):
            return []

    @staticmethod
    def get_user_stats() -> list[tuple[str, int]]:
        """Get memory count per user.

        Returns:
            List of (user_id, count) tuples, sorted by count descending

        Examples:
            >>> MemoryDatabaseQuery.get_user_stats()
            [('alice', 100), ('bob', 50), ('charlie', 25)]
        """
        if not db_exists():
            return []

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    "SELECT user_id, COUNT(*) as count FROM memories "
                    "WHERE user_id IS NOT NULL "
                    "GROUP BY user_id "
                    "ORDER BY count DESC"
                )
                return cursor.fetchall()
        except (sqlite3.Error, Exception):
            return []

    @staticmethod
    def get_db_size_mb() -> float:
        """Get database file size in megabytes.

        Returns:
            Database size in MB (0.0 if database doesn't exist)

        Examples:
            >>> MemoryDatabaseQuery.get_db_size_mb()
            12.5
        """
        if not db_exists():
            return 0.0

        db_path = get_db_path()
        try:
            size_bytes = db_path.stat().st_size
            return size_bytes / (1024 * 1024)  # Convert to MB
        except (OSError, Exception):
            return 0.0

    @staticmethod
    def list_projects(user_id: str) -> list[dict[str, Any]]:
        """Get all projects for a user (from coding memory).

        Args:
            user_id: User ID to query projects for

        Returns:
            List of project dictionaries with project_id and session count

        Examples:
            >>> MemoryDatabaseQuery.list_projects("alice")
            [
                {'project_id': 'kagura-ai', 'session_count': 10},
                {'project_id': 'my-project', 'session_count': 5}
            ]
        """
        if not db_exists():
            return []

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                # Query from memories table where key starts with coding_session
                cursor = conn.execute(
                    """
                    SELECT value FROM memories
                    WHERE user_id = ?
                    AND key LIKE 'coding_session:%'
                    """,
                    (user_id,),
                )

                # Parse project_id from session data
                projects: dict[str, int] = {}
                for row in cursor.fetchall():
                    try:
                        import json

                        session_data = json.loads(row[0])
                        project_id = session_data.get("project_id")
                        if project_id:
                            projects[project_id] = projects.get(project_id, 0) + 1
                    except (json.JSONDecodeError, Exception):
                        continue

                # Convert to list of dicts
                return [
                    {"project_id": proj_id, "session_count": count}
                    for proj_id, count in sorted(
                        projects.items(), key=lambda x: x[1], reverse=True
                    )
                ]
        except (sqlite3.Error, Exception):
            return []

    @staticmethod
    def count_sessions(user_id: str, project_id: str | None = None) -> int:
        """Count coding sessions for a user/project.

        Args:
            user_id: User ID to query
            project_id: Optional project filter

        Returns:
            Number of coding sessions

        Examples:
            >>> MemoryDatabaseQuery.count_sessions("alice")
            15

            >>> MemoryDatabaseQuery.count_sessions("alice", "kagura-ai")
            10
        """
        if not db_exists():
            return 0

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM memories
                    WHERE user_id = ?
                    AND key LIKE 'coding_session:%'
                    """,
                    (user_id,),
                )
                total = cursor.fetchone()[0] if cursor else 0

                # If project_id specified, filter in Python (no project column in DB)
                if project_id is not None:
                    cursor = conn.execute(
                        """
                        SELECT value FROM memories
                        WHERE user_id = ?
                        AND key LIKE 'coding_session:%'
                        """,
                        (user_id,),
                    )

                    count = 0
                    for row in cursor.fetchall():
                        try:
                            import json

                            session_data = json.loads(row[0])
                            if session_data.get("project_id") == project_id:
                                count += 1
                        except (json.JSONDecodeError, Exception):
                            continue
                    return count

                return total
        except (sqlite3.Error, Exception):
            return 0

    @staticmethod
    def execute_query(query: str, params: tuple = ()) -> list[tuple]:
        """Execute a custom read-only SQL query.

        WARNING: This is a low-level method. Use specific query methods when possible.

        Args:
            query: SQL SELECT query
            params: Query parameters (for parameterized queries)

        Returns:
            List of result tuples

        Raises:
            ValueError: If query is not a SELECT statement
            sqlite3.Error: On database errors

        Examples:
            >>> MemoryDatabaseQuery.execute_query(
            ...     "SELECT key FROM memories WHERE user_id = ? LIMIT 5",
            ...     ("alice",)
            ... )
            [('memory_1',), ('memory_2',), ...]
        """
        if not db_exists():
            return []

        # Safety check: only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            msg = "Only SELECT queries are allowed (read-only)"
            raise ValueError(msg)

        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error:
            raise  # Re-raise database errors
