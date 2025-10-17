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

    def __init__(self, model: str = "gpt-5-mini"):
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
        spec = parse_response(str(response), AgentSpec)

        # Phase 2: Detect code execution need
        spec.requires_code_execution = await self.detect_code_execution_need(
            description
        )

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
- tools: List of required tools (e.g., ["web_search"])
  NOTE: Do NOT include "execute_code" here - it will be auto-added if needed
- has_memory: Whether agent needs conversation memory (true/false)
- requires_code_execution: Whether agent needs code execution (true/false)
  Set to true for: data processing, calculations, file operations
- system_prompt: Agent's system instructions (detailed, professional)
- examples: Array of objects with "input"/"output" keys, e.g.,
  [{{"input": "Hello", "output": "こんにちは"}}] or empty array []

Guidelines:
- Use descriptive, clear names
- System prompt should be professional and specific
- Only include tools if explicitly needed (empty array [] if none)
- has_memory=true only if conversation context is needed
- examples should be an array of objects, or empty array [] if none
- For YouTube/web content agents, include "web_search" in tools
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
            "web_search": [
                "search",
                "google",
                "find online",
                "look up",
                "web",
                "youtube",
                "url",
                "link",
                "scrape",
                "fetch",
            ],
            "memory": ["remember", "recall", "memory", "history", "conversation"],
            "file_ops": ["read file", "write file", "file operations", "save to file"],
        }

        detected = []
        desc_lower = description.lower()

        for tool, patterns in TOOL_PATTERNS.items():
            if any(pattern in desc_lower for pattern in patterns):
                detected.append(tool)

        return detected

    async def detect_code_execution_need(self, description: str) -> bool:
        """Detect if the task requires Python code execution

        Uses both keyword matching and LLM-based analysis for accurate detection.

        Args:
            description: Natural language agent description

        Returns:
            True if code execution capabilities are needed

        Example:
            >>> desc = "Analyze sales.csv and calculate average"
            >>> needs_code = await parser.detect_code_execution_need(desc)
            >>> assert needs_code is True
        """
        CODE_EXECUTION_KEYWORDS = [
            # Data processing
            "csv",
            "json",
            "xml",
            "excel",
            "pandas",
            "numpy",
            "データ処理",
            "データ分析",
            "ファイル読み込み",
            # Calculations
            "計算",
            "calculate",
            "compute",
            "fibonacci",
            "素数",
            "prime",
            "平均",
            "average",
            "合計",
            "sum",
            "最大",
            "max",
            "最小",
            "min",
            "統計",
            "statistics",
            # File operations
            "ファイル処理",
            "file processing",
            "read file",
            "write file",
            "parse",
            "抽出",
            "extract",
            "変換",
            "convert",
            # Algorithms
            "ソート",
            "sort",
            "フィルタ",
            "filter",
            "集計",
            "aggregate",
            # Visualization
            "グラフ",
            "plot",
            "chart",
            "visualization",
            "matplotlib",
            "seaborn",
        ]

        description_lower = description.lower()

        # Quick keyword-based detection
        if any(keyword in description_lower for keyword in CODE_EXECUTION_KEYWORDS):
            return True

        # LLM-based detection for edge cases
        prompt = f"""Does this task require Python code execution?

Task: {description}

Answer YES if the task involves:
- Data processing (CSV, JSON, Excel files)
- Mathematical calculations or algorithms
- File manipulation or parsing
- Complex data transformations
- Statistical analysis
- Data visualization

Answer NO if the task involves:
- Simple text generation
- Translation or summarization
- Conversation or Q&A
- Information retrieval only (without processing)

Answer with just "YES" or "NO".
"""

        response = await call_llm(prompt, self.config)
        return "yes" in str(response).lower()
