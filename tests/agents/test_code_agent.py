"""Tests for code execution agent"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from kagura.agents.code_agent import (
    CodeExecutionAgent,
    execute_code,
    CodeResult
)


@pytest.mark.asyncio
async def test_code_agent_simple_task():
    """Test code agent with simple arithmetic task"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        # Mock the code generator to return simple code
        async def mock_generator(task_desc: str, feedback: str = ""):
            return "result = 2 + 2"

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Calculate 2 + 2")

        assert result.success is True
        assert result.result == 4
        assert "result = 2 + 2" in result.code
        assert result.error is None


@pytest.mark.asyncio
async def test_code_agent_with_math():
    """Test code agent with math module"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """import math
result = math.sqrt(16)"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Calculate square root of 16")

        assert result.success is True
        assert result.result == 4.0


@pytest.mark.asyncio
async def test_code_agent_with_function():
    """Test code agent with function definition"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Calculate 10th Fibonacci number")

        assert result.success is True
        assert result.result == 55


@pytest.mark.asyncio
async def test_code_agent_clean_markdown():
    """Test code cleaning removes markdown"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """```python
result = 42
```"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Return 42")

        assert result.success is True
        assert result.result == 42
        assert "```" not in result.code


@pytest.mark.asyncio
async def test_code_agent_error_handling():
    """Test code agent handles execution errors"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return "result = 1 / 0"  # Will cause ZeroDivisionError

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Divide by zero")

        assert result.success is False
        assert "ZeroDivisionError" in result.error
        assert result.result is None


@pytest.mark.asyncio
async def test_code_agent_security_error():
    """Test code agent handles security violations"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return "import os\nresult = os.getcwd()"

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Get current directory")

        assert result.success is False
        assert "SecurityError" in result.error


@pytest.mark.asyncio
async def test_code_agent_with_retry_success():
    """Test code agent retry succeeds on second attempt"""
    agent = CodeExecutionAgent(max_retries=3)

    call_count = 0

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First attempt: error
                return "result = 1 / 0"
            else:
                # Second attempt: success
                return "result = 42"

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute_with_retry("Calculate something")

        assert result.success is True
        assert result.result == 42
        assert call_count == 2  # Should have retried once


@pytest.mark.asyncio
async def test_code_agent_with_retry_max_attempts():
    """Test code agent exhausts max retries"""
    agent = CodeExecutionAgent(max_retries=2)

    call_count = 0

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            nonlocal call_count
            call_count += 1
            # Always fail
            return "result = 1 / 0"

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute_with_retry("Always fail")

        assert result.success is False
        assert call_count == 2  # Max retries


@pytest.mark.asyncio
async def test_code_agent_stdout_capture():
    """Test code agent captures stdout"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """print("Hello, World!")
result = 42"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Print and return")

        assert result.success is True
        assert "Hello, World!" in result.stdout
        assert result.result == 42


@pytest.mark.asyncio
async def test_execute_code_convenience_function():
    """Test execute_code convenience function"""
    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return "result = 100"

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await execute_code("Return 100")

        assert result["success"] is True
        assert result["result"] == 100
        assert result["error"] is None
        assert "result = 100" in result["code"]


@pytest.mark.asyncio
async def test_code_agent_list_operations():
    """Test code agent with list operations"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """numbers = [1, 2, 3, 4, 5]
result = sum(numbers)"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Sum the list [1,2,3,4,5]")

        assert result.success is True
        assert result.result == 15


@pytest.mark.asyncio
async def test_code_agent_json_parsing():
    """Test code agent with JSON parsing"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return '''import json
data = '{"name": "Alice", "age": 30}'
result = json.loads(data)'''

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Parse JSON")

        assert result.success is True
        assert result.result == {"name": "Alice", "age": 30}


@pytest.mark.asyncio
async def test_code_agent_statistics():
    """Test code agent with statistics module"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """import statistics
data = [1, 2, 3, 4, 5]
result = statistics.mean(data)"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Calculate mean of [1,2,3,4,5]")

        assert result.success is True
        assert result.result == 3.0


@pytest.mark.asyncio
async def test_code_result_model():
    """Test CodeResult model"""
    result = CodeResult(
        task="Test task",
        code="result = 42",
        success=True,
        result=42,
        execution_time=0.001
    )

    assert result.task == "Test task"
    assert result.code == "result = 42"
    assert result.success is True
    assert result.result == 42
    assert result.error is None
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.asyncio
async def test_code_agent_custom_timeout():
    """Test code agent with custom timeout"""
    agent = CodeExecutionAgent(timeout=1.0)

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """import time
time.sleep(5)
result = 42"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Sleep too long")

        assert result.success is False
        assert "TimeoutError" in result.error


@pytest.mark.asyncio
async def test_code_agent_complex_task():
    """Test code agent with complex multi-step task"""
    agent = CodeExecutionAgent()

    with patch('kagura.agents.code_agent.agent') as mock_agent_decorator:
        async def mock_generator(task_desc: str, feedback: str = ""):
            return """import statistics

def calculate_stats(numbers):
    return {
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'stdev': statistics.stdev(numbers) if len(numbers) > 1 else 0
    }

data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
result = calculate_stats(data)"""

        mock_agent_decorator.return_value = lambda fn: mock_generator

        result = await agent.execute("Calculate statistics for 1-10")

        assert result.success is True
        assert 'mean' in result.result
        assert 'median' in result.result
        assert 'stdev' in result.result
        assert result.result['mean'] == 5.5
        assert result.result['median'] == 5.5
