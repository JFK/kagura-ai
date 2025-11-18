"""Common utilities for memory MCP tools.

Provides shared helper functions used across all memory tools.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kagura.core.memory import MemoryManager

# Global cache for MemoryManager instances (agent_name -> MemoryManager)
# Ensures working memory persists across MCP tool calls for the same agent
_memory_cache: dict[str, MemoryManager] = {}


def get_memory_manager(
    user_id: str, agent_name: str, enable_rag: bool = False
) -> MemoryManager:
    """Get or create cached MemoryManager instance

    Ensures the same MemoryManager instance is reused across MCP tool calls
    for the same user_id + agent_name combination, allowing working memory to persist.

    Args:
        user_id: User identifier (memory owner)
        agent_name: Name of the agent
        enable_rag: Whether to enable RAG (semantic search)

    Returns:
        Cached or new MemoryManager instance
    """
    logger = logging.getLogger(__name__)

    logger.debug("get_memory_manager: Importing MemoryManager...")
    from kagura.core.memory import MemoryManager

    logger.debug("get_memory_manager: MemoryManager imported successfully")

    cache_key = f"{user_id}:{agent_name}:rag={enable_rag}"
    logger.debug(f"get_memory_manager: cache_key={cache_key}")

    # Check if cached object exists and is valid
    if cache_key in _memory_cache:
        cached = _memory_cache[cache_key]

        # Validate required attributes (防止: stale cache from old code versions)
        required_attrs = ["persistent_rag", "rag", "graph", "persistent"]
        missing_attrs = [attr for attr in required_attrs if not hasattr(cached, attr)]

        if missing_attrs:
            logger.warning(
                f"Cached MemoryManager missing attributes {missing_attrs}, recreating. "
                "This can happen after code updates. Cache will be refreshed."
            )
            del _memory_cache[cache_key]
        else:
            logger.debug("get_memory_manager: Using cached MemoryManager")
            return cached

    # Create new MemoryManager
    logger.debug(f"get_memory_manager: Creating MemoryManager rag={enable_rag}")
    if enable_rag:
        logger.info(
            f"First-time RAG initialization for {agent_name}. "
            "Downloading embeddings model (~500MB, may take 30-60s)..."
        )
    _memory_cache[cache_key] = MemoryManager(
        user_id=user_id, agent_name=agent_name, enable_rag=enable_rag
    )
    logger.debug("get_memory_manager: MemoryManager created successfully")

    return _memory_cache[cache_key]


# Backward compatibility alias for tests and legacy code
_get_memory_manager = get_memory_manager
