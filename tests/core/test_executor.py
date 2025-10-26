"""Tests for code executor"""


import pytest

from kagura.core.executor import (
    CodeExecutor,
)


# Basic execution tests
@pytest.mark.asyncio
async def test_simple_arithmetic():
    """Test simple arithmetic execution"""
    executor = CodeExecutor()
    result = await executor.execute("result = 2 + 2")

    assert result.success is True
    assert result.result == 4
    assert result.error is None


@pytest.mark.asyncio
async def test_math_sqrt():
    """Test math.sqrt execution"""
    executor = CodeExecutor()
    result = await executor.execute("""
import math
result = math.sqrt(16)
""")

    assert result.success is True
    assert result.result == 4.0


@pytest.mark.asyncio
async def test_multiple_operations():
    """Test multiple operations"""
    executor = CodeExecutor()
    result = await executor.execute("""
x = 10
y = 20
result = x + y
""")

    assert result.success is True
    assert result.result == 30


@pytest.mark.asyncio
async def test_list_operations():
    """Test list operations"""
    executor = CodeExecutor()
    result = await executor.execute("""
numbers = [1, 2, 3, 4, 5]
result = sum(numbers)
""")

    assert result.success is True
    assert result.result == 15


@pytest.mark.asyncio
async def test_string_operations():
    """Test string operations"""
    executor = CodeExecutor()
    result = await executor.execute("""
text = "hello world"
result = text.upper()
""")

    assert result.success is True
    assert result.result == "HELLO WORLD"


@pytest.mark.asyncio
async def test_dict_operations():
    """Test dictionary operations"""
    executor = CodeExecutor()
    result = await executor.execute("""
data = {"name": "Alice", "age": 30}
result = data["name"]
""")

    assert result.success is True
    assert result.result == "Alice"


# Print and output capture tests
@pytest.mark.asyncio
async def test_stdout_capture():
    """Test stdout capture"""
    executor = CodeExecutor()
    result = await executor.execute("""
print("Hello, World!")
result = 42
""")

    assert result.success is True
    assert result.result == 42
    assert "Hello, World!" in result.stdout


@pytest.mark.asyncio
async def test_multiple_prints():
    """Test multiple print statements"""
    executor = CodeExecutor()
    result = await executor.execute("""
print("Line 1")
print("Line 2")
result = "done"
""")

    assert result.success is True
    assert "Line 1" in result.stdout
    assert "Line 2" in result.stdout


# Security tests - disallowed imports
@pytest.mark.asyncio
async def test_disallowed_import_os():
    """Test that os import is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
import os
result = os.getcwd()
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "os" in result.error


@pytest.mark.asyncio
async def test_disallowed_import_sys():
    """Test that sys import is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
import sys
result = sys.version
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "sys" in result.error


@pytest.mark.asyncio
async def test_disallowed_import_subprocess():
    """Test that subprocess import is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
import subprocess
result = subprocess.run(["ls"])
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "subprocess" in result.error


@pytest.mark.asyncio
async def test_disallowed_from_import():
    """Test that from...import is also blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
from os import getcwd
result = getcwd()
""")

    assert result.success is False
    assert "SecurityError" in result.error


# Security tests - disallowed names
@pytest.mark.asyncio
async def test_disallowed_eval():
    """Test that eval is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = eval("2 + 2")
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "eval" in result.error


@pytest.mark.asyncio
async def test_disallowed_exec():
    """Test that exec is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
exec("result = 42")
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "exec" in result.error


@pytest.mark.asyncio
async def test_disallowed_open():
    """Test that open is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = open("/etc/passwd")
""")

    assert result.success is False
    assert "SecurityError" in result.error
    assert "open" in result.error


@pytest.mark.asyncio
async def test_disallowed_import_builtin():
    """Test that __import__ with disallowed module is blocked"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = __import__("os")
""")

    assert result.success is False
    assert "ImportError" in result.error
    assert "not allowed" in result.error


# Allowed imports tests
@pytest.mark.asyncio
async def test_allowed_import_json():
    """Test that json import is allowed"""
    executor = CodeExecutor()
    result = await executor.execute("""
