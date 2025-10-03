# Quick Start

Get started with Kagura AI 2.0 in 5 minutes.

## Installation

```bash
pip install kagura-ai
```

or with uv:

```bash
uv add kagura-ai
```

## Set API Key

Kagura AI uses LiteLLM, which supports multiple LLM providers. Set your API key:

```bash
export OPENAI_API_KEY="your-key-here"
```

## Your First Agent

Create a simple conversational agent:

```python
# chat.py
from kagura import agent

@agent
async def chat(message: str) -> str:
    '''You are a friendly AI assistant. Respond to: {{ message }}'''
    pass

# Run
if __name__ == "__main__":
    import asyncio

    async def main():
        response = await chat("Hello! How are you?")
        print(response)

    asyncio.run(main())
```

Run it:
```bash
python chat.py
```

**Output:**
```
Hello! I'm doing well, thank you for asking! How can I help you today?
```

## Structured Output with Pydantic

Extract structured data using Pydantic models:

```python
# extract.py
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''Extract person information from: {{ text }}'''
    pass

# Use it
if __name__ == "__main__":
    import asyncio

    async def main():
        result = await extract_person(
            "Alice is 30 years old and works as a software engineer"
        )
        print(f"Name: {result.name}")
        print(f"Age: {result.age}")
        print(f"Occupation: {result.occupation}")

    asyncio.run(main())
```

**Output:**
```
Name: Alice
Age: 30
Occupation: software engineer
```

## Multiple Parameters

Use multiple parameters in your templates:

```python
from kagura import agent

@agent
async def translator(text: str, target_lang: str = "ja") -> str:
    '''Translate to {{ target_lang }}: {{ text }}'''
    pass

# Use with default
result = await translator("Hello, world!")
# Output: "こんにちは、世界！"

# Use with custom language
result = await translator("Hello, world!", target_lang="fr")
# Output: "Bonjour, le monde!"
```

## Code Execution

Generate and execute Python code:

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")

if result["success"]:
    print(f"Code:\n{result['code']}\n")
    print(f"Result: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

**Output:**
```python
Code:
import math
result = math.factorial(10)

Result: 3628800
```

## Interactive REPL

Try the interactive REPL for rapid prototyping:

```bash
kagura repl
```

Available commands:
- `/help` - Show available commands
- `/agents` - List defined agents
- `/exit` - Exit REPL
- `/clear` - Clear screen

Example REPL session:

```
╭──────────────────────────────────────╮
│ Kagura AI REPL                       │
│ Python-First AI Agent Framework      │
│                                      │
│ Type /help for commands, /exit to    │
│ quit                                 │
╰──────────────────────────────────────╯

>>> @agent
... async def hello(name: str) -> str:
...     '''Say hello to {{ name }}'''
...     pass
...

>>> await hello("World")
Hello, World!

>>> /exit
Goodbye!
```

## List Operations

Return lists from agents:

```python
@agent
async def extract_keywords(text: str) -> list[str]:
    '''Extract keywords from: {{ text }}'''
    pass

keywords = await extract_keywords(
    "Python is a programming language used for AI and web development"
)
print(keywords)
# ['Python', 'programming language', 'AI', 'web development']
```

## Complex Data Structures

Work with nested Pydantic models:

```python
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    title: str
    priority: int
    completed: bool

class Project(BaseModel):
    name: str
    tasks: List[Task]

@agent
async def plan_project(goal: str) -> Project:
    '''Create a project plan for: {{ goal }}'''
    pass

project = await plan_project("Build a web application")
print(f"Project: {project.name}")
for task in project.tasks:
    status = "✓" if task.completed else "○"
    print(f"{status} [{task.priority}] {task.title}")
```

## Next Steps

- [API Reference](api/agent.md) - Detailed API documentation
- [Examples](../../examples/) - More examples and patterns
- [Code Executor](api/executor.md) - Deep dive into code execution
- [REPL Guide](tutorials/05-repl.md) - Advanced REPL usage
