"""Error analysis for self-improving agents"""

import traceback
from dataclasses import dataclass
from typing import Any, Optional

from kagura.core.llm import LLMConfig, call_llm


@dataclass
class ErrorAnalysis:
    """Error analysis result

    Contains information about an error that occurred during agent execution
    and suggestions for how to fix it.

    Attributes:
        error_type: Type of error (e.g., "FileNotFoundError")
        error_message: Error message string
        stack_trace: Full stack trace
        root_cause: LLM-identified root cause
        suggested_fix: How to fix the error
        fix_code: Optional code snippet to apply
    """

    error_type: str
    error_message: str
    stack_trace: str
    root_cause: str
    suggested_fix: str
    fix_code: Optional[str] = None


class ErrorAnalyzer:
    """Analyze runtime errors in generated agents

    Uses LLM to analyze errors and suggest fixes for self-improving agents.

    Example:
        >>> analyzer = ErrorAnalyzer()
        >>> try:
        ...     raise FileNotFoundError("data.csv not found")
        ... except Exception as e:
        ...     analysis = await analyzer.analyze(e, agent_code, user_input)
        ...     print(analysis.suggested_fix)
    """

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize error analyzer

        Args:
            llm_config: LLM configuration for error analysis.
                       Defaults to gpt-4o-mini with temperature=0.3
        """
        self.llm_config = llm_config or LLMConfig(model="gpt-5-mini", temperature=0.3)

    async def analyze(
        self,
        exception: Exception,
        agent_code: str,
        user_input: dict[str, Any],
    ) -> ErrorAnalysis:
        """Analyze error and suggest fix

        Args:
            exception: Exception that occurred during execution
            agent_code: Generated agent code that caused error
            user_input: User input that triggered the error

        Returns:
            ErrorAnalysis with root cause and suggested fix

        Example:
            >>> try:
            ...     result = await agent("sales.csv")
            ... except FileNotFoundError as e:
            ...     analysis = await analyzer.analyze(e, code, {"path": "sales.csv"})
            ...     print(f"Fix: {analysis.suggested_fix}")
        """
        # Extract error details
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )

        # LLM-based analysis
        analysis_prompt = f"""Analyze this error in a Kagura AI agent and suggest a fix.

**Agent Code:**
```python
{agent_code}
```

**User Input:**
{user_input}

**Error:**
Type: {error_type}
Message: {error_message}

**Stack Trace:**
{stack_trace}

**Task:**
1. Identify the root cause
2. Suggest a specific fix
3. Provide the corrected code snippet (if applicable)

**Output format:**
Root cause: [explanation]
Suggested fix: [fix description]
Fix code: [code snippet or "N/A"]
"""

        response = await call_llm(analysis_prompt, self.llm_config)

        # Convert to string if LLMResponse
        response_str = str(response)

        # Parse LLM response
        root_cause = self._extract_section(response_str, "Root cause")
        suggested_fix = self._extract_section(response_str, "Suggested fix")
        fix_code = self._extract_section(response_str, "Fix code")

        return ErrorAnalysis(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            root_cause=root_cause,
            suggested_fix=suggested_fix,
            fix_code=fix_code if fix_code != "N/A" else None,
        )

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract section from LLM response

        Args:
            text: LLM response text
            section_name: Section name to extract (e.g., "Root cause")

        Returns:
            Extracted section content
        """
        lines = text.split("\n")
        result = []
        in_section = False

        for line in lines:
            # Check if this line starts the section
            if section_name.lower() in line.lower():
                in_section = True
                # Extract content after colon
                if ":" in line:
                    content = line.split(":", 1)[1].strip()
                    if content:
                        result.append(content)
                continue

            if in_section:
                # Stop at next section header
                if any(
                    keyword in line.lower()
                    for keyword in ["root cause", "suggested fix", "fix code"]
                ):
                    if not line.strip().startswith(section_name.lower()):
                        break

                # Skip empty lines at start
                if not result and not line.strip():
                    continue

                result.append(line)

        return "\n".join(result).strip()


__all__ = ["ErrorAnalyzer", "ErrorAnalysis"]
