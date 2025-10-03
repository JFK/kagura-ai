# Code Executor

The Code Executor provides safe Python code generation and execution capabilities in Kagura AI 2.0.

## Overview

The code execution system consists of:
1. **CodeExecutor**: Low-level code execution with security constraints
2. **execute_code()**: High-level agent that generates and executes code from natural language

## execute_code() Function

The simplest way to use code execution is through the `execute_code()` convenience function.

### Signature

```python
async def execute_code(task: str, *, model: str = "gpt-4o-mini") -> dict
```

### Parameters

- **task** (`str`): Natural language description of what to calculate or compute
- **model** (`str`, optional): LLM model to use for code generation

### Return Value

Returns a dictionary with the following keys:

```python
{
    "success": bool,          # True if execution succeeded
    "code": str,              # Generated Python code
    "result": Any,            # Value of the 'result' variable
    "error": str | None,      # Error message if failed
}
```

### Examples

#### Basic Calculation

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")

if result["success"]:
    print(f"Code:\n{result['code']}\n")
    print(f"Result: {result['result']}")
    # Code:
    # import math
    # result = math.factorial(10)
    #
    # Result: 3628800
else:
    print(f"Error: {result['error']}")
```

#### String Processing

```python
result = await execute_code("Reverse the string 'Hello, World!' and make it uppercase")

if result["success"]:
    print(result['result'])  # "!DLROW ,OLLEH"
```

#### List Operations

```python
result = await execute_code("Create a list of squares of numbers from 1 to 10")

if result["success"]:
    print(result['result'])  # [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
```

#### Statistical Analysis

```python
result = await execute_code(
    "Calculate the mean and standard deviation of [10, 20, 30, 40, 50]"
)

if result["success"]:
    print(result['result'])
    # {'mean': 30.0, 'stdev': 15.811388300841896}
```

#### Error Handling

```python
result = await execute_code("Divide 100 by 0")

if not result["success"]:
    print(f"Error: {result['error']}")
    # Error: division by zero
```

## CodeExecutor Class

For more control, use the `CodeExecutor` class directly.

### Signature

```python
class CodeExecutor:
    def __init__(
        self,
        timeout: float = 30.0,
        max_memory: int = 512 * 1024 * 1024,  # 512MB
        allowed_imports: set[str] | None = None
    )
```

### Parameters

- **timeout** (`float`, default: `30.0`): Maximum execution time in seconds
- **max_memory** (`int`, default: `512MB`): Maximum memory usage in bytes
- **allowed_imports** (`set[str] | None`): Set of allowed import modules. If `None`, uses default safe list.

### Methods

#### execute()

```python
async def execute(self, code: str) -> ExecutionResult
```

Executes Python code and returns the result.

**Parameters:**
- **code** (`str`): Python code to execute. Must set a variable named `result`.

**Returns:**
- `ExecutionResult` object with fields:
  - `success` (`bool`): Whether execution succeeded
  - `result` (`Any`): Value of the `result` variable
  - `error` (`str | None`): Error message if failed
  - `stdout` (`str`): Captured stdout output
  - `stderr` (`str`): Captured stderr output

### Examples

#### Basic Usage

```python
from kagura.core.executor import CodeExecutor

executor = CodeExecutor()

result = await executor.execute("""
import math
result = math.sqrt(16)
""")

print(result.success)  # True
print(result.result)   # 4.0
```

#### Custom Timeout

```python
executor = CodeExecutor(timeout=60.0)

result = await executor.execute("""
import time
time.sleep(2)
result = "completed"
""")
```

#### Capturing Output

```python
result = await executor.execute("""
print("Debug message")
result = 42
""")

