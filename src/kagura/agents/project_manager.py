"""ProjectManager Preset - Task tracking and planning agent."""

from pathlib import Path
from typing import Optional

from kagura.builder import AgentBuilder


class ProjectManagerPreset(AgentBuilder):
    """Preset configuration for project management agents.

    Features:
    - Persistent memory for project state
    - Task tracking and prioritization
    - Strategic planning capabilities
    - Professional, organized tone

    Example:
        >>> from kagura.agents import ProjectManagerPreset
        >>> pm = (
        ...     ProjectManagerPreset("pm", project="MyProject")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await pm("Create a sprint plan for next week")
    """

    def __init__(
        self, name: str, project: str = "Project", persist_dir: Optional[Path] = None
    ):
        """Initialize project manager preset.

        Args:
            name: Agent name
            project: Project name
            persist_dir: Directory for project state storage
        """
        super().__init__(name)

        # Configure for project management
        self.with_context(
            temperature=0.4,  # Strategic, consistent planning
            max_tokens=2000,  # Detailed plans
        )

        # Enable persistent memory for project state
        self.with_memory(
            type="persistent" if persist_dir else "context",
            max_messages=150,  # Long project history
            persist_dir=persist_dir,
        )

        # Note: Compression is enabled by default in @agent decorator
        self.project = project
