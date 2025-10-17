"""PersonalAssistant Preset - Memory-rich personal AI assistant."""

from pathlib import Path
from typing import Optional

from kagura.builder import AgentBuilder


class PersonalAssistantPreset(AgentBuilder):
    """Preset configuration for personal assistant agents.

    Features:
    - Persistent memory for long-term context
    - RAG for knowledge retrieval
    - Context compression for long conversations
    - Natural, friendly tone

    Example:
        >>> from kagura.agents import PersonalAssistantPreset
        >>> assistant = (
        ...     PersonalAssistantPreset("my_assistant")
        ...     .with_model("gpt-5-mini")
        ...     .build()
        ... )
        >>> result = await assistant("What did we discuss yesterday?")
    """

    def __init__(
        self, name: str, persist_dir: Optional[Path] = None, enable_rag: bool = True
    ):
        """Initialize personal assistant preset.

        Args:
            name: Agent name
            persist_dir: Directory for persistent storage
            enable_rag: Enable RAG for semantic memory (default: True)
        """
        super().__init__(name)

        # Configure for personal assistance
        self.with_context(
            temperature=0.7,  # Natural, friendly responses
            max_tokens=1500,
        )

        # Enable comprehensive memory
        self.with_memory(
            type="persistent" if persist_dir else "context",
            max_messages=200,  # Long conversation history
            enable_rag=enable_rag,
            persist_dir=persist_dir,
        )

        # Note: Compression is enabled by default in @agent decorator
        # Context compression happens automatically
