"""Event store for telemetry data."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


class EventStore:
    """Store telemetry events in SQLite database.

    Example:
        >>> store = EventStore()
        >>> await store.save_execution({
        ...     "id": "exec_123",
        ...     "agent_name": "my_agent",
        ...     "status": "completed",
        ... })
        >>> executions = store.get_executions(agent_name="my_agent")
    """

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        """Initialize event store.

        Args:
            db_path: Path to SQLite database. If None, uses ~/.kagura/telemetry.db
                Can also be ":memory:" for in-memory database (testing).
        """
        if db_path is None:
            db_path = Path.home() / ".kagura" / "telemetry.db"
        elif isinstance(db_path, str) and db_path != ":memory:":
            db_path = Path(db_path)

        self.db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None

        # Create parent directory if needed
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # For :memory: databases, keep a persistent connection
        if self.db_path == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:")

        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        close_conn = self._memory_conn is None

        try:
            # Create executions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    ended_at REAL,
                    duration REAL,
                    status TEXT,
                    error TEXT,
                    kwargs TEXT,
                    events TEXT,
                    metrics TEXT,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)

            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_started
                ON executions(agent_name, started_at DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON executions(status)
            """)

            conn.commit()
        finally:
            if close_conn:
                conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        # Return persistent connection for :memory: databases
        if self._memory_conn is not None:
            return self._memory_conn

        # Create new connection for file-based databases
        if isinstance(self.db_path, Path):
            return sqlite3.connect(str(self.db_path))
        return sqlite3.connect(self.db_path)

    def _should_close_connection(self) -> bool:
        """Check if connection should be closed after operation.

        Returns:
            False for :memory: databases (persistent connection),
            True for file-based databases
        """
        return self._memory_conn is None

    async def save_execution(self, execution: dict[str, Any]) -> None:
        """Save execution record.

        Args:
            execution: Execution data dictionary containing:
                - id: Execution ID
                - agent_name: Name of the agent
                - started_at: Start timestamp
                - ended_at: End timestamp (optional)
                - duration: Duration in seconds (optional)
                - status: Execution status (optional)
                - error: Error message if failed (optional)
                - kwargs: Agent arguments (optional)
                - events: List of events (optional)
                - metrics: Metrics dictionary (optional)
        """
        conn = self._get_connection()

        try:
            conn.execute(
                """
                INSERT INTO executions
                (id, agent_name, started_at, ended_at, duration,
                 status, error, kwargs, events, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution["id"],
                    execution["agent_name"],
                    execution["started_at"],
                    execution.get("ended_at"),
                    execution.get("duration"),
                    execution.get("status"),
                    execution.get("error"),
                    json.dumps(execution.get("kwargs", {})),
                    json.dumps(execution.get("events", [])),
                    json.dumps(execution.get("metrics", {})),
                ),
            )
            conn.commit()
        finally:
            if self._should_close_connection():
                conn.close()

    def get_execution(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Get execution by ID (supports partial ID matching).

        Args:
            execution_id: Execution ID (can be partial, e.g., "exec_951c348")

        Returns:
            Execution dict or None if not found
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        try:
            # Try exact match first
            cursor = conn.execute(
                "SELECT * FROM executions WHERE id = ?", (execution_id,)
            )
            row = cursor.fetchone()

            # If not found, try partial match (prefix)
            if row is None:
                cursor = conn.execute(
                    """SELECT * FROM executions WHERE id LIKE ?
                    ORDER BY started_at DESC LIMIT 1""",
                    (f"{execution_id}%",),
                )
                row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_dict(row)
        finally:
            if self._should_close_connection():
                conn.close()

    def get_executions(
        self,
        agent_name: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query execution records.

        Args:
            agent_name: Filter by agent name
            status: Filter by status
            since: Filter by start time (timestamp)
            limit: Maximum number of records to return

        Returns:
            List of execution dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row

        try:
            query = "SELECT * FROM executions WHERE 1=1"
            params: list[Any] = []

            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            if status:
                query += " AND status = ?"
                params.append(status)

            if since:
                query += " AND started_at >= ?"
                params.append(since)

            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]
        finally:
            if self._should_close_connection():
                conn.close()

    def get_summary_stats(
        self, agent_name: Optional[str] = None, since: Optional[float] = None
    ) -> dict[str, Any]:
        """Get summary statistics.

        Args:
            agent_name: Filter by agent name
            since: Filter by start time (timestamp)

        Returns:
            Dictionary containing:
                - total_executions: Total number of executions
                - completed: Number of completed executions
                - failed: Number of failed executions
                - avg_duration: Average duration in seconds
                - total_cost: Total cost (if available)
        """
        conn = self._get_connection()

        try:
            query = """
                SELECT
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(duration) as avg_duration
                FROM executions
                WHERE 1=1
            """
            params: list[Any] = []

            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)

            if since:
                query += " AND started_at >= ?"
                params.append(since)

            cursor = conn.execute(query, params)
            row = cursor.fetchone()

            return {
                "total_executions": row[0] or 0,
                "completed": row[1] or 0,
                "failed": row[2] or 0,
                "avg_duration": row[3] or 0.0,
            }
        finally:
            if self._should_close_connection():
                conn.close()

    def delete_old_executions(self, older_than: float) -> int:
        """Delete executions older than timestamp.

        Args:
            older_than: Timestamp threshold

        Returns:
            Number of deleted records
        """
        conn = self._get_connection()

        try:
            cursor = conn.execute(
                "DELETE FROM executions WHERE started_at < ?", (older_than,)
            )
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            if self._should_close_connection():
                conn.close()

    def clear_all(self) -> None:
        """Clear all execution records."""
        conn = self._get_connection()

        try:
            conn.execute("DELETE FROM executions")
            conn.commit()
        finally:
            if self._should_close_connection():
                conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """Convert SQLite row to dictionary.

        Args:
            row: SQLite row

        Returns:
            Dictionary representation
        """
        data = dict(row)

        # Parse JSON fields
        if data.get("kwargs"):
            data["kwargs"] = json.loads(data["kwargs"])
        if data.get("events"):
            data["events"] = json.loads(data["events"])
        if data.get("metrics"):
            data["metrics"] = json.loads(data["metrics"])

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"EventStore(db_path={self.db_path!r})"
