"""FastAPI dependencies.

Dependency injection for MemoryManager and other shared resources.
"""

from pathlib import Path
from typing import Annotated

from fastapi import Depends

from kagura.core.memory import MemoryManager

# Global MemoryManager instance
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get or create MemoryManager instance.

    Returns:
        Shared MemoryManager instance
    """
    global _memory_manager

    if _memory_manager is None:
        # Initialize MemoryManager with default settings
        # TODO: Make this configurable via environment variables
        persist_dir = Path(".kagura/api")
        persist_dir.mkdir(parents=True, exist_ok=True)

        _memory_manager = MemoryManager(
            agent_name="api",
            persist_dir=persist_dir,
            max_messages=100,
            enable_rag=True,  # Enable semantic search
            enable_compression=False,  # Disable for API (stateless)
        )

    return _memory_manager


# Type alias for dependency injection
MemoryManagerDep = Annotated[MemoryManager, Depends(get_memory_manager)]
