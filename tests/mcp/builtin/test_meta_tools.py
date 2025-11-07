"""Tests for meta agent MCP tools (Issue #583)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kagura.mcp.builtin.meta import meta_create_agent, meta_fix_code_error


@pytest.mark.asyncio
async def test_meta_create_agent_basic():
    """Test meta_create_agent MCP tool."""
    mock_meta = MagicMock()
    mock_meta.generate = AsyncMock(return_value="def agent(): pass")

    with patch("kagura.meta.MetaAgent", return_value=mock_meta):
        result = await meta_create_agent(description="Simple agent")

        assert "def agent():" in result
        mock_meta.generate.assert_called_once_with("Simple agent")


@pytest.mark.asyncio
async def test_meta_fix_code_error_success():
    """Test meta_fix_code_error with valid fix."""
    # Mock LLM response
    llm_response = json.dumps(
        {
            "root_cause": "Missing colon after function definition",
            "fixed_code": "def add(a, b):\n    return a + b",
            "explanation": "Added colon after function parameters",
        }
    )

    mock_validator = MagicMock()
    mock_validator.validate.return_value = True

    with patch("kagura.core.llm.call_llm", new=AsyncMock(return_value=llm_response)):
        with patch("kagura.meta.validator.CodeValidator", return_value=mock_validator):
            result_str = await meta_fix_code_error(
                code="def add(a, b)\n    return a + b",
                error="SyntaxError: invalid syntax",
            )

            result = json.loads(result_str)
            assert result["success"] is True
            assert "def add(a, b):" in result["fixed_code"]
            assert "root_cause" in result
            assert "explanation" in result


@pytest.mark.asyncio
async def test_meta_fix_code_error_with_context():
    """Test meta_fix_code_error with additional context."""
    llm_response = json.dumps(
        {
            "root_cause": "Variable not defined",
            "fixed_code": "def process(data):\n    result = data * 2\n    return result",
            "explanation": "Defined result variable",
        }
    )

    mock_validator = MagicMock()
    mock_validator.validate.return_value = True

    with patch("kagura.core.llm.call_llm", new=AsyncMock(return_value=llm_response)):
        with patch("kagura.meta.validator.CodeValidator", return_value=mock_validator):
            result_str = await meta_fix_code_error(
                code="def process(data):\n    return result",
                error="NameError: name 'result' is not defined",
                context="This function should double the input value",
            )

            result = json.loads(result_str)
            assert result["success"] is True
            assert result["context_used"] is True


@pytest.mark.asyncio
async def test_meta_fix_code_error_invalid_fixed_code():
    """Test when LLM returns invalid Python code."""
    llm_response = json.dumps(
        {
            "root_cause": "Some error",
            "fixed_code": "this is not valid python (",
            "explanation": "Attempted fix",
        }
    )

    mock_validator = MagicMock()
    mock_validator.validate.return_value = False  # Invalid code

    with patch("kagura.core.llm.call_llm", new=AsyncMock(return_value=llm_response)):
        with patch("kagura.meta.validator.CodeValidator", return_value=mock_validator):
            result_str = await meta_fix_code_error(
                code="def broken():", error="SyntaxError"
            )

            result = json.loads(result_str)
            assert result["success"] is False
            assert "not valid Python" in result["error"]


@pytest.mark.asyncio
async def test_meta_fix_code_error_json_parse_failure():
    """Test when LLM returns non-JSON response."""
    llm_response = "This is not JSON, just a plain text response"

    with patch("kagura.core.llm.call_llm", new=AsyncMock(return_value=llm_response)):
        result_str = await meta_fix_code_error(
            code="def test():", error="SyntaxError"
        )

        result = json.loads(result_str)
        assert result["success"] is False
        assert "Failed to parse LLM response" in result["error"]


@pytest.mark.asyncio
async def test_meta_fix_code_error_with_markdown_json():
    """Test parsing JSON from markdown code blocks."""
    llm_response = """Here is the fix:

```json
{
    "root_cause": "Missing import",
    "fixed_code": "import os\\ndef test(): pass",
    "explanation": "Added import statement"
}
```

That should fix it!"""

    mock_validator = MagicMock()
    mock_validator.validate.return_value = True

    with patch("kagura.core.llm.call_llm", new=AsyncMock(return_value=llm_response)):
        with patch("kagura.meta.validator.CodeValidator", return_value=mock_validator):
            result_str = await meta_fix_code_error(
                code="def test(): pass", error="ImportError: os not found"
            )

            result = json.loads(result_str)
            assert result["success"] is True
            assert "import os" in result["fixed_code"]


@pytest.mark.asyncio
async def test_meta_fix_code_error_exception_handling():
    """Test exception handling in meta_fix_code_error."""
    with patch(
        "kagura.core.llm.call_llm",
        new=AsyncMock(side_effect=Exception("LLM call failed")),
    ):
        result_str = await meta_fix_code_error(
            code="def test():", error="SyntaxError"
        )

        result = json.loads(result_str)
        assert result["success"] is False
        assert "Failed to fix code" in result["error"]
