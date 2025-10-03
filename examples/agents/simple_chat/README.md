# Simple Chat Agent

A basic conversational AI agent demonstrating the core `@agent` decorator.

## Overview

This example shows the simplest possible use case of Kagura AI 2.0:
- Single parameter (message)
- Simple string return type
- Jinja2 template in docstring
- No complex parsing needed

## Code

```python
from kagura import agent

@agent
async def chat(message: str) -> str:
    """You are a friendly AI assistant. Respond to: {{ message }}"""
    pass
```

## How It Works

1. **@agent Decorator**: Converts the async function into an AI agent
2. **Docstring Template**: Uses Jinja2 syntax `{{ message }}` to inject the parameter
3. **Type Hint**: Return type `str` tells the parser to expect a simple string response
4. **LLM Call**: The decorator handles calling the LLM with the rendered prompt
5. **Response**: Returns the LLM's response as a string

## Running the Example

```bash
python agent.py
```

## Expected Output

```
=== Simple Chat Agent Example ===

User: Hello! How are you?
Agent: Hello! I'm doing well, thank you for asking! How can I help you today?

User: What is the meaning of life?
Agent: That's a profound question! The meaning of life is subjective and varies from person to person...

User: Can you help me understand Python decorators?
Agent: Of course! Python decorators are functions that modify the behavior of other functions...
```

## Key Concepts

- **@agent decorator**: One-line agent creation
- **Jinja2 templates**: Dynamic prompt generation
- **Async/await**: Proper async handling
- **Type hints**: Automatic response parsing

## Next Steps

- See [data_extractor](../data_extractor/) for structured output with Pydantic
- See [code_generator](../code_generator/) for code execution
- See [workflow_example](../workflow_example/) for multi-step agents
