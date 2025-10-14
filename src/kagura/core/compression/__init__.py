"""Context compression module

This module provides token counting, context window management,
and message trimming for efficient long-form conversations.

Example:
    >>> from kagura.core.compression import TokenCounter, ContextMonitor, MessageTrimmer
    >>> counter = TokenCounter(model="gpt-4o-mini")
    >>> monitor = ContextMonitor(counter, max_tokens=10000)
    >>> usage = monitor.check_usage(messages)
    >>> if usage.should_compress:
    ...     trimmer = MessageTrimmer(counter)
    ...     trimmed = trimmer.trim(messages, max_tokens=4000, strategy="smart")
"""

from .exceptions import CompressionError, ModelNotSupportedError, TokenCountError
from .monitor import ContextMonitor, ContextUsage
from .token_counter import TokenCounter
from .trimmer import MessageTrimmer, TrimStrategy

__all__ = [
    "TokenCounter",
    "ContextMonitor",
    "ContextUsage",
    "MessageTrimmer",
    "TrimStrategy",
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
]
