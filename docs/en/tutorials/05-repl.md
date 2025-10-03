# Tutorial 5: Using the Interactive REPL

Learn how to use Kagura AI's interactive REPL for rapid prototyping and testing.

## What is the REPL?

REPL stands for Read-Eval-Print Loop - an interactive environment where you can:
- Define agents on the fly
- Test them immediately
- Iterate quickly without writing files
- Experiment with different prompts and models

## Starting the REPL

```bash
kagura repl
```

You'll see the welcome screen:

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

## Environment Setup

### API Keys with .env File

The REPL automatically loads environment variables from a `.env` file in your project directory. This is the recommended way to manage API keys:

**Step 1**: Create a `.env` file in your project root:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

**Step 2**: Start the REPL (the `.env` file is loaded automatically):

```bash
kagura repl
```

That's it! No need to manually export environment variables.

**Note**: Copy `.env.example` to `.env` to get started:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Command History

The REPL automatically saves your command history to `~/.kagura_history`. This means:
- **Up/Down arrows** work to navigate your previous commands
- **History persists** across REPL sessions
- **Up to 1000 commands** are saved

This makes it easy to:
- Rerun previous commands
- Edit and retry agent definitions
- Resume work from previous sessions

## Basic Usage

### Import and Define

```python
>>> from kagura import agent
>>>
>>> @agent
... async def hello(name: str) -> str:
...     '''Say hello to {{ name }}'''
...     pass
...
Agent 'hello' defined
```

### Call the Agent

```python
>>> await hello("World")
Hello, World! How can I help you today?
```

That's it! No files, no boilerplate - just define and run.

## REPL Commands

Commands start with `/`:

### /help - Show Help

```python
>>> /help
Available Commands:
  /help      - Show this help message
  /agents    - List all defined agents
  /exit      - Exit REPL
  /clear     - Clear screen
  /model     - Show or set default model
  /temp      - Show or set default temperature
```

### /agents - List Agents

```python
>>> /agents
Defined Agents:
  hello(name: str) -> str
  translate(text: str, lang: str) -> str
```

### /model - Change Model

```python
>>> /model
Current model: gpt-4o-mini

>>> /model gpt-4o
Model changed to: gpt-4o
```

### /temp - Change Temperature

```python
>>> /temp
Current temperature: 0.7

>>> /temp 1.2
Temperature changed to: 1.2
```

### /clear - Clear Screen

```python
>>> /clear
# Screen clears
```

### /exit - Exit REPL

```python
>>> /exit
Goodbye!
```

## Multi-line Input

The REPL automatically detects multi-line statements:

```python
>>> from pydantic import BaseModel
>>>
>>> class Person(BaseModel):
...     name: str
...     age: int
...     occupation: str
...
>>>
>>> @agent
... async def extract_person(text: str) -> Person:
...     '''Extract person info from: {{ text }}'''
...     pass
...
Agent 'extract_person' defined
```

## Practical Workflow

### 1. Quick Testing

Test ideas quickly:

```python
>>> @agent
... async def v1(text: str) -> str:
...     '''Summarize: {{ text }}'''
...     pass
...
>>> await v1("Long text here...")
Summary here...

>>> @agent
... async def v2(text: str) -> str:
...     '''Summarize in bullet points: {{ text }}'''
...     pass
...
>>> await v2("Long text here...")
- Point 1
- Point 2
```

### 2. Iterative Refinement

Refine your prompts:

```python
>>> @agent
... async def summarize_v1(text: str) -> str:
...     '''Summarize: {{ text }}'''
...     pass
...
>>> result1 = await summarize_v1("Long article...")
>>> # Not quite right, let's try again

>>> @agent
... async def summarize_v2(text: str) -> str:
...     '''Provide a concise summary in 2-3 sentences: {{ text }}'''
...     pass
...
>>> result2 = await summarize_v2("Long article...")
>>> # Better!
```

### 3. Debugging

Inspect results:

```python
>>> result = await extract_person("Alice is 30 years old and works as an engineer")
>>> print(result)
Person(name='Alice', age=30, occupation='engineer')

>>> print(type(result))
<class '__main__.Person'>

>>> print(result.model_dump())
{'name': 'Alice', 'age': 30, 'occupation': 'engineer'}
```

### 4. Composition

Chain agents together:

```python
>>> @agent
... async def extract_topic(text: str) -> str:
...     '''Extract the main topic from: {{ text }}'''
...     pass
...
>>> @agent
... async def elaborate(topic: str) -> str:
...     '''Elaborate on: {{ topic }}'''
...     pass
...
>>> topic = await extract_topic("Quantum computing is revolutionary...")
>>> await elaborate(topic)
Quantum computing is a revolutionary technology...
```

## Advanced Features

### Using Code Execution

```python
>>> from kagura.agents import execute_code
>>>
>>> result = await execute_code("Calculate fibonacci(15)")
>>> result["result"]
610
```

### Trying Different Models

```python
>>> @agent(model="gpt-4o")
... async def advanced(query: str) -> str:
...     '''Answer with deep analysis: {{ query }}'''
...     pass
...
>>> @agent(model="gpt-4o-mini")
... async def simple(query: str) -> str:
...     '''Answer briefly: {{ query }}'''
...     pass
...
```

### Custom Temperature

