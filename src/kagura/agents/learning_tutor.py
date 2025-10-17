"""LearningTutor Preset - Adaptive teaching agent with memory."""

from pathlib import Path
from typing import Optional

from kagura.builder import AgentBuilder


class LearningTutorPreset(AgentBuilder):
    """Preset configuration for adaptive learning tutors.

    Features:
    - Persistent memory for student progress tracking
    - Adaptive teaching based on history
    - Patient, encouraging tone
    - Step-by-step explanations

    Example:
        >>> from kagura.agents import LearningTutorPreset
        >>> tutor = (
        ...     LearningTutorPreset("math_tutor", subject="Mathematics")
        ...     .with_model("gpt-4o")
        ...     .build()
        ... )
        >>> result = await tutor("Explain quadratic equations")
    """

    def __init__(
        self, name: str, subject: str = "General", persist_dir: Optional[Path] = None
    ):
        """Initialize learning tutor preset.

        Args:
            name: Agent name
            subject: Subject area (e.g., "Mathematics", "Programming")
            persist_dir: Directory for student progress storage
        """
        super().__init__(name)

        # Configure for teaching
        self.with_context(
            temperature=0.6,  # Consistent but not rigid
            max_tokens=2000,  # Detailed explanations
        )

        # Enable persistent memory for student progress
        self.with_memory(
            type="persistent" if persist_dir else "context",
            max_messages=100,
            persist_dir=persist_dir,
        )

        self.subject = subject
