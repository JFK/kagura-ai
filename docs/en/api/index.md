# API Reference

Complete API documentation for Kagura AI 2.0.

## Core Components

### [@agent Decorator](agent.md)

Convert async functions into AI agents with automatic LLM integration.

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass
```

**Key Features:**
- One-line agent creation
- Type-based response parsing
- Jinja2 template support
- Multi-LLM support via LiteLLM

[Read more →](agent.md)

### [Code Executor](executor.md)

Safe Python code generation and execution.

```python
from kagura.agents import execute_code

result = await execute_code("Calculate factorial of 10")
print(result["result"])  # 3628800
```

**Key Features:**
- Natural language → Python code
- AST-based security validation
- Resource limits (timeout, memory)
- Safe module whitelist

[Read more →](executor.md)

### [CLI Commands](cli.md)

Command-line interface for Kagura AI.

```bash
# Start interactive REPL
kagura repl

# Check version
kagura version
```

**Key Features:**
- Interactive REPL for rapid prototyping
- Multi-line input support
- Syntax highlighting
- Command history

[Read more →](cli.md)

## Quick Links

- [Getting Started](../quickstart.md) - Build your first agent
- [Tutorials](../tutorials/01-basic-agent.md) - Step-by-step guides
- [Examples](../../examples/) - Code examples
- [FAQ](../faq.md) - Frequently asked questions

## API Overview

### Core Functions

| Function | Description |
|----------|-------------|
| `@agent` | Convert function to AI agent |
| `execute_code()` | Generate and execute Python code |

### Configuration

Agents can be configured with:
- `model`: LLM model to use
- `temperature`: Sampling temperature
- `max_tokens`: Maximum response tokens

Example:

```python
@agent(model="gpt-4o", temperature=0.5)
async def my_agent(query: str) -> str:
    '''Answer: {{ query }}'''
    pass
```

### Type Support

Supported return types:

| Type | Example | Description |
|------|---------|-------------|
| `str` | `-> str` | Plain text response |
| `int` | `-> int` | Integer value |
| `float` | `-> float` | Floating point number |
| `bool` | `-> bool` | Boolean value |
| `list[T]` | `-> list[str]` | List of items |
| `dict` | `-> dict` | Dictionary |
| `BaseModel` | `-> Person` | Pydantic model |
| `Optional[T]` | `-> Optional[str]` | Optional value |

### Template Syntax

Agent docstrings use Jinja2 syntax:

```python
@agent
async def greet(name: str, time: str = "morning") -> str:
    '''
    Good {{ time }}, {{ name }}!
    {% if time == "evening" %}
    Hope you had a great day.
    {% endif %}
    '''
    pass
```

Supported Jinja2 features:
- Variable interpolation: `{{ variable }}`
- Conditionals: `{% if condition %}`
- Loops: `{% for item in items %}`
- Filters: `{{ text|upper }}`

## Error Handling

All agents can raise these exceptions:

```python
from litellm import APIError
from pydantic import ValidationError

try:
    result = await my_agent("input")
except APIError as e:
    # LLM API error (auth, rate limit, etc.)
    print(f"API error: {e}")
except ValidationError as e:
    # Pydantic parsing error
    print(f"Validation error: {e}")
except Exception as e:
    # Other errors
    print(f"Unexpected error: {e}")
```

## Environment Variables

Kagura AI respects these environment variables:

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) API key |
| `GOOGLE_API_KEY` | Google (Gemini) API key |
| `AZURE_API_KEY` | Azure OpenAI API key |

Set them before running your agents:

```bash
export OPENAI_API_KEY="your-key-here"
python my_agent.py
```

## Best Practices

### 1. Use Type Hints

Always specify return types for automatic parsing:

```python
# Good
@agent
async def extract_keywords(text: str) -> list[str]:
    '''Extract keywords from: {{ text }}'''
    pass

# Less good
@agent
async def extract_keywords(text: str):  # No return type
    '''Extract keywords from: {{ text }}'''
    pass
```

### 2. Clear Instructions

Write explicit docstrings:

```python
# Good
@agent
async def summarize(text: str, max_words: int) -> str:
    '''Summarize the following text in {{ max_words }} words or less.

    Text: {{ text }}
    '''
    pass

# Less clear
@agent
async def summarize(text: str, max_words: int) -> str:
    '''Summarize {{ text }} in {{ max_words }} words'''
    pass
```

### 3. Pydantic Models

Use Pydantic for structured data:

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(ge=0, le=150, description="Age in years")
    email: str = Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")

@agent
async def extract_person(text: str) -> Person:
    '''Extract person information from: {{ text }}'''
    pass
```

### 4. Error Handling

Always handle errors in production:

```python
async def safe_agent_call():
    try:
        result = await my_agent("input")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        return {"success": False, "error": str(e)}
```

## Version Information

Check Kagura AI version:

```python
import kagura
print(kagura.__version__)  # "2.5.0"
```

Or via CLI:

```bash
kagura version
```

## Support

- [GitHub Issues](https://github.com/JFK/kagura-ai/issues)
- [Discussion Forum](https://github.com/JFK/kagura-ai/discussions)
- [Documentation](https://www.kagura-ai.com/)

## Related

- [Quick Start Guide](../quickstart.md)
- [Tutorials](../tutorials/01-basic-agent.md)
- [Examples](../../examples/)
- [FAQ](../faq.md)
