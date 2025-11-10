"""Backward compatibility facade for coding memory.

This module maintains import compatibility while the actual implementation
is in the coding/ subdirectory. This allows gradual refactoring without
breaking existing code.

DEPRECATED PATH (still works):
    from kagura.core.memory.coding_memory import CodingMemoryManager

PREFERRED PATH:
    from kagura.core.memory.coding import CodingMemoryManager

Both paths import the same implementation, so existing code continues to work.

Phase 3 Refactoring (v4.3.0):
    PR #618-1: Created coding/ module, established foundation
    Future PRs: Will split manager.py into focused modules
"""

# Re-export everything from the coding module
from kagura.core.memory.coding import (
    CodingMemoryManager,
    CodingPattern,
    CodingSession,
    DesignDecision,
    ErrorRecord,
    FileChangeRecord,
    ProjectContext,
    UserCancelledError,
)

__all__ = [
    "CodingMemoryManager",
    "UserCancelledError",
    "CodingSession",
    "FileChangeRecord",
    "ErrorRecord",
    "DesignDecision",
    "ProjectContext",
    "CodingPattern",
]
