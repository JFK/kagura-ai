# Code Generator Agent

Demonstrates safe Python code generation and execution using Kagura AI 2.0's built-in executor.

## Overview

This example shows how to use Kagura AI 2.0's code execution feature:
- **Code generation**: LLM generates Python code from natural language
- **Safe execution**: Runs in a sandboxed environment with security constraints
- **Result extraction**: Automatically captures the `result` variable
- **Error handling**: Proper exception handling and reporting

## Code

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")

if result["success"]:
    print(f"Code:\n{result['code']}")
    print(f"Result: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

## How It Works

1. **Natural Language Input**: Describe what you want to calculate
2. **Code Generation**: LLM generates appropriate Python code
3. **AST Validation**: Code is validated for security (no dangerous operations)
4. **Execution**: Code runs in a sandboxed environment
5. **Result Extraction**: The `result` variable is captured and returned
6. **Error Handling**: Any errors are caught and reported

## Security Features

The code executor has built-in security constraints:
- **Forbidden imports**: Cannot import `os`, `sys`, `subprocess`, etc.
- **Forbidden operations**: No file I/O, no network access
- **AST validation**: Code is analyzed before execution
- **Timeout**: Execution has a time limit
- **Resource limits**: Memory and CPU constraints

## Response Format

The `execute_code` function returns a dictionary:

```python
{
    "success": bool,          # True if execution succeeded
    "code": str,              # Generated Python code
    "result": Any,            # Value of the 'result' variable
    "error": str | None,      # Error message if failed
}
```

## Examples

### 1. Mathematical Calculation

```python
result = await execute_code("Calculate the factorial of 10")
# Generated code:
# import math
# result = math.factorial(10)
# Result: 3628800
```

### 2. String Processing

```python
result = await execute_code("Reverse the string 'Hello' and convert to uppercase")
# Generated code:
# text = "Hello"
# result = text[::-1].upper()
# Result: "OLLEH"
```

### 3. List Operations

```python
result = await execute_code("Create a list of squares of numbers from 1 to 10")
# Generated code:
# result = [i**2 for i in range(1, 11)]
# Result: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
```

### 4. Statistical Analysis

```python
result = await execute_code("Calculate mean and std dev of [10, 20, 30, 40, 50]")
# Generated code:
# import statistics
# data = [10, 20, 30, 40, 50]
# result = {"mean": statistics.mean(data), "std": statistics.stdev(data)}
```

## Running the Example

```bash
python agent.py
```

## Expected Output

```
=== Code Generator Agent Example ===

1. Calculate Factorial
Task: Calculate the factorial of 10
Generated Code:
import math
result = math.factorial(10)

Result: 3628800

2. String Processing
Task: Reverse and uppercase string
Generated Code:
text = "Hello, World!"
result = text[::-1].upper()

Result: !DLROW ,OLLEH
...
```

## Key Concepts

- **execute_code()**: Built-in code execution agent
- **Safe execution**: Sandboxed environment with security constraints
- **Natural language → Code**: LLM generates executable Python
- **Error handling**: Graceful error reporting
- **Result capture**: Automatic extraction of results

## Advanced Usage

For more control, use the `CodeExecutor` class directly:

```python
from kagura.core.executor import CodeExecutor

executor = CodeExecutor(timeout=10.0)
result = await executor.execute("""
import math
result = math.factorial(10)
""")
```

## Next Steps

- See [simple_chat](../simple_chat/) for basic agent usage
- See [data_extractor](../data_extractor/) for structured data extraction
- See [workflow_example](../workflow_example/) for multi-step workflows
