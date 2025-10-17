"""Compression policy configuration"""

from dataclasses import dataclass
from typing import Literal

CompressionStrategy = Literal["auto", "trim", "summarize", "smart", "off"]


@dataclass
class CompressionPolicy:
    """Context compression configuration

    Defines how and when to compress conversation history.

    Example:
        >>> policy = CompressionPolicy(
        ...     strategy="smart",
        ...     max_tokens=4000,
        ...     trigger_threshold=0.8
        ... )
    """

    strategy: CompressionStrategy = "smart"
    """Compression strategy:
    - auto: Automatically choose best strategy
    - trim: Simple message trimming (fast, no LLM)
    - summarize: Summarize old messages (LLM-based)
    - smart: Preserve events + summarize routine (best quality)
    - off: No compression
    """

    max_tokens: int = 4000
    """Maximum context tokens (excluding completion tokens)"""

    trigger_threshold: float = 0.8
    """Trigger compression at this ratio (0.0 - 1.0)

    Example: 0.8 = compress when reaching 80% of max_tokens
    """

    preserve_recent: int = 5
    """Always preserve this many recent messages"""

    preserve_system: bool = True
    """Always preserve system message"""

    target_ratio: float = 0.5
    """After compression, aim for this ratio (0.0 - 1.0)

    Example: 0.5 = reduce to 50% of max_tokens after compression
    """

    enable_summarization: bool = True
    """Allow LLM-based summarization (required for 'summarize' and 'smart')"""

    summarization_model: str = "gpt-5-mini"
    """Model for summarization (should be fast and cheap)"""

    def __post_init__(self):
        """Validate configuration"""
        if not 0.0 <= self.trigger_threshold <= 1.0:
            raise ValueError(
                f"trigger_threshold must be between 0.0 and 1.0, "
                f"got {self.trigger_threshold}"
            )

        if not 0.0 <= self.target_ratio <= 1.0:
            raise ValueError(
                f"target_ratio must be between 0.0 and 1.0, got {self.target_ratio}"
            )

        if self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")

        if self.preserve_recent < 0:
            raise ValueError(
                f"preserve_recent must be non-negative, got {self.preserve_recent}"
            )

        # Check if summarization is required but disabled
        if self.strategy in ["summarize", "smart"] and not self.enable_summarization:
            raise ValueError(
                f"strategy '{self.strategy}' requires enable_summarization=True"
            )
