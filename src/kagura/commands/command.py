"""Command definition for Kagura AI custom commands.

Represents a custom command loaded from a Markdown file with frontmatter.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Command:
    """Represents a custom command.

    A command is defined in a Markdown file with YAML frontmatter containing
    metadata, and a Markdown body containing the command template.

    Attributes:
        name: Command name (used to invoke the command)
        description: Human-readable description
        template: Markdown template body
        allowed_tools: List of allowed tool names (empty = all allowed)
        model: LLM model to use (default: gpt-4o-mini)
        parameters: Command parameter definitions
        metadata: Additional metadata from frontmatter
    """

    name: str
    description: str
    template: str
    allowed_tools: list[str] = field(default_factory=list)
    model: str = "gpt-5-mini"
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate command after initialization."""
        if not self.name:
            raise ValueError("Command name cannot be empty")
        if not self.template:
            raise ValueError("Command template cannot be empty")

    def validate_parameters(self, provided: dict[str, Any]) -> None:
        """Validate provided parameters against parameter definitions.

        Args:
            provided: Parameters provided by user

        Raises:
            ValueError: If required parameters are missing
        """
        # Check for required parameters
        for param_name, param_def in self.parameters.items():
            if isinstance(param_def, dict):
                # Parameter with type definition
                required = param_def.get("required", False)
                if required and param_name not in provided:
                    raise ValueError(f"Required parameter missing: {param_name}")
            elif isinstance(param_def, str):
                # Simple type string (e.g., "string", "int")
                if param_name not in provided:
                    raise ValueError(f"Required parameter missing: {param_name}")

    def __repr__(self) -> str:
        """String representation."""
        tools_str = f", tools={len(self.allowed_tools)}" if self.allowed_tools else ""
        params_str = f", params={len(self.parameters)}" if self.parameters else ""
        return f"Command(name={self.name!r}{tools_str}{params_str})"
