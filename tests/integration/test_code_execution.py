"""Integration tests for code execution"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from kagura.agents import execute_code
from kagura.core.executor import CodeExecutor


@pytest.mark.asyncio
async def test_code_agent_end_to_end(mock_llm_response):
    """Test code generation → execution flow"""
    # Mock LLM to return valid Python code
    with mock_llm_response('result = sum([1, 2, 3, 4, 5])'):
        result = await execute_code("Calculate sum of 1 to 5")

        assert result["success"] is True
        assert result["result"] == 15
        assert "result = sum" in result["code"]


@pytest.mark.asyncio
async def test_code_executor_with_math():
    """Test CodeExecutor with math operations"""
    executor = CodeExecutor()

    result = await executor.execute("""
import math
result = math.sqrt(16)
""")

    assert result.success is True
    assert result.result == 4.0


@pytest.mark.asyncio
async def test_code_executor_security():
    """Test security constraints in CodeExecutor"""
    executor = CodeExecutor()

    # Test forbidden import
    result = await executor.execute("""
import os
result = os.getcwd()
""")

    assert result.success is False
    assert "Forbidden import" in result.error or "not allowed" in result.error.lower()


@pytest.mark.asyncio
async def test_code_executor_timeout():
    """Test timeout in CodeExecutor"""
    executor = CodeExecutor(timeout=1.0)

    result = await executor.execute("""
import time
time.sleep(5)
result = "done"
""")

    assert result.success is False
    assert "timeout" in result.error.lower() or "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_code_agent_with_error(mock_llm_response):
    """Test code agent error handling"""
    # Mock LLM to return invalid code
    with mock_llm_response('result = 1 / 0'):
        result = await execute_code("Divide by zero")

        assert result["success"] is False
        assert "division by zero" in result["error"].lower() or "zerodivision" in result["error"].lower()
