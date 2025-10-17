"""Research Preset - Analysis and research agent with RAG."""

from pathlib import Path
from typing import Optional

from kagura.builder import AgentBuilder


class ResearchPreset(AgentBuilder):
    """Preset configuration for research and analysis tasks.

    Features:
    - RAG memory for semantic search
    - Lower temperature for factual responses
    - Longer context for detailed analysis

    Example:
        >>> from kagura.agents import ResearchPreset
        >>> researcher = (
        ...     ResearchPreset("researcher")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await researcher("Analyze trends in AI")
    """

    def __init__(self, name: str, persist_dir: Optional[Path] = None):
        """Initialize research preset.

        Args:
            name: Agent name
            persist_dir: Optional directory for persistent storage
        """
        super().__init__(name)

        # Configure for research/analysis
        self.with_memory(
            type="rag",
            enable_rag=True,  # Semantic search for relevant information
            persist_dir=persist_dir,
            max_messages=200,  # Larger context for analysis
        ).with_context(
            temperature=0.3,  # Factual, consistent responses
            max_tokens=2000,  # Detailed analysis
        )
