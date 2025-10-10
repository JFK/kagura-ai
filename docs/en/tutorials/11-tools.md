# Tools Tutorial

The **@tool decorator** allows you to convert regular Python functions into tools that can be used by AI agents or exposed via MCP.

## What are Tools?

Tools are **non-LLM functions** that provide deterministic, reliable functionality to your agents:

- **Calculations**: Math, tax, conversions
- **Data Access**: Database queries, API calls
- **File Operations**: Read, write, process files
- **System Operations**: Execute commands, manage resources

Unlike `@agent` (which calls an LLM), `@tool` functions execute **pure Python code**.

---

## Quick Start

### Basic Tool

```python
from kagura import tool

@tool
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    """Calculate tax amount"""
    return amount * rate

# Call directly
tax = calculate_tax(100.0, 0.15)  # 15.0
```

### Using Tools with Agents

```python
from kagura import agent, tool

@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get currency exchange rate (simplified)"""
    rates = {
        ("USD", "EUR"): 0.85,
        ("EUR", "USD"): 1.18,
        ("USD", "JPY"): 110.0,
    }
    return rates.get((from_currency, to_currency), 1.0)

@agent
async def currency_assistant(query: str) -> str:
    """
    Help with currency conversions.

    Available tools:
    - get_exchange_rate(from_currency, to_currency): Get exchange rate

    Query: {{ query }}
    """
    pass

# Use
result = await currency_assistant("Convert 100 USD to EUR")
# AI will suggest using get_exchange_rate("USD", "EUR") = 0.85
# Then calculate: 100 * 0.85 = 85 EUR
```

---

## Tool Features

### 1. Type Validation

Tools automatically validate argument types:

```python
@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# Valid
result = divide(10.0, 2.0)  # 5.0

# Invalid - raises TypeError
divide(10.0)  # Missing argument
divide(10.0, 2.0, 3.0)  # Too many arguments
```

### 2. Default Parameters

```python
@tool
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone"""
    return f"{greeting}, {name}!"

greet("Alice")  # "Hello, Alice!"
greet("Bob", "Hi")  # "Hi, Bob!"
greet(name="Charlie", greeting="Hey")  # "Hey, Charlie!"
```

### 3. Custom Names

```python
@tool(name="tax_calculator")
def calc_tax(amount: float) -> float:
    """Calculate 10% tax"""
    return amount * 0.1

# Registered as "tax_calculator" instead of "calc_tax"
```

### 4. Documentation

Docstrings are preserved for MCP integration:

```python
@tool
def search_database(query: str, limit: int = 10) -> list:
    """
    Search database for records matching query.

    Args:
        query: Search query string
        limit: Maximum number of results

    Returns:
        List of matching records
    """
    # Implementation here
    return []
```

---

## Tool Registry

All tools are automatically registered in the global `tool_registry`:

```python
from kagura.core.tool_registry import tool_registry

# List all tools
print(tool_registry.list_names())
# ['calculate_tax', 'get_exchange_rate', 'divide', ...]

# Get a specific tool
tax_tool = tool_registry.get("calculate_tax")
result = tax_tool(100.0, 0.15)  # 15.0

# Get all tools
all_tools = tool_registry.get_all()
for name, func in all_tools.items():
    print(f"{name}: {func.__doc__}")
```

---

## Examples

### Example 1: Calculator Tools

```python
from kagura import tool

@tool
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a"""
    return a - b

@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """Divide a by b"""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

# Use directly
print(add(5, 3))       # 8.0
print(multiply(4, 7))  # 28.0
```

### Example 2: String Processing Tools

```python
@tool
def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

@tool
def to_uppercase(text: str) -> str:
    """Convert text to uppercase"""
    return text.upper()

@tool
def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text"""
    import re
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)

# Use
text = "Contact: alice@example.com or bob@test.org"
emails = extract_emails(text)
print(emails)  # ['alice@example.com', 'bob@test.org']
```

### Example 3: Data Processing Tools

```python
@tool
def filter_dict(data: dict, keys: list[str]) -> dict:
    """Filter dictionary to only include specified keys"""
    return {k: v for k, v in data.items() if k in keys}

@tool
def merge_dicts(*dicts: dict) -> dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result

@tool
def get_nested_value(data: dict, path: str, default=None):
    """Get value from nested dictionary using dot notation"""
    keys = path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    return value

# Use
data = {"user": {"name": "Alice", "age": 30, "email": "alice@example.com"}}
name = get_nested_value(data, "user.name")  # "Alice"
```

### Example 4: File Tools

```python
import json
from pathlib import Path

@tool
def read_json_file(filepath: str) -> dict:
    """Read and parse JSON file"""
    with open(filepath) as f:
        return json.load(f)

@tool
def write_json_file(filepath: str, data: dict) -> None:
    """Write data to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

@tool
def list_files(directory: str, extension: str = "*") -> list[str]:
    """List files in directory with optional extension filter"""
    path = Path(directory)
    if extension == "*":
        return [str(f) for f in path.iterdir() if f.is_file()]
    return [str(f) for f in path.glob(f"*.{extension}")]

# Use
files = list_files(".", "py")  # All .py files in current directory
```

---

## Integration with MCP

Tools can be exposed via MCP for use in Claude Desktop:

```python
from kagura import tool

@tool
def weather_lookup(city: str) -> dict:
    """Get current weather for a city"""
    # Implementation
    return {
        "city": city,
        "temperature": 72,
        "condition": "sunny"
    }

# Automatically available in MCP
# Run: kagura mcp start
# Claude Desktop can now call weather_lookup
```

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

### 3. Error Handling

```python
@tool
def fetch_user_data(user_id: int) -> dict:
    """Fetch user data from database"""
    try:
        # Database query
        user = database.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        return user
    except DatabaseError as e:
        raise RuntimeError(f"Database error: {e}") from e
```

### 4. Type Hints

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
    # Implementation
    return {
        "order_id": order_id,
        "status": "processing",
        "estimated_delivery": "2025-10-15"
    }
```

---

## Troubleshooting

### Tool not found in registry

```python
from kagura.core.tool_registry import tool_registry

# Check if tool is registered
if "my_tool" not in tool_registry.list_names():
    print("Tool not found!")
    print("Available tools:", tool_registry.list_names())
```

### Type validation errors

```python
@tool
def strict_function(x: int) -> int:
    return x * 2

# This will raise TypeError
strict_function("not an int")  # Error!
strict_function(5, 10)  # Too many arguments!
```

### Tool name conflicts

```python
# This will raise ValueError
@tool
def duplicate():
    pass

@tool
def duplicate():  # Error: already registered!
    pass

# Solution: Use custom names
@tool(name="duplicate_v2")
def duplicate():
    pass
```

---

## Next Steps

- Learn about [Agent Routing](./09-agent-routing.md)
- Explore [MCP Integration](./06-mcp-integration.md)
- Try [Chat REPL](./10-chat-repl.md)

## Further Reading

- [Tools API Reference](../api/tools.md)
- [Tool Registry API](../api/tools.md#tool-registry)
- [MCP Tools Integration](../api/mcp.md#tools)
