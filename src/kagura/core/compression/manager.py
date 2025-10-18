"""Context compression manager - simplified for personal use

Note: In v3.0, this module provides basic compression framework.
      Advanced features (trimming strategies, summarization) removed
      as personal assistant conversations are typically short.

      If needed in future, can be re-implemented or users can
      implement custom compression logic.
"""

from typing import Any, Optional

from .monitor import ContextMonitor, ContextUsage
from .policy import CompressionPolicy
from .token_counter import TokenCounter


class ContextManager:
    """Simplified context compression manager for personal use

    Provides token monitoring and basic compression framework.

    In v3.0, advanced compression (trimming, summarization) removed.
    Personal assistant conversations are typically short, so
    basic monitoring is sufficient.

    Example:
        >>> from kagura.core.compression import ContextManager, CompressionPolicy
        >>> manager = ContextManager(
        ...     policy=CompressionPolicy(strategy="off"),
        ...     model="gpt-5-mini"
        ... )
        >>> usage = manager.get_usage(messages)
        >>> if usage.should_compress:
        ...     # Implement custom compression logic
        ...     pass
    """

    def __init__(
        self, policy: Optional[CompressionPolicy] = None, model: str = "gpt-5-mini"
    ):
        """Initialize context manager

        Args:
            policy: Compression policy (default: strategy="off")
            model: LLM model name for token counting
        """
        self.policy = policy or CompressionPolicy(strategy="off")
        self.counter = TokenCounter(model=model)
        self.monitor = ContextMonitor(self.counter, max_tokens=self.policy.max_tokens)

    async def compress(
        self, messages: list[dict[str, Any]], system_prompt: str = ""
    ) -> list[dict[str, Any]]:
        """Compress messages if needed

        Note: In v3.0, this is a no-op (returns original messages).
              Advanced compression removed as personal conversations are short.

              Users can implement custom compression logic if needed:
              1. Check usage via get_usage()
              2. Implement custom compression strategy
              3. Return compressed messages

        Args:
            messages: Message history
            system_prompt: System prompt (if any)

        Returns:
            Original messages (no compression in v3.0)

        Example:
            >>> compressed = await manager.compress(messages)
            >>> # In v3.0, compressed == messages (no-op)
        """
        # Check if compression needed
        usage = self.monitor.check_usage(messages, system_prompt)

        if not usage.should_compress or self.policy.strategy == "off":
            # No compression needed or disabled
            return messages

        # In v3.0: No advanced compression strategies
        # Return original messages
        # Users can implement custom logic by subclassing ContextManager
        return messages

    def get_usage(
        self, messages: list[dict[str, Any]], system_prompt: str = ""
    ) -> ContextUsage:
        """Get current context usage

        Args:
            messages: Message history
            system_prompt: System prompt

        Returns:
            ContextUsage statistics

        Example:
            >>> usage = manager.get_usage(messages)
            >>> print(f"Usage: {usage.usage_ratio:.1%}")
        """
        return self.monitor.check_usage(messages, system_prompt)
