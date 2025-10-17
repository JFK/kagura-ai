"""Code Review Preset - Code analysis and review agent."""

from kagura.builder import AgentBuilder


class CodeReviewPreset(AgentBuilder):
    """Preset configuration for code review and analysis tasks.

    Features:
    - Working memory for temporary code context
    - Very low temperature for precise, deterministic analysis
    - Optimized for technical accuracy

    Example:
        >>> from kagura.agents import CodeReviewPreset
        >>> reviewer = (
        ...     CodeReviewPreset("code_reviewer")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await reviewer("Review this Python function: ...")
    """

    def __init__(self, name: str):
        """Initialize code review preset.

        Args:
            name: Agent name
        """
        super().__init__(name)

        # Configure for code review
        self.with_memory(
            type="working",  # Temporary context for code snippets
            max_messages=50,
        ).with_context(
            temperature=0.1,  # Very precise, deterministic
            max_tokens=1500,  # Detailed code analysis
        )
