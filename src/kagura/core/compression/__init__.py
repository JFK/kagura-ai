"""Context compression module

This module provides token counting, context window management,
message trimming, and context summarization for efficient long-form conversations.

Example:
    >>> from kagura.core.compression import (
    ...     TokenCounter,
    ...     ContextMonitor,
    ...     MessageTrimmer,
    ...     ContextSummarizer,
    ... )
    >>> counter = TokenCounter(model="gpt-5-mini")
    >>> monitor = ContextMonitor(counter, max_tokens=10000)
    >>> usage = monitor.check_usage(messages)
    >>> if usage.should_compress:
    ...     # Option 1: Trim messages
    ...     trimmer = MessageTrimmer(counter)
    ...     trimmed = trimmer.trim(messages, max_tokens=4000, strategy="smart")
    ...     # Option 2: Summarize messages
    ...     summarizer = ContextSummarizer(counter)
    ...     summary = await summarizer.summarize_recursive(
    ...         messages, target_tokens=1000
    ...     )
"""

from .exceptions import CompressionError, ModelNotSupportedError, TokenCountError
from .manager import ContextManager
from .monitor import ContextMonitor, ContextUsage
from .policy import CompressionPolicy, CompressionStrategy
from .summarizer import ContextSummarizer
from .token_counter import TokenCounter
from .trimmer import MessageTrimmer, TrimStrategy

__all__ = [
    "TokenCounter",
    "ContextMonitor",
    "ContextUsage",
    "MessageTrimmer",
    "TrimStrategy",
    "ContextSummarizer",
    "CompressionPolicy",
    "CompressionStrategy",
    "ContextManager",
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
]
