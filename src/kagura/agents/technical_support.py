"""TechnicalSupport Preset - Customer support with routing and knowledge base."""

from pathlib import Path
from typing import Optional

from kagura.builder import AgentBuilder


class TechnicalSupportPreset(AgentBuilder):
    """Preset configuration for technical support agents.

    Features:
    - RAG for knowledge base integration
    - Routing for multi-topic support
    - Memory for customer context
    - Professional, helpful tone

    Example:
        >>> from kagura.agents import TechnicalSupportPreset
        >>> support = (
        ...     TechnicalSupportPreset("support", kb_dir=Path("./kb"))
        ...     .with_model("gpt-5-mini")
        ...     .build()
        ... )
        >>> result = await support("How do I reset my password?")
    """

    def __init__(
        self, name: str, kb_dir: Optional[Path] = None, enable_routing: bool = True
    ):
        """Initialize technical support preset.

        Args:
            name: Agent name
            kb_dir: Knowledge base directory for RAG (optional)
            enable_routing: Enable multi-agent routing (default: True)
        """
        super().__init__(name)

        # Configure for support
        self.with_context(
            temperature=0.5,  # Balanced: accurate + friendly
            max_tokens=1000,
        )

        # Enable memory for customer context
        self.with_memory(
            type="context",
            max_messages=50,
        )

        # Optional: RAG for knowledge base
        if kb_dir:
            self.with_memory(
                type="context",
                enable_rag=True,
                persist_dir=kb_dir,
            )

        self._enable_routing = enable_routing
