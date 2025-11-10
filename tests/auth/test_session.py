"""Tests for Redis Session Manager.

Issue #554 (Redis) + Issue #650 (Google OAuth2 Web Integration)
"""

import os
import time

import pytest

from kagura.auth.session import SessionManager


@pytest.mark.skipif(
    not os.getenv("TEST_REDIS_URL"),
    reason="TEST_REDIS_URL not set (Redis tests require Redis server)",
)
class TestSessionManager:
    """Test SessionManager with Redis backend.

    Note: Requires TEST_REDIS_URL environment variable.

    Example:
        export TEST_REDIS_URL=redis://localhost:6379/1
        pytest tests/auth/test_session.py
    """

    @pytest.fixture
    def redis_url(self):
        """Get test Redis URL from environment."""
        return os.getenv("TEST_REDIS_URL")

    @pytest.fixture
    def session_manager(self, redis_url):
        """Create SessionManager instance."""
        manager = SessionManager(redis_url=redis_url, session_ttl=3600)

        yield manager

        # Cleanup: Delete all test sessions
        try:
            keys = manager._redis.keys("session:*")
            if keys:
                manager._redis.delete(*keys)
        except Exception:
            pass

    def test_create_session(self, session_manager):
        """Test session creation."""
        user_info = {
            "sub": "test_user_001",
            "email": "test@example.com",
            "name": "Test User",
        }

        session_id = session_manager.create_session(user_info)

        assert session_id is not None
        assert len(session_id) > 20  # Secure token

    def test_get_session(self, session_manager):
        """Test session retrieval."""
        user_info = {
            "sub": "test_user_002",
            "email": "test2@example.com",
        }

        session_id = session_manager.create_session(user_info)

        # Get session
        session = session_manager.get_session(session_id)

        assert session is not None
        assert session["sub"] == "test_user_002"
        assert session["email"] == "test2@example.com"
        assert "created_at" in session
        assert "last_accessed" in session

    def test_get_nonexistent_session(self, session_manager):
        """Test getting non-existent session."""
        session = session_manager.get_session("invalid_session_id")

        assert session is None

    def test_delete_session(self, session_manager):
        """Test session deletion (logout)."""
        user_info = {"sub": "test_user_003", "email": "test3@example.com"}

        session_id = session_manager.create_session(user_info)

        # Session exists
        assert session_manager.get_session(session_id) is not None

        # Delete session
        deleted = session_manager.delete_session(session_id)
        assert deleted is True

        # Session should be gone
        assert session_manager.get_session(session_id) is None

    def test_update_session(self, session_manager):
        """Test session data update."""
        user_info = {"sub": "test_user_004", "email": "test4@example.com"}

        session_id = session_manager.create_session(user_info)

        # Update session
        updated = session_manager.update_session(
            session_id, {"preferences": {"theme": "dark"}}
        )
        assert updated is True

        # Get updated session
        session = session_manager.get_session(session_id)
        assert session is not None
        assert session["preferences"]["theme"] == "dark"

    def test_session_ttl_expiration(self, session_manager):
        """Test session TTL expiration."""
        # Create manager with short TTL
        short_ttl_manager = SessionManager(
            redis_url=session_manager.redis_url, session_ttl=2
        )

        user_info = {"sub": "test_user_ttl", "email": "ttl@example.com"}

        session_id = short_ttl_manager.create_session(user_info)

        # Session exists immediately
        assert short_ttl_manager.get_session(session_id) is not None

        # Wait for expiration
        time.sleep(3)

        # Session should be expired
        assert short_ttl_manager.get_session(session_id) is None

    def test_get_active_sessions_count(self, session_manager):
        """Test counting active sessions."""
        # Create multiple sessions
        for i in range(3):
            user_info = {"sub": f"test_user_count_{i}", "email": f"count{i}@example.com"}
            session_manager.create_session(user_info)

        count = session_manager.get_active_sessions_count()
        assert count >= 3  # At least the ones we created

    def test_last_accessed_update(self, session_manager):
        """Test that last_accessed is updated on get_session."""
        user_info = {"sub": "test_user_access", "email": "access@example.com"}

        session_id = session_manager.create_session(user_info)

        # Get initial session
        session1 = session_manager.get_session(session_id, update_access=False)
        last_accessed_1 = session1["last_accessed"]  # type: ignore[index]

        # Wait a bit
        time.sleep(1)

        # Get again with update
        session2 = session_manager.get_session(session_id, update_access=True)
        last_accessed_2 = session2["last_accessed"]  # type: ignore[index]

        # last_accessed should be updated
        assert last_accessed_2 > last_accessed_1

    def test_singleton_pattern(self, redis_url):
        """Test that multiple SessionManagers share same Redis client."""
        manager1 = SessionManager(redis_url=redis_url)
        manager2 = SessionManager(redis_url=redis_url)

        # Should share same Redis client
        assert manager1._redis is manager2._redis

        # Operations on manager1 should be visible in manager2
        user_info = {"sub": "test_singleton", "email": "singleton@example.com"}
        session_id = manager1.create_session(user_info)

        session = manager2.get_session(session_id)
        assert session is not None
        assert session["sub"] == "test_singleton"

        # Cleanup
        manager1.delete_session(session_id)
