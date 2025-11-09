"""Tests for kagura.utils.db module."""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from kagura.utils.common.db import MemoryDatabaseQuery, db_exists, get_db_path


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "memory.db"

        # Create test database with schema
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE memories (
                id INTEGER PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT,
                user_id TEXT,
                agent_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Insert test data
        test_data = [
            ("memory_1", "value1", "alice", "agent1"),
            ("memory_2", "value2", "alice", "agent1"),
            ("memory_3", "value3", "bob", "agent2"),
            (
                "coding_session:1",
                json.dumps({"project_id": "kagura-ai"}),
                "alice",
                "global",
            ),
            (
                "coding_session:2",
                json.dumps({"project_id": "kagura-ai"}),
                "alice",
                "global",
            ),
            (
                "coding_session:3",
                json.dumps({"project_id": "my-project"}),
                "alice",
                "global",
            ),
            (
                "coding_session:4",
                json.dumps({"project_id": "kagura-ai"}),
                "bob",
                "global",
            ),
        ]

        for key, value, user_id, agent_name in test_data:
            conn.execute(
                "INSERT INTO memories (key, value, user_id, agent_name) VALUES (?, ?, ?, ?)",
                (key, value, user_id, agent_name),
            )

        conn.commit()
        conn.close()

        # Patch get_db_path to return test database
        with patch("kagura.utils.db.get_db_path", return_value=db_path):
            yield db_path


class TestGetDbPath:
    """Tests for get_db_path function."""

    def test_returns_path(self):
        """Test that get_db_path returns a Path object."""
        result = get_db_path()
        assert isinstance(result, Path)
        assert result.name == "memory.db"


class TestDbExists:
    """Tests for db_exists function."""

    def test_exists_with_real_db(self, temp_db):
        """Test db_exists returns True when database exists."""
        assert db_exists() is True

    def test_not_exists(self):
        """Test db_exists returns False when database doesn't exist."""
        with patch(
            "kagura.utils.db.get_db_path", return_value=Path("/nonexistent/memory.db")
        ):
            assert db_exists() is False


class TestCountMemories:
    """Tests for MemoryDatabaseQuery.count_memories."""

    def test_count_all_memories(self, temp_db):
        """Test counting all memories."""
        count = MemoryDatabaseQuery.count_memories()
        assert count == 7  # Total in test data

    def test_count_by_user(self, temp_db):
        """Test counting memories for specific user."""
        count_alice = MemoryDatabaseQuery.count_memories(user_id="alice")
        count_bob = MemoryDatabaseQuery.count_memories(user_id="bob")

        assert count_alice == 5  # alice has 5 memories
        assert count_bob == 2  # bob has 2 memories

    def test_count_nonexistent_user(self, temp_db):
        """Test counting memories for nonexistent user."""
        count = MemoryDatabaseQuery.count_memories(user_id="nonexistent")
        assert count == 0

    def test_count_no_database(self):
        """Test counting when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            count = MemoryDatabaseQuery.count_memories()
            assert count == 0


class TestListUsers:
    """Tests for MemoryDatabaseQuery.list_users."""

    def test_list_users(self, temp_db):
        """Test listing all users."""
        users = MemoryDatabaseQuery.list_users()
        assert sorted(users) == ["alice", "bob"]

    def test_list_users_no_database(self):
        """Test listing users when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            users = MemoryDatabaseQuery.list_users()
            assert users == []


class TestGetUserStats:
    """Tests for MemoryDatabaseQuery.get_user_stats."""

    def test_get_user_stats(self, temp_db):
        """Test getting user statistics."""
        stats = MemoryDatabaseQuery.get_user_stats()

        # Should be sorted by count descending
        assert len(stats) == 2
        assert stats[0] == ("alice", 5)  # alice has more
        assert stats[1] == ("bob", 2)

    def test_get_user_stats_no_database(self):
        """Test getting stats when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            stats = MemoryDatabaseQuery.get_user_stats()
            assert stats == []


class TestGetDbSizeMb:
    """Tests for MemoryDatabaseQuery.get_db_size_mb."""

    def test_get_db_size(self, temp_db):
        """Test getting database size."""
        size_mb = MemoryDatabaseQuery.get_db_size_mb()
        assert size_mb > 0.0
        assert size_mb < 1.0  # Test DB should be small

    def test_get_db_size_no_database(self):
        """Test getting size when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            size_mb = MemoryDatabaseQuery.get_db_size_mb()
            assert size_mb == 0.0


class TestListProjects:
    """Tests for MemoryDatabaseQuery.list_projects."""

    def test_list_projects_for_user(self, temp_db):
        """Test listing projects for a user."""
        projects = MemoryDatabaseQuery.list_projects("alice")

        assert len(projects) == 2
        # Sorted by session count descending
        assert projects[0]["project_id"] == "kagura-ai"
        assert projects[0]["session_count"] == 2
        assert projects[1]["project_id"] == "my-project"
        assert projects[1]["session_count"] == 1

    def test_list_projects_for_different_user(self, temp_db):
        """Test listing projects for different user."""
        projects = MemoryDatabaseQuery.list_projects("bob")

        assert len(projects) == 1
        assert projects[0]["project_id"] == "kagura-ai"
        assert projects[0]["session_count"] == 1

    def test_list_projects_no_sessions(self, temp_db):
        """Test listing projects for user with no sessions."""
        projects = MemoryDatabaseQuery.list_projects("charlie")
        assert projects == []

    def test_list_projects_no_database(self):
        """Test listing projects when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            projects = MemoryDatabaseQuery.list_projects("alice")
            assert projects == []


class TestCountSessions:
    """Tests for MemoryDatabaseQuery.count_sessions."""

    def test_count_all_sessions_for_user(self, temp_db):
        """Test counting all sessions for a user."""
        count_alice = MemoryDatabaseQuery.count_sessions("alice")
        count_bob = MemoryDatabaseQuery.count_sessions("bob")

        assert count_alice == 3
        assert count_bob == 1

    def test_count_sessions_by_project(self, temp_db):
        """Test counting sessions for specific project."""
        count = MemoryDatabaseQuery.count_sessions("alice", "kagura-ai")
        assert count == 2

        count = MemoryDatabaseQuery.count_sessions("alice", "my-project")
        assert count == 1

    def test_count_sessions_nonexistent_project(self, temp_db):
        """Test counting sessions for nonexistent project."""
        count = MemoryDatabaseQuery.count_sessions("alice", "nonexistent")
        assert count == 0

    def test_count_sessions_no_database(self):
        """Test counting sessions when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            count = MemoryDatabaseQuery.count_sessions("alice")
            assert count == 0


class TestExecuteQuery:
    """Tests for MemoryDatabaseQuery.execute_query."""

    def test_execute_select_query(self, temp_db):
        """Test executing a SELECT query."""
        results = MemoryDatabaseQuery.execute_query(
            "SELECT key FROM memories WHERE user_id = ? LIMIT 2", ("alice",)
        )

        assert len(results) == 2
        assert all(isinstance(row, tuple) for row in results)

    def test_execute_count_query(self, temp_db):
        """Test executing a COUNT query."""
        results = MemoryDatabaseQuery.execute_query(
            "SELECT COUNT(*) FROM memories WHERE user_id = ?", ("alice",)
        )

        assert len(results) == 1
        assert results[0][0] == 5

    def test_execute_query_no_params(self, temp_db):
        """Test executing query without parameters."""
        results = MemoryDatabaseQuery.execute_query("SELECT COUNT(*) FROM memories")

        assert len(results) == 1
        assert results[0][0] == 7

    def test_execute_non_select_query_raises(self, temp_db):
        """Test that non-SELECT queries raise ValueError."""
        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            MemoryDatabaseQuery.execute_query("INSERT INTO memories VALUES (1, 'test')")

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            MemoryDatabaseQuery.execute_query("UPDATE memories SET key = 'test'")

        with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
            MemoryDatabaseQuery.execute_query("DELETE FROM memories")

    def test_execute_query_no_database(self):
        """Test executing query when database doesn't exist."""
        with patch("kagura.utils.db.db_exists", return_value=False):
            results = MemoryDatabaseQuery.execute_query("SELECT * FROM memories")
            assert results == []

    def test_execute_query_invalid_sql_raises(self, temp_db):
        """Test that invalid SQL raises sqlite3.Error."""
        with pytest.raises(sqlite3.Error):
            MemoryDatabaseQuery.execute_query("SELECT * FROM nonexistent_table")


class TestErrorHandling:
    """Tests for error handling in database operations."""

    def test_count_memories_database_error(self, temp_db):
        """Test that database errors are handled gracefully."""
        # Corrupt the database connection
        with patch("sqlite3.connect", side_effect=sqlite3.Error("Connection error")):
            count = MemoryDatabaseQuery.count_memories()
            assert count == 0

    def test_list_users_database_error(self, temp_db):
        """Test that list_users handles errors gracefully."""
        with patch("sqlite3.connect", side_effect=sqlite3.Error("Connection error")):
            users = MemoryDatabaseQuery.list_users()
            assert users == []

    def test_get_db_size_os_error(self):
        """Test that get_db_size_mb handles OS errors gracefully."""
        with patch("kagura.utils.db.get_db_path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.stat.side_effect = OSError("Permission denied")

            size = MemoryDatabaseQuery.get_db_size_mb()
            assert size == 0.0
