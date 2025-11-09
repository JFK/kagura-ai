"""Coding memory module - modular implementation.

This module provides coding-specialized memory management for AI coding assistants.
In Phase 3 (PR #618-1), we've established the foundation by moving the entire
implementation into this subpackage. Future PRs will split manager.py into
focused modules (session, file tracking, error recording, etc.).

Main class: CodingMemoryManager (extends MemoryManager)
Public API: All methods and models re-exported from submodules

Backward Compatibility:
    Both import paths work:
    >>> from kagura.core.memory.coding_memory import CodingMemoryManager
    >>> from kagura.core.memory.coding import CodingMemoryManager
"""

# Phase 3.1 (PR #618-1): Foundation
# Currently all implementation is in manager.py
# Future PRs will extract to specialized modules

from kagura.core.memory.coding.manager import CodingMemoryManager, UserCancelledError

# Re-export models for convenience (they're already in models/coding.py)
from kagura.core.memory.models.coding import (
    CodingPattern,
    CodingSession,
    DesignDecision,
    ErrorRecord,
    FileChangeRecord,
    ProjectContext,
)

__all__ = [
    # Main class
    "CodingMemoryManager",
    # Exception
    "UserCancelledError",
    # Models
    "CodingSession",
    "FileChangeRecord",
    "ErrorRecord",
    "DesignDecision",
    "ProjectContext",
    "CodingPattern",
]