print(result.stdout)  # "Debug message\n"
print(result.result)  # 42
```

## Security Features

The Code Executor has built-in security constraints to prevent malicious code execution.

### Forbidden Imports

The following modules are blocked by default:

- **System Access**: `os`, `sys`, `subprocess`, `shutil`
- **File I/O**: `open` (built-in), `io` (restricted)
- **Network**: `socket`, `urllib`, `requests`, `http`
- **Process Control**: `multiprocessing`, `threading` (restricted)
- **Code Execution**: `eval`, `exec`, `compile` (built-in)
- **Dangerous Modules**: `pickle`, `ctypes`, `importlib`

### Allowed Imports

Safe modules that are allowed by default:

```python
ALLOWED_IMPORTS = {
    "math",
    "statistics",
    "random",
    "datetime",
    "json",
    "re",
    "collections",
    "itertools",
    "functools",
    "typing",
}
```

### AST Validation

Before execution, code is analyzed using Python's Abstract Syntax Tree (AST) to detect:

- Forbidden function calls (`eval`, `exec`, `open`, etc.)
- Forbidden imports
- Dangerous operations

Example validation error:

```python
result = await executor.execute("""
import os
result = os.system('ls')
""")

print(result.error)
# "Forbidden import: os"
```

### Resource Limits

- **Timeout**: Code execution is terminated after the timeout period
- **Memory**: Process memory is monitored (platform-dependent)
- **CPU**: No infinite loops allowed (enforced via timeout)

## Advanced Usage

### Custom Allowed Imports

```python
executor = CodeExecutor(
    allowed_imports={"math", "numpy", "pandas"}
)

result = await executor.execute("""
import numpy as np
result = np.array([1, 2, 3]).mean()
""")
```

### Error Recovery

```python
executor = CodeExecutor()

code = """
import math
result = math.factorial(10)
"""

try:
    result = await executor.execute(code)
    if result.success:
        print(f"Success: {result.result}")
    else:
        print(f"Execution error: {result.error}")
except TimeoutError:
    print("Code execution timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Combining with Agents

```python
from kagura import agent
from kagura.core.executor import CodeExecutor

executor = CodeExecutor()

@agent
async def generate_code(task: str) -> str:
    '''Generate Python code to: {{ task }}

    Return only the code, nothing else.
    '''
    pass

async def run_task(task: str):
    # Generate code
    code = await generate_code(task)

    # Execute code
    result = await executor.execute(code)

    return result

# Use it
result = await run_task("Calculate fibonacci(15)")
print(result.result)
```

## Best Practices

### 1. Always Check Success

```python
result = await execute_code("some task")

if result["success"]:
    # Use result["result"]
    process(result["result"])
else:
    # Handle error
    log_error(result["error"])
```

### 2. Set Appropriate Timeouts

```python
# Short tasks
executor = CodeExecutor(timeout=5.0)

# Long computations
executor = CodeExecutor(timeout=300.0)
```

### 3. Use result Variable

The executor looks for a variable named `result`:

```python
# Good
result = await executor.execute("""
x = 10
y = 20
result = x + y
""")

# Won't work - no 'result' variable
result = await executor.execute("""
x = 10
y = 20
print(x + y)
""")
```

### 4. Handle Errors Gracefully

```python
result = await execute_code(task)

if not result["success"]:
    # Retry with more explicit instructions
    task = f"{task}. Show step by step."
    result = await execute_code(task)
```

## Limitations

1. **No File I/O**: Cannot read or write files
2. **No Network Access**: Cannot make HTTP requests
3. **No System Commands**: Cannot execute shell commands
4. **Limited Libraries**: Only safe, pre-approved libraries
5. **Memory Constraints**: Large data structures may fail
6. **Execution Time**: Long-running code will timeout

## Security Considerations

⚠️ **Important**: While the Code Executor has security constraints, it should still be used with caution:

1. **User Input**: Be careful with untrusted user input
2. **Production Use**: Consider additional sandboxing for production
3. **Resource Limits**: Set appropriate timeouts and memory limits
4. **Monitoring**: Log all code execution for auditing

## Related

- [@agent Decorator](agent.md) - Creating AI agents
- [Code Generator Example](../../examples/agents/code_generator/) - Full example
- [Quick Start](../quickstart.md#code-execution) - Getting started
