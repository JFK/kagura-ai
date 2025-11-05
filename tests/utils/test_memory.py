"""Tests for kagura.utils.memory module."""

from unittest.mock import MagicMock, patch

import pytest

from kagura.utils.memory import MemoryManagerFactory, get_memory_manager


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    MemoryManagerFactory.clear_cache()
    yield
    MemoryManagerFactory.clear_cache()


@pytest.fixture
def mock_memory_manager():
    """Mock MemoryManager to avoid actual initialization."""
    with patch("kagura.utils.memory.MemoryManager") as mock:
        # side_effect creates new MagicMock for each call
        mock.side_effect = lambda **kwargs: MagicMock()
        yield mock


class TestMemoryManagerFactory:
    """Tests for MemoryManagerFactory."""

    def test_get_or_create_mcp_context(self, mock_memory_manager):
        """Test creating MemoryManager with MCP context."""
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp"
        )

        assert memory is not None
        mock_memory_manager.assert_called_once()
        call_kwargs = mock_memory_manager.call_args.kwargs

        assert call_kwargs["user_id"] == "alice"
        assert call_kwargs["agent_name"] == "agent1"
        assert call_kwargs["enable_rag"] is True
        assert call_kwargs["enable_compression"] is True  # MCP default

    def test_get_or_create_api_context(self, mock_memory_manager):
        """Test creating MemoryManager with API context."""
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice", context="api"
        )

        assert memory is not None
        call_kwargs = mock_memory_manager.call_args.kwargs

        assert call_kwargs["user_id"] == "alice"
        assert call_kwargs["agent_name"] == "api"  # Default for API
        assert call_kwargs["enable_compression"] is False  # API disables
        assert "persist_dir" in call_kwargs  # API sets custom persist_dir

    def test_get_or_create_cli_context(self, mock_memory_manager):
        """Test creating MemoryManager with CLI context."""
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice", context="cli", cache=False
        )

        assert memory is not None
        call_kwargs = mock_memory_manager.call_args.kwargs

        assert call_kwargs["user_id"] == "alice"
        assert call_kwargs["agent_name"] == "cli"
        assert call_kwargs["enable_compression"] is True  # CLI enables

    def test_caching_enabled(self, mock_memory_manager):
        """Test that caching works when enabled."""
        mem1 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", cache=True
        )
        mem2 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", cache=True
        )

        # Should be same instance (cached)
        assert mem1 is mem2
        # MemoryManager should only be called once
        assert mock_memory_manager.call_count == 1

    def test_caching_disabled(self, mock_memory_manager):
        """Test that caching can be disabled."""
        mem1 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", cache=False
        )
        mem2 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", cache=False
        )

        # Should be different instances (no caching)
        assert mem1 is not mem2
        # MemoryManager should be called twice
        assert mock_memory_manager.call_count == 2

    def test_different_users_separate_instances(self, mock_memory_manager):
        """Test that different users get separate instances."""
        mem_alice = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp"
        )
        mem_bob = MemoryManagerFactory.get_or_create(
            user_id="bob", agent_name="agent1", context="mcp"
        )

        assert mem_alice is not mem_bob
        assert mock_memory_manager.call_count == 2

    def test_different_agents_separate_instances(self, mock_memory_manager):
        """Test that different agents get separate instances."""
        mem1 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp"
        )
        mem2 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent2", context="mcp"
        )

        assert mem1 is not mem2
        assert mock_memory_manager.call_count == 2

    def test_different_rag_setting_separate_instances(self, mock_memory_manager):
        """Test that different RAG settings get separate instances."""
        mem1 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", enable_rag=True
        )
        mem2 = MemoryManagerFactory.get_or_create(
            user_id="alice", agent_name="agent1", context="mcp", enable_rag=False
        )

        assert mem1 is not mem2
        assert mock_memory_manager.call_count == 2

    def test_custom_parameters(self, mock_memory_manager):
        """Test that custom parameters are passed through."""
        MemoryManagerFactory.get_or_create(
            user_id="alice",
            agent_name="agent1",
            context="mcp",
            enable_rag=False,
            enable_compression=False,
            max_messages=50,
        )

        call_kwargs = mock_memory_manager.call_args.kwargs
        assert call_kwargs["enable_rag"] is False
        assert call_kwargs["enable_compression"] is False
        assert call_kwargs["max_messages"] == 50

    def test_agent_name_defaults_to_context(self, mock_memory_manager):
        """Test that agent_name defaults to context when not provided."""
        MemoryManagerFactory.get_or_create(user_id="alice", context="mcp")
        call_kwargs = mock_memory_manager.call_args.kwargs
        assert call_kwargs["agent_name"] == "mcp"

        MemoryManagerFactory.clear_cache()

        MemoryManagerFactory.get_or_create(user_id="alice", context="api")
        call_kwargs = mock_memory_manager.call_args.kwargs
        assert call_kwargs["agent_name"] == "api"

    def test_creation_failure_raises(self, mock_memory_manager):
        """Test that MemoryManager creation failures are propagated."""
        mock_memory_manager.side_effect = RuntimeError("Initialization failed")

        with pytest.raises(RuntimeError, match="Initialization failed"):
            MemoryManagerFactory.get_or_create(user_id="alice", context="mcp")


