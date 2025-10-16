"""Agent specification models"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentSpec(BaseModel):
    """Structured agent specification extracted from natural language description

    This model represents all information needed to generate agent code.

    Attributes:
        name: Agent function name (snake_case)
        description: What the agent does (1-2 sentences)
        input_type: Input parameter type annotation
        output_type: Return type annotation
        tools: List of required tool names
        has_memory: Whether agent needs conversation memory
        requires_code_execution: Whether agent needs code execution (Phase 2)
        system_prompt: Agent's system instructions for LLM
        examples: Example input/output pairs

    Example:
        >>> spec = AgentSpec(
        ...     name="translator",
        ...     description="Translate English to Japanese",
        ...     input_type="str",
        ...     output_type="str",
        ...     system_prompt="You are a professional translator."
        ... )
    """

    name: str = Field(..., description="Agent name (snake_case)")
    description: str = Field(..., description="Agent purpose")
    input_type: str = Field(default="str", description="Input parameter type")
    output_type: str = Field(default="str", description="Output type")
    tools: list[str] = Field(default_factory=list, description="Required tools")
    has_memory: bool = Field(default=False, description="Needs memory context")
    requires_code_execution: bool = Field(
        default=False,
        description="Whether agent needs Python code execution capabilities",
    )
    system_prompt: str = Field(..., description="Agent system prompt")
    examples: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Example inputs/outputs (values can be any JSON-serializable type)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "translator",
                "description": "Translate English to Japanese",
                "input_type": "str",
                "output_type": "str",
                "tools": [],
                "has_memory": False,
                "requires_code_execution": False,
                "system_prompt": (
                    "You are a professional translator. "
                    "Translate the given text from English to Japanese."
                ),
                "examples": [
                    {"input": "Hello world", "output": "こんにちは世界"},
                    {"input": 5, "output": 10},
                    {"input": [1, 2], "output": {"sum": 3}},
                ],
            }
        }
    )
