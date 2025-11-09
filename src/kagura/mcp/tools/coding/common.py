"""Common utilities for coding MCP tools.

Shared helpers and imports used across all coding tool modules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kagura.core.memory.coding_memory import CodingMemoryManager


def get_coding_memory(user_id: str, project_id: str) -> CodingMemoryManager:
    """Get CodingMemoryManager instance (no caching for session synchronization).

    Note: Cache removed in v4.0.9 to fix session synchronization issues.
    Each call creates a fresh instance that loads current session state
    from persistent storage.

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier

    Returns:
        New CodingMemoryManager instance with current session state
    """
    import logging

    logger = logging.getLogger(__name__)

    from kagura.core.memory.coding_memory import CodingMemoryManager

    logger.debug(
        f"get_coding_memory: Creating CodingMemoryManager for {user_id}:{project_id}"
    )

    # Always create new instance to ensure fresh session state
    return CodingMemoryManager(
        user_id=user_id,
        project_id=project_id,
        enable_rag=True,  # Always enable for semantic search
        enable_graph=True,  # Always enable for relationships
    )