class TestClearCache:
    """Tests for cache clearing functionality."""

    def test_clear_all_cache(self, mock_memory_manager):
        """Test clearing all cached instances."""
        # Create multiple instances
        MemoryManagerFactory.get_or_create(user_id="alice", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="bob", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="charlie", context="api")

        # Clear all
        count = MemoryManagerFactory.clear_cache()
        assert count == 3

        # Cache should be empty
        stats = MemoryManagerFactory.get_cache_stats()
        assert stats["total"] == 0

    def test_clear_cache_by_user(self, mock_memory_manager):
        """Test clearing cache for specific user."""
        # Create instances for multiple users
        MemoryManagerFactory.get_or_create(user_id="alice", agent_name="agent1", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="alice", agent_name="agent2", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="bob", context="mcp")

        # Clear only alice's cache
        count = MemoryManagerFactory.clear_cache(user_id="alice")
        assert count == 2

        # Bob's instance should still be cached
        stats = MemoryManagerFactory.get_cache_stats()
        assert stats["total"] == 1

    def test_clear_empty_cache(self):
        """Test clearing empty cache returns 0."""
        count = MemoryManagerFactory.clear_cache()
        assert count == 0


class TestGetCacheStats:
    """Tests for cache statistics."""

    def test_get_stats_empty_cache(self):
        """Test getting stats from empty cache."""
        stats = MemoryManagerFactory.get_cache_stats()

        assert stats["total"] == 0
        assert stats["by_context"] == {"cli": 0, "mcp": 0, "api": 0}

    def test_get_stats_with_entries(self, mock_memory_manager):
        """Test getting stats with cached entries."""
        # Create instances in different contexts
        MemoryManagerFactory.get_or_create(user_id="alice", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="bob", context="mcp")
        MemoryManagerFactory.get_or_create(user_id="charlie", context="api")

        stats = MemoryManagerFactory.get_cache_stats()

        assert stats["total"] == 3
        assert stats["by_context"]["mcp"] == 2
        assert stats["by_context"]["api"] == 1
        assert stats["by_context"]["cli"] == 0


class TestMakeCacheKey:
    """Tests for cache key generation."""

    def test_make_cache_key_format(self):
        """Test cache key format."""
        key = MemoryManagerFactory._make_cache_key(
            user_id="alice",
            agent_name="agent1",
            enable_rag=True,
            context="mcp"
        )

        assert key == "alice:agent1:rag=True:ctx=mcp"

    def test_make_cache_key_different_params(self):
        """Test that different parameters produce different keys."""
        key1 = MemoryManagerFactory._make_cache_key(
            "alice", "agent1", True, "mcp"
        )
        key2 = MemoryManagerFactory._make_cache_key(
            "alice", "agent1", False, "mcp"
        )
        key3 = MemoryManagerFactory._make_cache_key(
            "alice", "agent2", True, "mcp"
        )
        key4 = MemoryManagerFactory._make_cache_key(
            "bob", "agent1", True, "mcp"
        )

        # All keys should be unique
        keys = {key1, key2, key3, key4}
        assert len(keys) == 4


class TestGetMemoryManagerConvenience:
    """Tests for get_memory_manager() convenience function."""

    def test_get_memory_manager_defaults(self, mock_memory_manager):
        """Test convenience function with default parameters."""
        memory = get_memory_manager("alice")

        assert memory is not None
        call_kwargs = mock_memory_manager.call_args.kwargs

        assert call_kwargs["user_id"] == "alice"
        assert call_kwargs["agent_name"] == "default"
        assert call_kwargs["enable_rag"] is True
        assert call_kwargs["enable_compression"] is True  # MCP context

    def test_get_memory_manager_custom_params(self, mock_memory_manager):
        """Test convenience function with custom parameters."""
        memory = get_memory_manager(
            user_id="alice",
            agent_name="custom_agent",
            enable_rag=False,
            cache=False
        )

        assert memory is not None
        call_kwargs = mock_memory_manager.call_args.kwargs

        assert call_kwargs["user_id"] == "alice"
        assert call_kwargs["agent_name"] == "custom_agent"
        assert call_kwargs["enable_rag"] is False

    def test_get_memory_manager_caching(self, mock_memory_manager):
        """Test that convenience function respects caching."""
        mem1 = get_memory_manager("alice", "agent1", cache=True)
        mem2 = get_memory_manager("alice", "agent1", cache=True)

        # Should be same instance (cached)
        assert mem1 is mem2
        assert mock_memory_manager.call_count == 1
