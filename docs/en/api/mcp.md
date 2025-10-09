# MCP API Reference

## Overview

The MCP (Model Context Protocol) module enables Kagura agents to be exposed as MCP tools, allowing integration with Claude Desktop, Claude Code, Cline, and other MCP-compatible clients.

## Module: `kagura.mcp`

### `create_mcp_server(name: str = "kagura-ai") -> Server`

Creates an MCP server instance that exposes registered Kagura agents as tools.

**Parameters:**
- `name` (str, optional): Server name. Defaults to "kagura-ai".

**Returns:**
- `Server`: Configured MCP server instance

**Example:**
```python
from kagura.mcp import create_mcp_server

server = create_mcp_server("my-server")
```

---

## Module: `kagura.mcp.schema`

### `generate_json_schema(func: Callable) -> dict`

Generates JSON Schema from a Python function signature.

**Parameters:**
- `func` (Callable): Function to generate schema for

**Returns:**
- `dict`: JSON Schema with `type`, `properties`, and optionally `required`

**Example:**
```python
from kagura.mcp.schema import generate_json_schema

def my_func(name: str, age: int = 18) -> str:
    """Sample function

    name: Person's name
    age: Person's age
    """
    pass

schema = generate_json_schema(my_func)
# {
#     "type": "object",
#     "properties": {
#         "name": {"type": "string", "description": "Person's name"},
#         "age": {"type": "integer", "description": "Person's age"}
#     },
#     "required": ["name"]
# }
```

### `python_type_to_json_schema(py_type: type) -> dict`

Converts a Python type to JSON Schema format.

**Parameters:**
- `py_type` (type): Python type annotation

**Returns:**
- `dict`: JSON Schema representation

**Supported Types:**
- Basic: `str`, `int`, `float`, `bool`
- Collections: `list[T]`, `dict[K, V]`
- Optional: `T | None`, `Optional[T]`
- Pydantic: `BaseModel` subclasses

**Example:**
```python
from kagura.mcp.schema import python_type_to_json_schema

# Basic types
python_type_to_json_schema(str)
# {"type": "string"}

# Lists
python_type_to_json_schema(list[int])
# {"type": "array", "items": {"type": "integer"}}

# Dicts
python_type_to_json_schema(dict[str, float])
# {"type": "object", "additionalProperties": {"type": "number"}}

# Optional
python_type_to_json_schema(str | None)
# {"type": ["string", "null"]}
```

---

## Module: `kagura.core.registry`

### `class AgentRegistry`

Global registry for all Kagura agents.

#### Methods

##### `register(name: str, func: Callable) -> None`

Register an agent.

**Parameters:**
- `name` (str): Agent name (must be unique)
- `func` (Callable): Agent function

**Raises:**
- `ValueError`: If agent name is already registered

**Example:**
```python
from kagura.core.registry import agent_registry

def my_agent():
    pass

agent_registry.register("my_agent", my_agent)
```

##### `get(name: str) -> Callable | None`

Get agent by name.

**Parameters:**
- `name` (str): Agent name

**Returns:**
- `Callable | None`: Agent function, or None if not found

**Example:**
```python
agent_func = agent_registry.get("my_agent")
if agent_func:
    result = await agent_func()
```

##### `get_all() -> dict[str, Callable]`

Get all registered agents.

**Returns:**
- `dict[str, Callable]`: Dictionary of agent_name -> agent_function

**Example:**
```python
agents = agent_registry.get_all()
for name, func in agents.items():
    print(f"Agent: {name}")
```

##### `list_names() -> list[str]`

List all agent names.

**Returns:**
- `list[str]`: List of agent names

**Example:**
```python
names = agent_registry.list_names()
print(f"Registered agents: {', '.join(names)}")
```

##### `unregister(name: str) -> None`

Unregister an agent.

**Parameters:**
- `name` (str): Agent name to remove

**Raises:**
- `KeyError`: If agent name is not registered

##### `clear() -> None`

Clear all agents from registry.

