# CLI Commands

Kagura AI 2.0 provides a command-line interface for version checking, running agents, and interactive development.

## Overview

The CLI is built with [Click](https://click.palletsprojects.com/) and provides:
- Version information
- Interactive REPL for rapid prototyping
- Agent file execution (future)

## Installation

The CLI is automatically installed with Kagura AI:

```bash
pip install kagura-ai
```

Verify installation:

```bash
kagura --version
```

## Commands

### kagura

Main command group.

```bash
kagura [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--help`: Show help message
- `--version`: Show version information

### kagura version

Display Kagura AI version information.

```bash
kagura version
```

**Output:**
```
Kagura AI v2.0.0-alpha.1
```

### kagura repl

Start an interactive REPL (Read-Eval-Print Loop) for rapid agent prototyping.

```bash
kagura repl [OPTIONS]
```

**Options:**
- `--model TEXT`: Default LLM model to use (default: `gpt-4o-mini`)
- `--temperature FLOAT`: Default temperature (default: `0.7`)
- `--help`: Show help message

**Example:**
```bash
# Start REPL with default settings
kagura repl

# Start with custom model
kagura repl --model gpt-4o

# Start with higher temperature
kagura repl --temperature 1.0
```

## Interactive REPL

The REPL provides an interactive Python environment optimized for AI agent development.

### Starting the REPL

```bash
kagura repl
```

**Welcome screen:**
```
╭──────────────────────────────────────╮
│ Kagura AI REPL                       │
│ Python-First AI Agent Framework      │
│                                      │
│ Type /help for commands, /exit to    │
│ quit                                 │
╰──────────────────────────────────────╯

>>>
```

### REPL Commands

Commands start with `/` and provide special functionality:

#### /help

Show available commands and usage information.

```
>>> /help
```

**Output:**
```
Available Commands:
  /help      - Show this help message
  /agents    - List all defined agents
  /exit      - Exit REPL
  /clear     - Clear screen
  /model     - Show or set default model
  /temp      - Show or set default temperature
```

#### /agents

List all agents defined in the current session.

```
>>> /agents
```

**Output:**
```
Defined Agents:
  hello(name: str) -> str
  translate(text: str, lang: str) -> str
  extract_person(text: str) -> Person
```

#### /exit

Exit the REPL.

```
>>> /exit
```

**Output:**
```
Goodbye!
```

#### /clear

Clear the terminal screen.

```
>>> /clear
```

#### /model

Show or set the default model for new agents.

```
>>> /model
Current model: gpt-4o-mini

>>> /model gpt-4o
Model changed to: gpt-4o
```

#### /temp

Show or set the default temperature.

```
>>> /temp
Current temperature: 0.7

>>> /temp 1.0
Temperature changed to: 1.0
```

### Defining Agents in REPL

Use Python syntax to define agents:

```python
>>> from kagura import agent
>>>
>>> @agent
... async def hello(name: str) -> str:
...     '''Say hello to {{ name }}'''
...     pass
...
Agent 'hello' defined

>>> await hello("World")
Hello, World! How can I help you today?
```

### Multi-line Input

The REPL supports multi-line input for complex definitions:

```python
>>> from pydantic import BaseModel
>>>
>>> class Person(BaseModel):
...     name: str
...     age: int
...
>>>
>>> @agent
... async def extract_person(text: str) -> Person:
...     '''Extract person info from: {{ text }}'''
...     pass
...
Agent 'extract_person' defined

>>> result = await extract_person("Alice is 30 years old")
>>> result.name
Alice
>>> result.age
30
```

### Importing Modules

Import any Python module as usual:

```python
>>> from kagura import agent
>>> from pydantic import BaseModel
>>> from typing import List
>>> import json
```

### Executing Code

Execute arbitrary Python code:

```python
>>> x = 10
>>> y = 20
>>> x + y
30

>>> [i**2 for i in range(5)]
[0, 1, 4, 9, 16]
```

### Using Code Execution

```python
>>> from kagura.agents import execute_code
>>>
>>> result = await execute_code("Calculate fibonacci(10)")
>>> result["result"]
55
```

## REPL Features

### Syntax Highlighting

Code is syntax-highlighted using [Pygments](https://pygments.org/) for better readability.

### Command History

Use arrow keys to navigate command history:
- ↑ (Up): Previous command
- ↓ (Down): Next command

### Auto-completion

Tab completion for:
- Python keywords
- Variable names
- Function names
- Module names

### Error Handling

Errors are displayed with helpful messages:

```python
>>> await hello()
Error: hello() missing 1 required positional argument: 'name'

>>> result = await extract_person("invalid")
Error: Validation error - could not parse response
```

## Examples

### Example 1: Simple Agent

```bash
$ kagura repl
>>> from kagura import agent
>>>
>>> @agent
... async def sentiment(text: str) -> str:
...     '''Analyze sentiment of: {{ text }}'''
...     pass
...
>>> await sentiment("I love this product!")
The sentiment is overwhelmingly positive...
```

### Example 2: Data Extraction

```bash
$ kagura repl
>>> from kagura import agent
>>> from pydantic import BaseModel
>>> from typing import List
>>>
>>> class Task(BaseModel):
...     title: str
...     priority: int
...
>>> @agent
... async def extract_tasks(text: str) -> List[Task]:
...     '''Extract tasks from: {{ text }}'''
...     pass
...
>>> tasks = await extract_tasks("1. Fix bug (high), 2. Write docs (low)")
>>> for task in tasks:
...     print(f"{task.title}: Priority {task.priority}")
...
Fix bug: Priority 3
Write docs: Priority 1
```

### Example 3: Code Generation

```bash
$ kagura repl --model gpt-4o
>>> from kagura.agents import execute_code
>>>
>>> result = await execute_code("Calculate prime numbers up to 20")
>>> result["result"]
[2, 3, 5, 7, 11, 13, 17, 19]
```

### Example 4: Agent Composition

```bash
$ kagura repl
>>> from kagura import agent
>>>
>>> @agent
... async def summarize(text: str) -> str:
...     '''Summarize in one sentence: {{ text }}'''
...     pass
...
>>> @agent
... async def translate(text: str, lang: str) -> str:
...     '''Translate to {{ lang }}: {{ text }}'''
...     pass
...
>>> text = "Long article text here..."
>>> summary = await summarize(text)
>>> japanese = await translate(summary, "Japanese")
>>> print(japanese)
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google API key

Set before starting REPL:

```bash
export OPENAI_API_KEY="your-key-here"
kagura repl
```

### Model Selection

Use different models for different tasks:

```bash
# Fast, cheap model for simple tasks
kagura repl --model gpt-4o-mini

# Powerful model for complex reasoning
kagura repl --model gpt-4o

# Claude for long context
kagura repl --model claude-3-5-sonnet-20241022

# Local model with Ollama
kagura repl --model ollama/llama3.2
```

## Tips and Tricks

### 1. Quick Testing

Use REPL for quick agent testing:

```python
>>> @agent
... async def test(x: str) -> str:
...     '''{{ x }}'''
...     pass
...
>>> await test("Is this working?")
```

### 2. Iterative Development

Refine prompts interactively:

```python
>>> @agent
... async def v1(text: str) -> str:
...     '''Summarize: {{ text }}'''
...     pass
...
>>> @agent
... async def v2(text: str) -> str:
...     '''Summarize in technical terms: {{ text }}'''
...     pass
...
>>> await v1(text)  # Try first version
>>> await v2(text)  # Try improved version
```

### 3. Debugging

Print intermediate results:

```python
>>> result = await my_agent("test")
>>> print(result)
>>> print(type(result))
>>> print(result.model_dump())  # For Pydantic models
```

### 4. Saving Work

Copy working code from REPL to a `.py` file:

```python
# In REPL - test and refine
>>> @agent
... async def my_agent(x: str) -> str:
...     '''Process {{ x }}'''
...     pass

# Then save to agent.py:
# from kagura import agent
#
# @agent
# async def my_agent(x: str) -> str:
#     '''Process {{ x }}'''
#     pass
```

## Troubleshooting

### REPL Won't Start

```bash
$ kagura repl
Error: 'kagura' command not found
```

**Solution**: Ensure Kagura AI is installed and in your PATH:
```bash
pip install kagura-ai
which kagura  # Should show path to kagura command
```

### Import Errors

```python
>>> from kagura import agent
ModuleNotFoundError: No module named 'kagura'
```

**Solution**: Check your Python environment:
```bash
python --version  # Should be 3.11+
pip list | grep kagura
```

### API Key Errors

```python
>>> await hello("test")
AuthenticationError: API key not found
```

**Solution**: Set your API key:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Memory Issues

If REPL becomes slow or unresponsive:

1. Exit and restart: `/exit`
2. Clear variables: `del large_variable`
3. Use `/clear` to clear screen

## Related

- [@agent Decorator](agent.md) - Creating agents
- [Quick Start](../quickstart.md) - Getting started
- [REPL Tutorial](../tutorials/05-repl.md) - Detailed REPL guide
