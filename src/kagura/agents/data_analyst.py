"""DataAnalyst Preset - Data analysis with code execution."""

from kagura.builder import AgentBuilder


class DataAnalystPreset(AgentBuilder):
    """Preset configuration for data analysis agents.

    Features:
    - Code execution enabled for data processing
    - Higher temperature for creative insights
    - Memory for tracking analysis context
    - Optimized for data-heavy tasks

    Example:
        >>> from kagura.agents import DataAnalystPreset
        >>> analyst = (
        ...     DataAnalystPreset("analyst")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await analyst("Analyze this CSV and find trends")
    """

    def __init__(self, name: str, enable_memory: bool = True):
        """Initialize data analyst preset.

        Args:
            name: Agent name
            enable_memory: Enable memory for analysis context (default: True)
        """
        super().__init__(name)

        # Configure for data analysis
        self.with_context(
            temperature=0.5,  # Balanced: accurate + creative
            max_tokens=2000,  # Longer responses for analysis
        )

        # Enable memory for tracking analysis
        if enable_memory:
            self.with_memory(
                type="context",
                max_messages=50,
            )

        # Note: Code execution tools would be added separately
        # This preset focuses on LLM-based analysis
