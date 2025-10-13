"""Agent specification models"""

from pydantic import BaseModel, Field


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
    system_prompt: str = Field(..., description="Agent system prompt")
    examples: list[dict[str, str]] = Field(
        default_factory=list, description="Example inputs/outputs"
    )

    class Config:
        """Pydantic configuration"""

        json_schema_extra = {
            "example": {
                "name": "translator",
                "description": "Translate English to Japanese",
                "input_type": "str",
                "output_type": "str",
                "tools": [],
                "has_memory": False,
                "system_prompt": (
                    "You are a professional translator. "
                    "Translate the given text from English to Japanese."
                ),
                "examples": [
                    {"input": "Hello world", "output": "こんにちは世界"}
                ],
            }
        }
