"""Context compression manager - unified interface"""

from typing import Any, Optional

from kagura.core.llm import LLMConfig

from .monitor import ContextMonitor, ContextUsage
from .policy import CompressionPolicy
from .summarizer import ContextSummarizer
from .token_counter import TokenCounter
from .trimmer import MessageTrimmer


class ContextManager:
    """Unified context compression manager

    Integrates all compression strategies (trim, summarize, smart, auto).

    Example:
        >>> from kagura.core.compression import ContextManager, CompressionPolicy
        >>> manager = ContextManager(
        ...     policy=CompressionPolicy(strategy="smart"),
        ...     model="gpt-5-mini"
        ... )
        >>> compressed = await manager.compress(messages)
    """

    def __init__(
        self, policy: Optional[CompressionPolicy] = None, model: str = "gpt-5-mini"
    ):
        """Initialize context manager

        Args:
            policy: Compression policy (default: CompressionPolicy())
            model: LLM model name for token counting and summarization
        """
        self.policy = policy or CompressionPolicy()
        self.counter = TokenCounter(model=model)
        self.monitor = ContextMonitor(self.counter, max_tokens=self.policy.max_tokens)
        self.trimmer = MessageTrimmer(self.counter)

        # Initialize summarizer if enabled
        if self.policy.enable_summarization:
            self.summarizer: Optional[ContextSummarizer] = ContextSummarizer(
                self.counter,
                llm_config=LLMConfig(
                    model=self.policy.summarization_model, temperature=0.3
                ),
            )
        else:
            self.summarizer = None

    async def compress(
        self, messages: list[dict[str, Any]], system_prompt: str = ""
    ) -> list[dict[str, Any]]:
        """Compress messages if needed

        Args:
            messages: Message history
            system_prompt: System prompt (if any)

        Returns:
            Compressed messages (or original if no compression needed)

        Example:
            >>> compressed = await manager.compress(messages)
            >>> assert len(compressed) <= len(messages)
        """
        # Check if compression needed
        usage = self.monitor.check_usage(messages, system_prompt)

        if not usage.should_compress:
            # No compression needed
            return messages

        if self.policy.strategy == "off":
            # Compression disabled
            return messages

        # Calculate target tokens
        target_tokens = int(self.policy.max_tokens * self.policy.target_ratio)

        # Apply compression strategy
        if self.policy.strategy == "trim":
            return self._compress_trim(messages, target_tokens)
        elif self.policy.strategy == "summarize":
            return await self._compress_summarize(messages, target_tokens)
        elif self.policy.strategy == "smart":
            return await self._compress_smart(messages, target_tokens)
        elif self.policy.strategy == "auto":
            return await self._compress_auto(messages, target_tokens)
        else:
            # Default to trim
            return self._compress_trim(messages, target_tokens)

    def _compress_trim(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Trim-based compression (fast, no LLM)"""
        return self.trimmer.trim(
            messages,
            target_tokens,
            strategy="smart",
            preserve_system=self.policy.preserve_system,
        )

    async def _compress_summarize(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Summarization-based compression"""
        if not self.summarizer:
            # Fallback to trim
            return self._compress_trim(messages, target_tokens)

        # Preserve recent messages
        recent = messages[-self.policy.preserve_recent :] if messages else []
        to_summarize = (
            messages[: -self.policy.preserve_recent]
            if len(messages) > self.policy.preserve_recent
            else []
        )

        if not to_summarize:
            return messages

        # Calculate token budget
        recent_tokens = self.counter.count_tokens_messages(recent)
        summary_budget = target_tokens - recent_tokens

        if summary_budget < 100:
            # Not enough space, just trim
            return self._compress_trim(messages, target_tokens)

        # Summarize old messages
        summary = await self.summarizer.summarize_recursive(
            to_summarize, summary_budget
        )

        # Reconstruct
        summary_msg = {
            "role": "system",
            "content": f"[Previous conversation summary] {summary}",
        }

        return [summary_msg] + recent

    async def _compress_smart(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Smart compression: preserve events + summarize"""
        if not self.summarizer:
            return self._compress_trim(messages, target_tokens)

        return await self.summarizer.compress_preserve_events(messages, target_tokens)

    async def _compress_auto(
        self, messages: list[dict[str, Any]], target_tokens: int
    ) -> list[dict[str, Any]]:
        """Automatically choose best strategy"""
        # Heuristic: if many messages, use smart; if few, use trim
        if len(messages) > 20:
            return await self._compress_smart(messages, target_tokens)
        else:
            return self._compress_trim(messages, target_tokens)

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
