# Tools API Reference

## Overview

The Tools API provides decorators and utilities for creating non-LLM functions that can be called by agents and exposed via MCP.

---

## `@tool` Decorator

Convert a regular Python function into a registered tool.

### Signature

```python
@tool
def function_name(...) -> ReturnType:
    """Function docstring"""
    pass

# Or with custom name
@tool(name="custom_name")
def function_name(...) -> ReturnType:
    """Function docstring"""
    pass
```

### Parameters

- **fn** (`Callable[P, T] | None`): Function to decorate (optional, for use without parentheses)
- **name** (`str | None`): Custom tool name (defaults to function name)

### Returns

- **Callable[P, T]**: Decorated function with type validation and registry integration

### Behavior

1. **Type Validation**: Validates arguments against function signature at call time
2. **Registry Integration**: Automatically registers tool in global `tool_registry`
3. **Metadata Preservation**: Preserves function name, docstring, and signature
4. **Error Handling**: Raises `TypeError` for invalid arguments

### Metadata Attributes

Decorated functions have the following metadata attributes:

- **`_is_tool`** (`bool`): Always `True` for tool-decorated functions
- **`_tool_name`** (`str`): Tool name (function name or custom name)
- **`_tool_signature`** (`inspect.Signature`): Function signature
- **`_tool_docstring`** (`str`): Function docstring

### Examples

#### Basic Tool

```python
from kagura import tool

@tool
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

result = add(5.0, 3.0)  # 8.0
```

#### Tool with Default Parameters

```python
@tool
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone"""
    return f"{greeting}, {name}!"

greet("Alice")           # "Hello, Alice!"
greet("Bob", "Hi")       # "Hi, Bob!"
```

#### Tool with Custom Name

```python
@tool(name="tax_calculator")
def calc_tax(amount: float, rate: float = 0.1) -> float:
    """Calculate tax amount"""
    return amount * rate

# Registered as "tax_calculator"
```

#### Tool with Complex Return Type

```python
@tool
def get_user(user_id: int) -> dict[str, Any]:
    """Get user data"""
    return {
        "id": user_id,
        "name": "Alice",
        "active": True
    }
```

#### Tool with Error Handling

```python
@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

result = divide(10.0, 2.0)  # 5.0
divide(10.0, 0.0)           # ValueError
```

### Error Handling

```python
@tool
def strict_function(x: int, y: int) -> int:
    """Requires exactly 2 arguments"""
    return x + y

# Valid
strict_function(1, 2)         # ✅ 3
strict_function(x=1, y=2)     # ✅ 3

# Invalid - raises TypeError
strict_function(1)            # ❌ TypeError: invalid arguments
strict_function(1, 2, 3)      # ❌ TypeError: invalid arguments
```

---

## Tool Registry

### `ToolRegistry` Class

Global registry for all Kagura tools.

#### Methods

##### `register(name: str, func: Callable[..., Any]) -> None`

Register a tool.

**Parameters**:
- `name` (`str`): Tool name (must be unique)
- `func` (`Callable`): Tool function

**Raises**:
- `ValueError`: If tool name is already registered

**Example**:
```python
from kagura.core.tool_registry import tool_registry

def my_tool():
    return "result"

tool_registry.register("my_tool", my_tool)
```

##### `get(name: str) -> Callable[..., Any] | None`

Get tool by name.

**Parameters**:
- `name` (`str`): Tool name

**Returns**:
- Tool function, or `None` if not found

**Example**:
```python
tool = tool_registry.get("my_tool")
if tool:
    result = tool()
```

##### `get_all() -> dict[str, Callable[..., Any]]`

Get all registered tools.

**Returns**:
- Dictionary of `tool_name` → `tool_function`

**Example**:
```python
all_tools = tool_registry.get_all()
for name, func in all_tools.items():
    print(f"{name}: {func.__doc__}")
```

##### `list_names() -> list[str]`

List all tool names.

**Returns**:
- List of tool names

**Example**:
```python
names = tool_registry.list_names()
print(names)  # ['add', 'multiply', 'divide']
```

##### `unregister(name: str) -> None`

Unregister a tool.

**Parameters**:
- `name` (`str`): Tool name

**Raises**:
- `KeyError`: If tool is not registered

**Example**:
```python
tool_registry.unregister("my_tool")
```

