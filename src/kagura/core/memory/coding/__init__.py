"""Coding memory module - modular implementation.

This module provides coding-specialized memory management for AI coding assistants.

Phase 3.1 (PR #618-1): Foundation - Moved entire implementation into this subpackage
Phase 3.2 (PR #618-2): Isolated Features - Extracted file tracking, error recording, decision recording

Main class: CodingMemoryManager (extends MemoryManager)
Public API: All methods and models re-exported from submodules

Backward Compatibility:
    Both import paths work:
    >>> from kagura.core.memory.coding_memory import CodingMemoryManager
    >>> from kagura.core.memory.coding import CodingMemoryManager
"""

# Phase 3.1 (PR #618-1): Foundation
from kagura.core.memory.coding.manager import CodingMemoryManager, UserCancelledError

# Phase 3.2 (PR #618-2): Isolated Features - Apply mixin pattern
from kagura.core.memory.coding import decision_recorder, error_recorder, file_tracker

# Phase 3.3 (PR #618-3): Analyzers - Apply mixin pattern
from kagura.core.memory.coding import analyzers

# Phase 3.4 (PR #618-4): Session Management - Apply mixin pattern
from kagura.core.memory.coding import session_manager

# Phase 3.5 (PR #618-5): GitHub Integration - Apply mixin pattern
from kagura.core.memory.coding import github_integration

# Attach methods from extracted modules as mixins
for module in [
    file_tracker,
    error_recorder,
    decision_recorder,
    analyzers,
    session_manager,
    github_integration,
]:
    for name in dir(module):
        # Skip module-level imports but allow private methods like _detect_active_session
        if name.startswith("__"):
            continue
        if callable(getattr(module, name)):
            attr = getattr(module, name)
            # Only attach if it's a function (not imported classes/constants)
            if hasattr(attr, "__call__") and not isinstance(attr, type):
                setattr(CodingMemoryManager, name, attr)

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