import json
data = '{"key": "value"}'
result = json.loads(data)
""")

    assert result.success is True
    assert result.result == {"key": "value"}


@pytest.mark.asyncio
async def test_allowed_import_datetime():
    """Test that datetime import is allowed"""
    executor = CodeExecutor()
    result = await executor.execute("""
from datetime import datetime
result = str(datetime(2024, 1, 1))
""")

    assert result.success is True
    assert "2024-01-01" in result.result


@pytest.mark.asyncio
async def test_allowed_import_statistics():
    """Test that statistics import is allowed"""
    executor = CodeExecutor()
    result = await executor.execute("""
import statistics
data = [1, 2, 3, 4, 5]
result = statistics.mean(data)
""")

    assert result.success is True
    assert result.result == 3.0


# Error handling tests
@pytest.mark.asyncio
async def test_syntax_error():
    """Test syntax error handling"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = 2 +
""")

    assert result.success is False
    assert "SyntaxError" in result.error


@pytest.mark.asyncio
async def test_runtime_error():
    """Test runtime error handling"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = 1 / 0
""")

    assert result.success is False
    assert "ZeroDivisionError" in result.error


@pytest.mark.asyncio
async def test_name_error():
    """Test name error handling"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = undefined_variable
""")

    assert result.success is False
    assert "NameError" in result.error


@pytest.mark.asyncio
async def test_type_error():
    """Test type error handling"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = "string" + 123
""")

    assert result.success is False
    assert "TypeError" in result.error


# Timeout tests
@pytest.mark.asyncio
async def test_timeout():
    """Test timeout enforcement"""
    executor = CodeExecutor(timeout=1.0)
    result = await executor.execute("""
import time
time.sleep(5)
result = "should not reach here"
""")

    assert result.success is False
    assert "TimeoutError" in result.error


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="This test causes pytest-asyncio event loop cleanup to hang - known issue"
)
async def test_infinite_loop_timeout():
    """Test timeout on infinite loop"""
    executor = CodeExecutor(timeout=1.0)
    result = await executor.execute("""
while True:
    pass
""")

    assert result.success is False
    assert "TimeoutError" in result.error


# Execution time tracking
@pytest.mark.asyncio
async def test_execution_time():
    """Test execution time tracking"""
    executor = CodeExecutor()
    result = await executor.execute("result = 2 + 2")

    assert result.execution_time > 0
    assert result.execution_time < 1.0  # Should be very fast


# No result variable
@pytest.mark.asyncio
async def test_no_result_variable():
    """Test code without result variable"""
    executor = CodeExecutor()
    result = await executor.execute("""
x = 10
y = 20
z = x + y
""")

    assert result.success is True
    assert result.result is None


# Complex code tests
@pytest.mark.asyncio
async def test_function_definition():
    """Test function definition and call"""
    executor = CodeExecutor()
    result = await executor.execute("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
""")

    assert result.success is True
    assert result.result == 55


@pytest.mark.asyncio
async def test_list_comprehension():
    """Test list comprehension"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = [x * 2 for x in range(5)]
""")

    assert result.success is True
    assert result.result == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_dictionary_comprehension():
    """Test dictionary comprehension"""
    executor = CodeExecutor()
    result = await executor.execute("""
result = {x: x**2 for x in range(5)}
""")

    assert result.success is True
    assert result.result == {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}


# Custom allowed imports
@pytest.mark.asyncio
async def test_custom_allowed_imports():
    """Test custom allowed imports"""
    executor = CodeExecutor(allowed_imports={"math"})

    # Math should work
    result = await executor.execute("""
import math
result = math.sqrt(16)
""")
    assert result.success is True

    # JSON should not work
    result = await executor.execute("""
import json
result = json.loads('{}')
""")
    assert result.success is False
    assert "SecurityError" in result.error


# Integration test
@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration with imports, functions, and operations"""
    executor = CodeExecutor()
    result = await executor.execute("""
import math
import statistics

def calculate_stats(numbers):
    return {
        'mean': statistics.mean(numbers),
        'median': statistics.median(numbers),
        'stdev': statistics.stdev(numbers) if len(numbers) > 1 else 0
    }

data = [1, 2, 3, 4, 5]
result = calculate_stats(data)
""")

    assert result.success is True
    assert result.result["mean"] == 3.0
    assert result.result["median"] == 3