```python
>>> @agent(temperature=0.1)  # Very deterministic
... async def factual(query: str) -> str:
...     '''Provide factual answer: {{ query }}'''
...     pass
...
>>> @agent(temperature=1.5)  # More creative
... async def creative(topic: str) -> str:
...     '''Write a creative story about: {{ topic }}'''
...     pass
...
```

## Tips and Tricks

### 1. Use Variables

Store results for reuse:

```python
>>> text = "Long article text here..."
>>> summary = await summarize(text)
>>> keywords = await extract_keywords(summary)
```

### 2. Quick Imports

Import common modules at the start:

```python
>>> from kagura import agent
>>> from pydantic import BaseModel
>>> from typing import List, Optional
```

### 3. Test Error Handling

```python
>>> try:
...     result = await my_agent("test")
... except Exception as e:
...     print(f"Error: {e}")
```

### 4. Save Working Code

Once you have working code, copy it to a `.py` file:

```python
# From REPL:
>>> @agent
... async def working_agent(x: str) -> str:
...     '''Process {{ x }}'''
...     pass

# Copy to agent.py:
from kagura import agent

@agent
async def working_agent(x: str) -> str:
    '''Process {{ x }}'''
    pass
```

## Common Workflows

### Workflow 1: Prompt Engineering

```python
# Start REPL
$ kagura repl

# Test different prompts
>>> @agent
... async def v1(text: str) -> str:
...     '''{{ text }}'''
...     pass
>>> await v1("Summarize this")

>>> @agent
... async def v2(text: str) -> str:
...     '''Provide a detailed summary of: {{ text }}'''
...     pass
>>> await v2("Summarize this")

# Find the best prompt, save to file
```

### Workflow 2: Model Comparison

```python
>>> @agent(model="gpt-4o-mini")
... async def fast(q: str) -> str:
...     '''Answer: {{ q }}'''
...     pass

>>> @agent(model="gpt-4o")
... async def accurate(q: str) -> str:
...     '''Answer: {{ q }}'''
...     pass

>>> await fast("Explain quantum computing")
>>> await accurate("Explain quantum computing")
# Compare outputs
```

### Workflow 3: Data Extraction Testing

```python
>>> from pydantic import BaseModel
>>> from typing import List

>>> class Item(BaseModel):
...     name: str
...     price: float

>>> @agent
... async def extract_items(text: str) -> List[Item]:
...     '''Extract items and prices from: {{ text }}'''
...     pass

>>> test_text = "Apple $1.50, Banana $0.75"
>>> await extract_items(test_text)
[Item(name='Apple', price=1.5), Item(name='Banana', price=0.75)]
```

## Keyboard Shortcuts

- **↑/↓**: Navigate command history (persistent across sessions, saved to `~/.kagura_history`)
- **Tab**: Auto-complete (when available)
- **Ctrl+C**: Cancel current input
- **Ctrl+D**: Exit REPL (saves history on exit)

## Troubleshooting

### Import Errors

```python
>>> from kagura import agent
ModuleNotFoundError: No module named 'kagura'
```

**Solution**: Ensure Kagura AI is installed in the current environment:
```bash
pip install kagura-ai
```

### API Key Errors

```python
>>> await hello("test")
AuthenticationError: API key not found
```

**Solution 1 (Recommended)**: Create a `.env` file:
```bash
# Create .env file
echo "OPENAI_API_KEY=your-key-here" > .env
kagura repl
```

**Solution 2**: Export environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
kagura repl
```

### Memory Issues

If the REPL becomes slow:
- Exit and restart: `/exit`
- Clear large variables: `del big_variable`

## Best Practices

1. **Start Simple**: Begin with basic agents, then add complexity
2. **Test Incrementally**: Test each change before moving on
3. **Save Working Code**: Copy successful agents to files
4. **Use Variables**: Store reusable data in variables
5. **Clean Up**: Delete large variables when done

## Example Session

Complete example of a REPL session:

```python
$ kagura repl

>>> from kagura import agent
>>> from pydantic import BaseModel

>>> class Task(BaseModel):
...     title: str
...     priority: int

>>> @agent
... async def extract_task(text: str) -> Task:
...     '''Extract task from: {{ text }}'''
...     pass
...
Agent 'extract_task' defined

>>> task = await extract_task("Fix the login bug (high priority)")
>>> print(task)
Task(title='Fix the login bug', priority=3)

>>> @agent
... async def create_issue(task: Task) -> str:
...     '''Create a GitHub issue for task: {{ task.title }} (priority: {{ task.priority }})'''
...     pass
...
Agent 'create_issue' defined

>>> issue = await create_issue(task)
>>> print(issue)
GitHub Issue:
Title: Fix the login bug
Priority: High (3)
Description: This is a high-priority bug that needs immediate attention...

>>> /exit
Goodbye!
```

## Summary

You learned:
- ✓ How to start and use the REPL
- ✓ REPL commands (/help, /agents, /model, etc.)
- ✓ Multi-line input for complex definitions
- ✓ Practical workflows for testing and iteration
- ✓ Tips for efficient REPL usage

The REPL is your playground for experimentation. Use it to:
- Test ideas quickly
- Refine prompts
- Compare models
- Debug agents

Happy coding! 🎉

## Next Steps

- [API Reference: CLI](../api/cli.md) - Detailed CLI documentation
- [Examples](../../examples/) - More code examples
- [FAQ](../faq.md) - Common questions
