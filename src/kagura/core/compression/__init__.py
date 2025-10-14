"""Context compression module

This module provides token counting and context window management
for efficient long-form conversations.

Example:
    >>> from kagura.core.compression import TokenCounter, ContextMonitor
    >>> counter = TokenCounter(model="gpt-4o-mini")
    >>> monitor = ContextMonitor(counter, max_tokens=10000)
    >>> usage = monitor.check_usage(messages)
    >>> if usage.should_compress:
    ...     print("Context is getting full!")
"""

from .exceptions import CompressionError, ModelNotSupportedError, TokenCountError
from .monitor import ContextMonitor, ContextUsage
from .token_counter import TokenCounter

__all__ = [
    "TokenCounter",
    "ContextMonitor",
    "ContextUsage",
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
]