##### `clear() -> None`

Clear all tools from registry.

**Example**:
```python
tool_registry.clear()
assert len(tool_registry.list_names()) == 0
```

##### `auto_discover(module_path: str) -> None`

Auto-discover tools in a module.

Scans a module for functions decorated with `@tool` and automatically registers them.

**Parameters**:
- `module_path` (`str`): Python module path (e.g., `"my_package.tools"`)

**Raises**:
- `ValueError`: If module is not found

**Example**:
```python
# my_package/tools.py
from kagura import tool

@tool
def tool1():
    return 1

@tool
def tool2():
    return 2

# main.py
from kagura.core.tool_registry import tool_registry

tool_registry.auto_discover("my_package.tools")
print(tool_registry.list_names())  # ['tool1', 'tool2']
```

### Global Registry Instance

The global `tool_registry` instance is automatically created and available for import:

```python
from kagura.core.tool_registry import tool_registry

# Check if tool exists
if "my_tool" in tool_registry.list_names():
    tool = tool_registry.get("my_tool")
    result = tool()
```

---

## Type Validation

Tools validate arguments using `inspect.signature` at call time.

### Supported Features

1. **Positional Arguments**
   ```python
   @tool
   def func(a: int, b: int) -> int:
       return a + b

   func(1, 2)  # ✅
   ```

2. **Keyword Arguments**
   ```python
   func(a=1, b=2)  # ✅
   func(1, b=2)    # ✅
   ```

3. **Default Parameters**
   ```python
   @tool
   def func(a: int, b: int = 10) -> int:
       return a + b

   func(5)      # ✅ 15
   func(5, 20)  # ✅ 25
   ```

4. **Variable Arguments**
   ```python
   @tool
   def merge(*dicts: dict) -> dict:
       result = {}
       for d in dicts:
           result.update(d)
       return result

   merge({"a": 1}, {"b": 2})  # ✅ {"a": 1, "b": 2}
   ```

### Validation Errors

```python
@tool
def strict(x: int, y: int) -> int:
    return x + y

# Missing argument
strict(1)  # ❌ TypeError: Tool 'strict' called with invalid arguments

# Too many arguments
strict(1, 2, 3)  # ❌ TypeError: Tool 'strict' called with invalid arguments

# Invalid keyword
strict(1, z=2)  # ❌ TypeError: Tool 'strict' called with invalid arguments
```

---

## MCP Integration

Tools are automatically exposed via MCP when using `kagura mcp start`.

### Example

```python
# my_tools.py
from kagura import tool

@tool
def weather_lookup(city: str) -> dict:
    """Get current weather for a city"""
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny"
    }

@tool
def currency_convert(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert currency"""
    # Simplified example
    rates = {"USD": 1.0, "EUR": 0.85, "JPY": 110.0}
    return amount * rates[to_currency] / rates[from_currency]
```

Start MCP server:
```bash
kagura mcp start
```

Tools are now available to Claude Desktop via MCP protocol.

---

## Best Practices

### 1. Clear Documentation

```python
@tool
def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculate discounted price.

    Args:
        price: Original price
        discount_percent: Discount percentage (e.g., 15 for 15%)

    Returns:
        Final price after discount

    Example:
        >>> calculate_discount(100.0, 15.0)
        85.0
    """
    return price * (1 - discount_percent / 100)
```

### 2. Input Validation

```python
@tool
def withdraw_money(account_id: str, amount: float) -> dict:
    """Withdraw money from account"""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    if amount > 10000:
        raise ValueError("Exceeds daily limit")

    # Process withdrawal
    return {"success": True, "new_balance": 5000 - amount}
```

### 3. Type Hints

Always use type hints for better documentation and validation:

```python
@tool
def process_order(
    order_id: str,
    items: list[dict],
    shipping_address: dict,
    priority: bool = False
) -> dict:
    """Process customer order"""
    return {
        "order_id": order_id,
        "status": "processing",
        "estimated_delivery": "2025-10-15"
    }
```

### 4. Error Handling

```python
@tool
def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from database"""
    try:
        user = database.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}") from e
```

---

## See Also

- [Tools Tutorial](../tutorials/11-tools.md)
- [Agent Decorator](./agents.md)
- [MCP Integration](./mcp.md)
