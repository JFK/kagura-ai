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

    if cache_key not in _memory_cache:
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
    else:
        logger.debug("get_memory_manager: Using cached MemoryManager")

    return _memory_cache[cache_key]


# Backward compatibility alias for tests and legacy code
_get_memory_manager = get_memory_manager
