"""MemoryManager factory and caching utilities.

Centralized MemoryManager creation with context-aware configuration and caching.
Eliminates duplicate initialization patterns across CLI, MCP, and API layers.
"""

import logging
from pathlib import Path
from typing import Literal

from kagura.config.paths import get_data_dir
from kagura.core.memory import MemoryManager

logger = logging.getLogger(__name__)

# Global cache: cache_key -> MemoryManager
_memory_cache: dict[str, MemoryManager] = {}


class MemoryManagerFactory:
    """Centralized MemoryManager creation with caching and context-aware configuration.

    This factory eliminates duplicate MemoryManager initialization patterns
    by providing a single source of truth for:
    - Caching strategy (MCP vs CLI vs API)
    - Configuration defaults (enable_rag, enable_compression, persist_dir)
    - Cache key generation

    Usage:
        # MCP context (with caching)
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice",
            agent_name="agent1",
            context="mcp"
        )

        # API context (custom persist_dir, no compression)
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice",
            context="api"
        )

        # CLI context (no caching)
        memory = MemoryManagerFactory.get_or_create(
            user_id="alice",
            context="cli",
            cache=False
        )
    """

    @staticmethod
    def get_or_create(
        user_id: str,
        *,
        context: Literal["cli", "mcp", "api"] = "mcp",
        agent_name: str | None = None,
        enable_rag: bool = True,
        enable_compression: bool | None = None,
        persist_dir: Path | None = None,
        max_messages: int | None = None,
        cache: bool = True,
    ) -> MemoryManager:
        """Get or create MemoryManager with context-aware configuration.

        Args:
            user_id: User identifier
            context: Execution context (cli/mcp/api) for default configuration
            agent_name: Agent name (default: context name)
            enable_rag: Enable semantic search with RAG
            enable_compression: Enable context compression (default: context-dependent)
            persist_dir: Custom persist directory (default: context-dependent)
            max_messages: Maximum message history
            cache: Whether to cache the MemoryManager instance

        Returns:
            MemoryManager instance (cached or newly created)

        Context-specific defaults:
            - CLI: cache=False (new instance each time)
            - MCP: cache=True, enable_compression=True
            - API: cache=True, enable_compression=False, persist_dir=api/<user_id>

        Examples:
            >>> # MCP context with caching
            >>> mem1 = MemoryManagerFactory.get_or_create("alice", context="mcp")
            >>> mem2 = MemoryManagerFactory.get_or_create("alice", context="mcp")
            >>> mem1 is mem2  # Same instance (cached)
            True

            >>> # CLI context without caching
            >>> mem1 = MemoryManagerFactory.get_or_create("alice", context="cli")
            >>> mem2 = MemoryManagerFactory.get_or_create("alice", context="cli")
            >>> mem1 is mem2  # Different instances
            False

            >>> # API context with custom configuration
            >>> mem = MemoryManagerFactory.get_or_create(
            ...     "alice",
            ...     context="api",
            ...     enable_rag=True
            ... )
        """
        # Apply context-specific defaults
        if agent_name is None:
            agent_name = context

        if enable_compression is None:
            # API disables compression (stateless), others enable
            enable_compression = context != "api"

        if persist_dir is None and context == "api":
            # API uses dedicated per-user directory
            persist_dir = get_data_dir() / "api" / user_id
            persist_dir.mkdir(parents=True, exist_ok=True)

        # Generate cache key
        cache_key = MemoryManagerFactory._make_cache_key(
            user_id=user_id,
            agent_name=agent_name,
            enable_rag=enable_rag,
            context=context,
        )

        # Check cache if enabled
        if cache and cache_key in _memory_cache:
            logger.debug(f"MemoryManagerFactory: Using cached instance ({cache_key})")
            return _memory_cache[cache_key]

        # Create new instance
        logger.debug(f"MemoryManagerFactory: Creating new instance ({cache_key})")

        # Log first-time RAG initialization (download warning)
        if enable_rag and cache_key not in _memory_cache:
            logger.info(
                f"First-time RAG initialization for {agent_name}. "
                "Downloading embeddings model (~500MB, may take 30-60s)..."
            )

        # Build kwargs
        kwargs: dict = {
            "user_id": user_id,
            "agent_name": agent_name,
            "enable_rag": enable_rag,
            "enable_compression": enable_compression,
        }

        if persist_dir is not None:
            kwargs["persist_dir"] = persist_dir

        if max_messages is not None:
            kwargs["max_messages"] = max_messages

        # Create MemoryManager
        try:
            memory = MemoryManager(**kwargs)
        except Exception as e:
            logger.error(f"Failed to create MemoryManager: {e}")
            raise

        # Cache if enabled
        if cache:
            _memory_cache[cache_key] = memory

        return memory

    @staticmethod
    def _make_cache_key(
        user_id: str, agent_name: str, enable_rag: bool, context: str
    ) -> str:
        """Generate cache key for MemoryManager.

        Args:
            user_id: User identifier
            agent_name: Agent name
            enable_rag: Whether RAG is enabled
            context: Execution context

        Returns:
            Cache key string

        Examples:
            >>> MemoryManagerFactory._make_cache_key(
            ...     "alice", "agent1", True, "mcp"
            ... )
            'alice:agent1:rag=True:ctx=mcp'
        """
        return f"{user_id}:{agent_name}:rag={enable_rag}:ctx={context}"

    @staticmethod
    def clear_cache(user_id: str | None = None) -> int:
        """Clear cached MemoryManager instances.

        Args:
            user_id: Optional user ID filter. If None, clears all cached instances.

        Returns:
            Number of instances cleared from cache

        Examples:
            >>> MemoryManagerFactory.clear_cache(user_id="alice")
            3  # Cleared 3 cached instances for alice

            >>> MemoryManagerFactory.clear_cache()
            10  # Cleared all cached instances
        """
        global _memory_cache

        if user_id is None:
            # Clear all
            count = len(_memory_cache)
            _memory_cache.clear()
            logger.info(f"MemoryManagerFactory: Cleared all {count} cached instances")
            return count

        # Clear for specific user
        keys_to_delete = [
            key for key in _memory_cache.keys() if key.startswith(f"{user_id}:")
        ]
        for key in keys_to_delete:
            del _memory_cache[key]

        logger.info(
            f"MemoryManagerFactory: Cleared {len(keys_to_delete)} cached instances for user '{user_id}'"
        )
        return len(keys_to_delete)

    @staticmethod
    def get_cache_stats() -> dict[str, int | dict[str, int]]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            - total: Total cached instances
            - by_context: Count by context (cli/mcp/api)

        Examples:
            >>> MemoryManagerFactory.get_cache_stats()
            {
                'total': 5,
                'by_context': {'mcp': 3, 'api': 2, 'cli': 0}
            }
        """
        by_context: dict[str, int] = {"cli": 0, "mcp": 0, "api": 0}

        for key in _memory_cache.keys():
            # Extract context from cache key: "user:agent:rag=True:ctx=mcp"
            if ":ctx=" in key:
                ctx = key.split(":ctx=")[-1]
                if ctx in by_context:
                    by_context[ctx] += 1

        return {
            "total": len(_memory_cache),
            "by_context": by_context,
        }


def get_memory_manager(
    user_id: str,
    agent_name: str = "default",
    enable_rag: bool = True,
    cache: bool = True,
) -> MemoryManager:
    """Convenience function for getting MemoryManager (MCP context).

    This is a backward-compatible wrapper around MemoryManagerFactory.get_or_create()
    for MCP context (the most common use case).

    Args:
        user_id: User identifier
        agent_name: Agent name
        enable_rag: Enable semantic search
        cache: Whether to cache instance

    Returns:
        MemoryManager instance

    Examples:
        >>> memory = get_memory_manager("alice", "agent1")
    """
    return MemoryManagerFactory.get_or_create(
        user_id=user_id,
        agent_name=agent_name,
        enable_rag=enable_rag,
        context="mcp",
        cache=cache,
    )
