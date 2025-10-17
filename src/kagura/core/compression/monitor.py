"""Context window usage monitoring"""

from dataclasses import dataclass
from typing import Any, Optional

from .token_counter import TokenCounter


@dataclass
class ContextUsage:
    """Context usage statistics

    Attributes:
        prompt_tokens: Tokens in prompts
        completion_tokens: Reserved for completion
        total_tokens: Total tokens (prompt + completion)
        max_tokens: Maximum allowed tokens
        usage_ratio: Usage ratio (0.0 - 1.0)
        should_compress: Whether compression is recommended
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    max_tokens: int
    usage_ratio: float
    should_compress: bool


class ContextMonitor:
    """Monitor context window usage

    Tracks token usage and recommends compression when needed.

    Example:
        >>> counter = TokenCounter(model="gpt-5-mini")
        >>> monitor = ContextMonitor(counter, max_tokens=10000)
        >>> messages = [{"role": "user", "content": "Hello"}]
        >>> usage = monitor.check_usage(messages)
        >>> print(f"Usage: {usage.usage_ratio:.1%}")
    """

    def __init__(self, token_counter: TokenCounter, max_tokens: Optional[int] = None):
        """Initialize monitor

        Args:
            token_counter: TokenCounter instance
            max_tokens: Max context window (if None, auto-detect from model)
        """
        self.counter = token_counter
        self.max_tokens = max_tokens or self._get_max_tokens()

    def _get_max_tokens(self) -> int:
        """Get max tokens for current model

        Reserves space for completion tokens.

        Returns:
            Maximum tokens for prompts
        """
        limits = self.counter.get_model_limits(self.counter.model)
        # Reserve space for completion (e.g., 4000 tokens)
        # This ensures we never exceed the context window
        return limits["context_window"] - 4000

    def check_usage(
        self, messages: list[dict[str, Any]], system_prompt: str = ""
    ) -> ContextUsage:
        """Check current context usage

        Args:
            messages: Message history
            system_prompt: System prompt

        Returns:
            ContextUsage statistics

        Example:
            >>> monitor = ContextMonitor(TokenCounter())
            >>> messages = [{"role": "user", "content": "Test"}]
            >>> usage = monitor.check_usage(messages)
            >>> if usage.should_compress:
            ...     print("Time to compress!")
        """
        estimate = self.counter.estimate_context_size(
            messages,
            system_prompt,
            max_tokens=4000,  # Reserve for completion
        )

        usage_ratio = estimate["total_tokens"] / self.max_tokens
        should_compress = self.counter.should_compress(
            estimate["total_tokens"], self.max_tokens
        )

        return ContextUsage(
            prompt_tokens=estimate["prompt_tokens"],
            completion_tokens=estimate["completion_tokens"],
            total_tokens=estimate["total_tokens"],
            max_tokens=self.max_tokens,
            usage_ratio=usage_ratio,
            should_compress=should_compress,
        )