##### `auto_discover(module_path: str) -> None`

Auto-discover agents in a module.

**Parameters:**
- `module_path` (str): Python module path (e.g., "my_package.agents")

**Raises:**
- `ValueError`: If module is not found

**Example:**
```python
# Discover all agents in a module
agent_registry.auto_discover("my_package.agents")

# All @agent decorated functions in the module are now registered
```

---

### Global Instance: `agent_registry`

A global `AgentRegistry` instance is available for use:

```python
from kagura.core.registry import agent_registry

# Agents decorated with @agent are automatically registered here
```

---

## CLI Commands

### `kagura mcp serve`

Start MCP server using stdio transport.

**Usage:**
```bash
kagura mcp serve [OPTIONS]
```

**Options:**
- `--name TEXT`: Server name (default: "kagura-ai")

**Example:**
```bash
# Start server
kagura mcp serve

# Custom server name
kagura mcp serve --name my-server

# Verbose logging
kagura -v mcp serve
```

---

### `kagura mcp list`

List all registered agents.

**Usage:**
```bash
kagura mcp list
```

**Output:**
```
Registered agents (3):

  • analyze_code
    Analyze code quality and suggest improvements

  • review_code
    Review code and provide feedback

  • generate_tests
    Generate unit tests for the code
```

---

## Agent Metadata

Agents decorated with `@agent` have special attributes for MCP integration:

### `_is_agent: bool`

Flag indicating this is a Kagura agent.

```python
from kagura import agent

@agent
async def my_agent():
    pass

print(my_agent._is_agent)  # True
```

### `_agent_config: LLMConfig`

LLM configuration for the agent.

```python
print(my_agent._agent_config.model)  # "gpt-4o-mini"
print(my_agent._agent_config.temperature)  # 0.7
```

### `_agent_template: str`

Jinja2 template extracted from docstring.

```python
@agent
async def greet(name: str):
    """Say hello to {{ name }}"""
    pass

print(greet._agent_template)  # "Say hello to {{ name }}"
```

---

## MCP Tool Naming

Agents are exposed to MCP clients with the `kagura_` prefix:

| Agent Function Name | MCP Tool Name |
|---------------------|---------------|
| `analyze_code` | `kagura_analyze_code` |
| `review_code` | `kagura_review_code` |
| `translate` | `kagura_translate` |

This prefix prevents naming conflicts with other MCP tools.

---

## Type Conversion Table

### Python → JSON Schema

| Python Type | JSON Schema |
|-------------|-------------|
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `bool` | `{"type": "boolean"}` |
| `list[T]` | `{"type": "array", "items": {...}}` |
| `dict[str, T]` | `{"type": "object", "additionalProperties": {...}}` |
| `T \| None` | `{"type": ["T", "null"]}` |
| `BaseModel` | Pydantic's `model_json_schema()` |

---

## Complete Example

```python
from kagura import agent
from kagura.core.registry import agent_registry
from kagura.mcp import create_mcp_server
from kagura.mcp.schema import generate_json_schema

# Define agent
@agent
async def analyze_sentiment(text: str, detailed: bool = False) -> dict:
    """
    Analyze sentiment of text

    text: Text to analyze
    detailed: Include detailed breakdown
    """
    pass

# Agent is automatically registered
print(agent_registry.get("analyze_sentiment"))  # <function ...>

# Generate schema
schema = generate_json_schema(analyze_sentiment)
print(schema)
# {
#     "type": "object",
#     "properties": {
#         "text": {"type": "string", "description": "Text to analyze"},
#         "detailed": {"type": "boolean", "description": "Include detailed breakdown"}
#     },
#     "required": ["text"]
# }

# Create MCP server
server = create_mcp_server()

# Server exposes agent as "kagura_analyze_sentiment" tool
```

---

## See Also

- [MCP Integration Tutorial](../tutorials/06-mcp-integration.md)
- [CLI Reference](cli.md)
- [Agent Decorator](agent.md)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
