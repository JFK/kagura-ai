"""Built-in MCP tools for Meta Agent

Exposes agent generation capabilities via MCP.
"""

from __future__ import annotations

from kagura import tool


@tool
async def meta_create_agent(description: str) -> str:
    """Create agent from natural language description

    Args:
        description: Agent description

    Returns:
        Generated agent code or error message
    """
    try:
        from kagura.meta import MetaAgent

        meta = MetaAgent()
        code = await meta.generate(description)

        return code
    except Exception as e:
        return f"Error creating agent: {e}"


@tool
async def meta_fix_code_error(code: str, error: str, context: str = "") -> str:
    """Automatically fix syntax/type errors in code.

    Use for automated error resolution in IDE workflows, CI/CD, or coding assistants.

    Args:
        code: Source code with error
        error: Error message or stack trace
        context: Optional context (e.g., from chunked documents via Issue #581)

    Returns:
        JSON with fixed_code, explanation, and success status

    Example:
        # Syntax error
        code = 'def add(a, b)\\n    return a + b'  # Missing colon
        error = 'SyntaxError: invalid syntax'
        result = meta_fix_code_error(code, error)
        # Returns: {"success": true, "fixed_code": "def add(a, b):\\n    return a + b", ...}
    """
    import json

    try:
        from kagura.core.llm import LLMConfig, call_llm
        from kagura.meta.validator import CodeValidator

        # Build analysis prompt
        context_section = f"\n\n**Additional Context:**\n{context}" if context else ""

        prompt = f"""Fix the following Python code error.

**Original Code:**
```python
{code}
```

**Error:**
{error}{context_section}

**Task:**
1. Identify the root cause of the error
2. Provide the corrected code
3. Explain what was fixed

**Output format (JSON):**
{{
    "root_cause": "explanation",
    "fixed_code": "corrected code here",
    "explanation": "what was changed and why"
}}

Return ONLY valid JSON, no additional text."""

        # Use LLM to analyze and fix
        llm_config = LLMConfig(model="gpt-5-mini", temperature=0.2)
        response = await call_llm(prompt, llm_config)
        response_str = str(response)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_str:
                json_start = response_str.find("```json") + 7
                json_end = response_str.find("```", json_start)
                json_str = response_str[json_start:json_end].strip()
            elif "```" in response_str:
                json_start = response_str.find("```") + 3
                json_end = response_str.find("```", json_start)
                json_str = response_str[json_start:json_end].strip()
            else:
                json_str = response_str.strip()

            fix_data = json.loads(json_str)
            fixed_code = fix_data.get("fixed_code", "")
            root_cause = fix_data.get("root_cause", "Unknown")
            explanation = fix_data.get("explanation", "No explanation provided")

        except (json.JSONDecodeError, KeyError) as e:
            return json.dumps(
                {
                    "success": False,
                    "error": "Failed to parse LLM response",
                    "details": str(e),
                    "llm_response": response_str[:500],
                },
                indent=2,
            )

        # Validate fixed code
        if fixed_code:
            validator = CodeValidator()
            if validator.validate(fixed_code):
                return json.dumps(
                    {
                        "success": True,
                        "fixed_code": fixed_code,
                        "root_cause": root_cause,
                        "explanation": explanation,
                        "context_used": bool(context),
                    },
                    indent=2,
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Fixed code is not valid Python",
                        "suggested_code": fixed_code,
                        "root_cause": root_cause,
                        "explanation": explanation,
                    },
                    indent=2,
                )
        else:
            return json.dumps(
                {
                    "success": False,
                    "error": "No fixed code provided by LLM",
                    "root_cause": root_cause,
                    "explanation": explanation,
                },
                indent=2,
            )

    except Exception as e:
        return json.dumps(
            {"success": False, "error": f"Failed to fix code: {str(e)}"}, indent=2
        )
