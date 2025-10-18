"""Context compression module

This module provides token counting and context monitoring for personal use.

Implements RFC-024 Context Compression (Phase 1 & 4 only):
- Phase 1: Token Management (monitor and track) ✅
- Phase 4: Integration (unified API, compression policies) ✅

Note: Phase 2 (Trimming) and Phase 3 (Summarization) removed in v3.0.
      Personal assistant conversations are typically short, so advanced
      compression is not needed. Can be re-implemented if needed in future.

Example:
    >>> from kagura.core.compression import TokenCounter, ContextMonitor
    >>> counter = TokenCounter(model="gpt-5-mini")
    >>> monitor = ContextMonitor(counter, max_tokens=10000)
    >>> usage = monitor.check_usage(messages)
    >>> if usage.should_compress:
    ...     # Handle compression (custom implementation)
    ...     pass
"""

from .exceptions import CompressionError, ModelNotSupportedError, TokenCountError
from .manager import ContextManager
from .monitor import ContextMonitor, ContextUsage
from .policy import CompressionPolicy, CompressionStrategy
from .token_counter import TokenCounter

__all__ = [
    # Phase 1: Token Management
    "TokenCounter",
    "ContextMonitor",
    "ContextUsage",
    # Phase 4: Integration & Policy
    "CompressionPolicy",
    "CompressionStrategy",
    "ContextManager",
    # Exceptions
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
]
