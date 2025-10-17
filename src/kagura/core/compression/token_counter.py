"""Token counting for various LLM models"""

from typing import Any

import tiktoken

from .exceptions import TokenCountError


class TokenCounter:
    """Count tokens for various LLM models

    Uses tiktoken for accurate token counting across different models.

    Example:
        >>> counter = TokenCounter(model="gpt-5-mini")
        >>> tokens = counter.count_tokens("Hello, world!")
        >>> print(f"Tokens: {tokens}")
    """

    def __init__(self, model: str = "gpt-5-mini"):
        """Initialize with specific model tokenizer

        Args:
            model: LLM model name (e.g., "gpt-5-mini", "claude-3-5-sonnet")
        """
        self.model = model
        self._encoder = self._get_encoder(model)

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoder for model

        Args:
            model: Model name

        Returns:
            tiktoken.Encoding instance

        Raises:
            TokenCountError: If encoder cannot be loaded
        """
        try:
            # OpenAI models
            if "gpt" in model.lower():
                return tiktoken.encoding_for_model(model)
            # Claude models (use cl100k_base)
            elif "claude" in model.lower():
                return tiktoken.get_encoding("cl100k_base")
            # Gemini models (use cl100k_base approximation)
            elif "gemini" in model.lower():
                return tiktoken.get_encoding("cl100k_base")
            else:
                # Default to cl100k_base
                return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            # Fallback to cl100k_base
            try:
                return tiktoken.get_encoding("cl100k_base")
            except Exception:
                raise TokenCountError(
                    f"Failed to load encoder for model '{model}': {e}"
                )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text

        Args:
            text: Text to count

        Returns:
            Number of tokens

        Example:
            >>> counter = TokenCounter()
            >>> tokens = counter.count_tokens("Hello, world!")
            >>> assert tokens > 0
        """
        if not text:
            return 0

        try:
            return len(self._encoder.encode(text))
        except Exception as e:
            raise TokenCountError(f"Failed to count tokens: {e}")

    def count_tokens_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in message list (OpenAI format)

        Includes overhead for message formatting.

        Args:
            messages: List of messages with role/content

        Returns:
            Total token count including overhead

        Example:
            >>> counter = TokenCounter()
            >>> messages = [
            ...     {"role": "system", "content": "You are helpful."},
            ...     {"role": "user", "content": "Hello!"}
            ... ]
            >>> tokens = counter.count_tokens_messages(messages)
            >>> assert tokens > 10
        """
        # OpenAI message format overhead
        # Every message: 3 tokens for role/name/content delimiters
        # Every reply: 3 tokens (assistant priming)
        tokens = 3  # Reply priming

        for message in messages:
            tokens += 3  # Message overhead (role, name, content delimiters)
            tokens += self.count_tokens(message.get("role", ""))
            tokens += self.count_tokens(message.get("content", ""))

            # Name field adds 1 token, then removes 1 token for role adjustment
            if "name" in message:
                tokens += self.count_tokens(message["name"])
                tokens -= 1  # Name adjustment

        return tokens

    def estimate_context_size(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        max_tokens: int = 1000,
    ) -> dict[str, int]:
        """Estimate total context window usage

        Args:
            messages: Conversation history
            system_prompt: System prompt
            max_tokens: Max completion tokens

        Returns:
            Dict with prompt_tokens, completion_tokens, total_tokens

        Example:
            >>> counter = TokenCounter()
            >>> estimate = counter.estimate_context_size(
            ...     [{"role": "user", "content": "Hello"}],
            ...     system_prompt="Be helpful.",
            ...     max_tokens=1000
            ... )
            >>> assert "prompt_tokens" in estimate
            >>> assert "total_tokens" in estimate
        """
        prompt_tokens = self.count_tokens(system_prompt)
        prompt_tokens += self.count_tokens_messages(messages)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": max_tokens,
            "total_tokens": prompt_tokens + max_tokens,
        }

    def should_compress(
        self, current_tokens: int, max_tokens: int, threshold: float = 0.8
    ) -> bool:
        """Decide if compression is needed

        Args:
            current_tokens: Current token count
            max_tokens: Maximum allowed tokens
            threshold: Trigger compression at this ratio (default: 0.8 = 80%)

        Returns:
            True if compression should be triggered

        Example:
            >>> counter = TokenCounter()
            >>> # Below threshold
            >>> assert not counter.should_compress(1000, 10000, threshold=0.8)
            >>> # Above threshold
            >>> assert counter.should_compress(9000, 10000, threshold=0.8)
        """
        if max_tokens <= 0:
            return False

        return current_tokens >= (max_tokens * threshold)

    def get_model_limits(self, model: str) -> dict[str, int]:
        """Get token limits for specific model

        Args:
            model: Model name

        Returns:
            Dict with context_window, max_completion_tokens

        Example:
            >>> counter = TokenCounter()
            >>> limits = counter.get_model_limits("gpt-5-mini")
            >>> assert limits["context_window"] > 0
            >>> assert limits["max_completion"] > 0
        """
        # Model limits (as of 2025)
        limits = {
            "gpt-5-mini": {"context_window": 128_000, "max_completion": 16_384},
            "gpt-4o": {"context_window": 128_000, "max_completion": 16_384},
            "gpt-4-turbo": {"context_window": 128_000, "max_completion": 4_096},
            "gpt-4-turbo-preview": {"context_window": 128_000, "max_completion": 4_096},
            "gpt-3.5-turbo": {"context_window": 16_385, "max_completion": 4_096},
            "claude-3-5-sonnet": {"context_window": 200_000, "max_completion": 8_192},
            "claude-3-opus": {"context_window": 200_000, "max_completion": 4_096},
            "claude-3-sonnet": {"context_window": 200_000, "max_completion": 4_096},
            "gemini-1.5-pro": {"context_window": 2_000_000, "max_completion": 8_192},
            "gemini-1.5-flash": {"context_window": 1_000_000, "max_completion": 8_192},
        }

        # Default for unknown models
        default = {"context_window": 8_000, "max_completion": 2_000}

        return limits.get(model, default)
