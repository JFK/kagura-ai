"""ContentWriter Preset - Content creation agent."""

from kagura.builder import AgentBuilder


class ContentWriterPreset(AgentBuilder):
    """Preset configuration for content writing agents.

    Features:
    - High temperature for creativity
    - Long-form content generation
    - Optional web research integration
    - Caching for repeated content types

    Example:
        >>> from kagura.agents import ContentWriterPreset
        >>> writer = (
        ...     ContentWriterPreset("writer")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await writer("Write a blog post about AI trends")
    """

    def __init__(self, name: str, enable_web: bool = False):
        """Initialize content writer preset.

        Args:
            name: Agent name
            enable_web: Enable web research (default: False)
        """
        super().__init__(name)

        # Configure for creative writing
        self.with_context(
            temperature=0.8,  # High creativity
            max_tokens=3000,  # Long-form content
        )

        # Optional: Add web research capability
        # (Web tools would be added separately)
        self._enable_web = enable_web
