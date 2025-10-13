"""Natural language spec parser

Parse natural language agent descriptions into structured AgentSpec using LLM.
"""

from kagura.core.llm import LLMConfig, call_llm
from kagura.core.parser import parse_response

from .spec import AgentSpec


class NLSpecParser:
    """Parse natural language agent descriptions into AgentSpec

    Uses existing Kagura LLM infrastructure (call_llm + parse_response)
    to extract structured information from user descriptions.

    Example:
        >>> parser = NLSpecParser()
        >>> desc = "Create an agent that translates English to Japanese"
        >>> spec = await parser.parse(desc)
        >>> print(spec.name)  # "translator"
        >>> print(spec.system_prompt)  # Generated system prompt
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize parser with LLM model

        Args:
            model: LLM model to use for parsing (default: gpt-4o-mini)
        """
        self.config = LLMConfig(model=model, temperature=0.3)

    async def parse(self, description: str) -> AgentSpec:
        """Parse natural language description into AgentSpec

        Args:
            description: Natural language agent description

        Returns:
            Structured AgentSpec

        Example:
            >>> spec = await parser.parse("Summarize articles in 3 bullet points")
            >>> assert spec.name == "article_summarizer"
            >>> assert spec.output_type == "str"
        """
        prompt = self._build_prompt(description)

        # Use existing call_llm + parse_response
        response = await call_llm(prompt, self.config)
        spec = parse_response(response, AgentSpec)

        return spec

    def _build_prompt(self, description: str) -> str:
        """Build parsing prompt

        Args:
            description: User's natural language description

        Returns:
            Prompt for LLM
        """
        return f"""Extract structured agent specification from this description:

{description}

Return JSON with these fields:
- name: snake_case function name (e.g., "translator", "article_summarizer")
- description: What the agent does (1-2 sentences)
- input_type: Parameter type (str, dict, list, etc.)
- output_type: Return type (str, dict, list, etc.)
- tools: Required tools (code_executor, web_search, memory, file_ops, etc.)
- has_memory: Whether agent needs conversation memory (true/false)
- system_prompt: Agent's system instructions (detailed, professional)
- examples: Example inputs/outputs (if any mentioned)

Guidelines:
- Use descriptive, clear names
- System prompt should be professional and specific
- Only include tools if explicitly needed
- has_memory=true only if conversation context is needed
"""

    def detect_tools(self, description: str) -> list[str]:
        """Detect required tools from description using pattern matching

        Args:
            description: Natural language description

        Returns:
            List of detected tool names

        Example:
            >>> desc = "Execute Python code to solve math problems"
            >>> tools = parser.detect_tools(desc)
            >>> assert "code_executor" in tools
        """
        TOOL_PATTERNS = {
            "code_executor": [
                "execute code",
                "run python",
                "code execution",
                "calculate",
            ],
            "web_search": ["search web", "google", "find online", "look up"],
            "memory": ["remember", "recall", "memory", "history", "conversation"],
            "file_ops": ["read file", "write file", "file operations", "save to file"],
        }

        detected = []
        desc_lower = description.lower()

        for tool, patterns in TOOL_PATTERNS.items():
            if any(pattern in desc_lower for pattern in patterns):
                detected.append(tool)

        return detected
