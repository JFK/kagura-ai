# 01_basic - Basic Features

This directory contains examples demonstrating the fundamental features of Kagura AI 2.0.

## Overview

Learn the core concepts of Kagura AI:
- `@agent` decorator for converting functions to AI agents
- Jinja2 templates for prompt engineering
- Type hints and Pydantic models for structured outputs
- LLM configuration and model selection
- Safe Python code execution

## Examples

### 1. hello_world.py - Simplest Agent
**Demonstrates:**
- Minimal `@agent` decorator usage
- Jinja2 template in docstring
- Simple string return type

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    """Say hello to {{ name }} in a friendly way."""
    pass

result = await hello("World")
```

**Key Concepts:**
- Zero-boilerplate AI agent creation
- Template variables with `{{ }}`
- Async function execution

---

### 2. simple_chat.py - Conversational Agent
**Demonstrates:**
- Building a conversational agent
- Multi-turn interactions
- Different prompting styles

```python
@agent(model="gpt-4o-mini")
async def chatbot(message: str) -> str:
    """You are a friendly chatbot. Respond to: {{ message }}"""
    pass
```

**Key Concepts:**
- Model selection with `model` parameter
- Conversational prompt patterns
- Temperature and creativity control

---

### 3. pydantic_parsing.py - Structured Output
**Demonstrates:**
- Type hints with Pydantic models
- Automatic JSON parsing
- Structured data extraction

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    """Extract person information from: {{ text }}"""
    pass
```

**Key Concepts:**
- Return type annotations
- Pydantic model validation
- Automatic schema generation
- JSON parsing from LLM responses

---

### 4. config_usage.py - LLM Configuration
**Demonstrates:**
- Creating custom LLMConfig
- Reusing configuration across agents
- Advanced LLM parameters

```python
from kagura import agent, LLMConfig

config = LLMConfig(
    model="gpt-4o",
    temperature=0.3,
    max_tokens=1000
)

@agent(config=config)
async def precise_agent(query: str) -> str:
    """Answer precisely: {{ query }}"""
    pass
```

**Key Concepts:**
- `LLMConfig` for reusable settings
- Temperature control (0.0-1.0)
- Token limits and cost optimization
- Multi-agent consistency

---

### 5. code_execution.py - Safe Code Execution
**Demonstrates:**
- Using the built-in code execution tool
- Safe Python code execution
- Security constraints

```python
from kagura import agent
from kagura.commands.execute_code import execute_code

@agent(tools=[execute_code])
async def code_assistant(task: str) -> str:
    """
    Solve this task by writing Python code: {{ task }}

    Use the execute_code tool to run your solution.
    """
    pass
```

**Key Concepts:**
- Tool integration with `tools` parameter
- AST-based security validation
- Sandboxed execution
- No file I/O or network access

---

## Prerequisites

```bash
# Install Kagura AI
pip install kagura-ai

# Set your API key
export OPENAI_API_KEY="your-key-here"
```

## Running Examples

```bash
# Run any example
python hello_world.py
python simple_chat.py
python pydantic_parsing.py
python config_usage.py
python code_execution.py
```

## Learning Path

1. **Start here:** `hello_world.py` - Understand the basics
2. **Next:** `simple_chat.py` - Learn prompting
3. **Then:** `pydantic_parsing.py` - Master structured outputs
4. **Advanced:** `config_usage.py` - Optimize configuration
5. **Power user:** `code_execution.py` - Integrate tools

## Common Patterns

### Basic Agent Template
```python
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    """Process {{ input }} and provide output."""
    pass

# Usage
result = await my_agent("test input")
print(result)
```

### Structured Output Template
```python
from kagura import agent
from pydantic import BaseModel

class MyOutput(BaseModel):
    field1: str
    field2: int

@agent
async def my_agent(input: str) -> MyOutput:
    """Extract structured data from: {{ input }}"""
    pass

# Usage
result = await my_agent("some text")
print(result.field1, result.field2)
```

### With Configuration
```python
from kagura import agent, LLMConfig

config = LLMConfig(model="gpt-4o-mini", temperature=0.7)

@agent(config=config)
async def my_agent(input: str) -> str:
    """Process: {{ input }}"""
    pass
```

## Tips & Best Practices

### 1. Prompt Engineering
✅ **Good:**
```python
"""You are an expert {{ domain }} assistant.

Task: {{ task }}

Provide a detailed, accurate response."""
```

❌ **Bad:**
```python
"""{{ task }}"""  # Too vague
```

### 2. Temperature Selection
- **0.0-0.3:** Deterministic tasks (parsing, classification, math)
- **0.4-0.7:** Balanced creativity (general chat, Q&A)
- **0.8-1.0:** Creative tasks (story writing, brainstorming)

### 3. Model Selection
- **gpt-4o-mini:** Fast, cost-effective (recommended for most tasks)
- **gpt-4o:** More capable, higher quality
- **claude-3-5-sonnet:** Excellent for coding and analysis
- **gemini-pro:** Good for multimodal tasks

### 4. Error Handling
```python
try:
    result = await my_agent("input")
except Exception as e:
    print(f"Agent error: {e}")
    # Handle gracefully
```

### 5. Type Hints Are Important
```python
# ✅ Good: Clear types
async def agent(text: str) -> Person:
    pass

# ❌ Bad: No types
async def agent(text):  # Unclear what to expect
    pass
```

## Next Steps

After mastering these basics, explore:
- [02_memory](../02_memory/) - Memory management
- [03_routing](../03_routing/) - Agent routing
- [07_presets](../07_presets/) - Pre-configured agents
- [08_real_world](../08_real_world/) - Production examples

## Troubleshooting

### Issue: "API key not found"
**Solution:** Set your API key in environment:
```bash
export OPENAI_API_KEY="sk-..."
```

### Issue: "Model not found"
**Solution:** Check available models with LiteLLM:
```python
from litellm import get_supported_models
print(get_supported_models())
```

### Issue: Pydantic parsing fails
**Solution:** Add more specific instructions in prompt:
```python
"""Extract data and return as JSON with these exact fields: name, age, occupation"""
```

### Issue: Agent responses are inconsistent
**Solution:** Lower temperature for more deterministic outputs:
```python
@agent(temperature=0.1)
async def consistent_agent(input: str) -> str:
    pass
```

## Documentation

- [API Reference - @agent decorator](../../docs/en/api/agent.md)
- [Configuration Guide](../../docs/en/api/config.md)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)

---

**Ready to build your first agent? Start with `hello_world.py`!**
