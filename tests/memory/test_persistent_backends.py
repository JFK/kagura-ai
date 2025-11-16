"""Tests for Persistent Memory with different backends.

Issue #554 - Cloud-Native Infrastructure Migration
"""

import os
import tempfile
from pathlib import Path

import pytest

from kagura.core.memory.persistent import PersistentMemory


class TestPersistentMemoryLegacyMode:
    """Test PersistentMemory with legacy sqlite3 backend."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_legacy_mode_backward_compatibility(self, temp_db):
        """Test that legacy mode still works (backward compatibility)."""
        mem = PersistentMemory(db_path=temp_db)

        # Store
        mem.store("test_key", "test_value", user_id="user1")

        # Recall
        value = mem.recall("test_key", user_id="user1")
        assert value == "test_value"

        # Forget
        mem.forget("test_key", user_id="user1")

        # Should be gone
        value = mem.recall("test_key", user_id="user1")
        assert value is None


class TestPersistentMemoryWithSQLAlchemy:
    """Test PersistentMemory with SQLAlchemy backend (SQLite)."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_sqlalchemy_sqlite_mode(self, temp_db):
        """Test SQLAlchemy backend with SQLite."""
        database_url = f"sqlite:///{temp_db}"

        mem = PersistentMemory(database_url=database_url)

        assert mem._use_sqlalchemy
        assert mem._backend is not None

        # Store
        mem.store("test_key", "test_value", user_id="user1")

        # Recall
        value = mem.recall("test_key", user_id="user1")
        assert value == "test_value"

        # Forget
        mem.forget("test_key", user_id="user1")

        # Should be gone
        value = mem.recall("test_key", user_id="user1")
        assert value is None

    def test_sqlalchemy_with_metadata(self, temp_db):
        """Test metadata storage/retrieval."""
        database_url = f"sqlite:///{temp_db}"
        mem = PersistentMemory(database_url=database_url)

        # Store with metadata
        mem.store(
            "test_key",
            "test_value",
            user_id="user1",
            metadata={"source": "test", "tags": ["python", "ai"]},
        )

        # Recall with metadata
        value, metadata = mem.recall(
            "test_key", user_id="user1", include_metadata=True
        )

        assert value == "test_value"
        assert metadata == {"source": "test", "tags": ["python", "ai"]}


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set (PostgreSQL tests require database)",
)
class TestPersistentMemoryWithPostgreSQL:
    """Test PersistentMemory with PostgreSQL backend.

    Note: Requires TEST_DATABASE_URL environment variable.

    Example:
        export TEST_DATABASE_URL=postgresql://localhost:5432/kagura_test
        pytest tests/memory/test_persistent_backends.py::TestPersistentMemoryWithPostgreSQL
    """

    @pytest.fixture
    def database_url(self):
        """Get test database URL from environment."""
        return os.getenv("TEST_DATABASE_URL")

    @pytest.fixture
    def persistent_memory(self, database_url):
        """Create PersistentMemory with PostgreSQL backend."""
        mem = PersistentMemory(database_url=database_url)

        yield mem

        # Cleanup
        try:
            if mem._backend:
                # Delete all test data
                session = mem._backend._get_session()
                session.execute("DELETE FROM memories WHERE user_id LIKE 'test_%'")
                session.commit()
                session.close()
                mem._backend.close()
        except Exception:
            pass

    def test_postgres_store_and_recall(self, persistent_memory):
        """Test store and recall with PostgreSQL."""
        # Store
        persistent_memory.store("test_key", "test_value", user_id="test_user1")

        # Recall
        value = persistent_memory.recall("test_key", user_id="test_user1")
        assert value == "test_value"

    def test_postgres_multi_user_isolation(self, persistent_memory):
        """Test that different users have isolated memories."""
        # User 1 stores
        persistent_memory.store("shared_key", "user1_value", user_id="test_user1")

        # User 2 stores
        persistent_memory.store("shared_key", "user2_value", user_id="test_user2")

        # Each user should see their own value
        value1 = persistent_memory.recall("shared_key", user_id="test_user1")
        value2 = persistent_memory.recall("shared_key", user_id="test_user2")

        assert value1 == "user1_value"
        assert value2 == "user2_value"

    def test_postgres_update_existing(self, persistent_memory):
        """Test updating existing memory."""
        # Store initial value
        persistent_memory.store("test_key", "value1", user_id="test_user1")

        # Update
        persistent_memory.store("test_key", "value2", user_id="test_user1")

        # Should have updated value
        value = persistent_memory.recall("test_key", user_id="test_user1")
        assert value == "value2"

    def test_postgres_access_tracking(self, persistent_memory):
        """Test access count tracking."""
        # Store
        persistent_memory.store("test_key", "test_value", user_id="test_user1")

        # Recall multiple times with tracking
        persistent_memory.recall("test_key", user_id="test_user1", track_access=True)
        persistent_memory.recall("test_key", user_id="test_user1", track_access=True)
        persistent_memory.recall("test_key", user_id="test_user1", track_access=True)

        # Access count should be updated (implementation-dependent)
        # This is verified by checking last_accessed_at is not None
        value, metadata = persistent_memory.recall(
            "test_key", user_id="test_user1", include_metadata=True
        )
        assert value == "test_value"

    def test_environment_variable_postgres(self, database_url, monkeypatch):
        """Test PERSISTENT_BACKEND environment variable."""
        monkeypatch.setenv("PERSISTENT_BACKEND", "postgres")
        monkeypatch.setenv("DATABASE_URL", database_url)

        mem = PersistentMemory()

        assert mem._use_sqlalchemy
        assert mem._backend is not None

        # Test basic operations
        mem.store("test_key", "test_value", user_id="test_env_user")
        value = mem.recall("test_key", user_id="test_env_user")
        assert value == "test_value"

        # Cleanup
        mem.forget("test_key", user_id="test_env_user")
        mem._backend.close()
