# Kagura AI

![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

**Production-Ready AI Agent Framework with Memory, Routing, and Multimodal RAG**

Kagura AI is a production-ready framework focused on simplicity and developer experience. Convert any Python function into an AI agent with a single decorator, and leverage advanced features like memory management, intelligent routing, multimodal RAG, and context compression.

---

## ✨ Features

### Core Framework
- **@agent Decorator**: One-line AI agent creation
- **@tool Decorator**: Convert Python functions into callable tools ⭐️ NEW
- **@workflow Decorator**: Multi-agent orchestration and workflows ⭐️ NEW
- **Jinja2 Templates**: Powerful prompt templating in docstrings
- **Type-based Parsing**: Automatic response parsing using type hints
- **Pydantic Models**: First-class support for structured outputs
- **Code Execution**: Safe Python code generation and execution
- **Interactive REPL**: `kagura repl` for rapid prototyping
- **Chat REPL**: `kagura chat` with preset agents (translate, summarize, review) ⭐️ NEW
- **Multi-LLM Support**: Works with OpenAI, Anthropic, Google, and more via [LiteLLM](https://github.com/BerriAI/litellm)

### Advanced Features
- **Memory Management**: Three-tier memory system (Context/Persistent/RAG) with ChromaDB for semantic search
- **Agent Routing**: Intelligent routing with Intent/Semantic/Memory-Aware strategies
- **Multimodal RAG**: Index and search images, PDFs, audio, video using Gemini API + ChromaDB
- **Web Integration**: Brave Search + DuckDuckGo + web scraping for real-time information
- **Context Compression**: Efficient token management for long conversations (RFC-024)
- **MCP Integration**: Use Kagura agents directly in Claude Desktop via Model Context Protocol
- **Shell Integration**: Secure shell command execution with Git automation
- **Custom Commands**: Define reusable AI tasks in Markdown files with YAML frontmatter
- **Hooks System**: Intercept and modify command execution with PreToolUse/PostToolUse hooks
- **Testing Framework**: Built-in testing utilities with semantic assertions and mocking
- **Observability**: Telemetry, cost tracking, and performance monitoring

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install kagura-ai

# With AI features (Memory, Routing, Context Compression)
pip install kagura-ai[ai]

# With Web & Multimodal (images, PDFs, audio, video, web search)
pip install kagura-ai[web]

# With OAuth2 authentication
pip install kagura-ai[auth]

# With all features (recommended)
pip install kagura-ai[full]
```

**See [Installation Guide](https://www.kagura-ai.com/en/installation/) for detailed preset options.**

### Basic Example

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass

# Run the agent
result = await hello("World")
print(result)  # "Hello, World!"
```

### Structured Output with Pydantic

```python
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

result = await extract_person("Alice is 30 years old and works as a software engineer")
print(f"{result.name}, {result.age}, {result.occupation}")
# Output: Alice, 30, software engineer
```

### Code Execution

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")
if result["success"]:
    print(result["result"])  # 3628800
```

### Interactive REPL

```bash
kagura repl
```

Available commands:
- `/help` - Show available commands
- `/agents` - List defined agents
- `/exit` - Exit REPL
- `/clear` - Clear screen

### MCP Integration (Claude Desktop)

Use Kagura agents directly in Claude Desktop:

```bash
# Start MCP server
kagura mcp start

# Configure Claude Desktop (macOS)
kagura mcp config claude
```

Then interact with your agents in Claude Desktop conversation!

### Memory Management

```python
from kagura import agent

@agent(enable_memory=True)
async def chat_with_memory(message: str) -> str:
    '''You are a helpful assistant. Remember our conversation.
    User says: {{ message }}'''
    pass

# Memory persists across calls
await chat_with_memory("My name is Alice")
await chat_with_memory("What's my name?")  # "Your name is Alice"
```

### Chat REPL

```bash
# Start interactive chat
kagura chat

# Use preset agents
/translate Hello World
/summarize <paste long text>
/review <paste code>
```

### Tool & Workflow Decorators

```python
from kagura import tool, workflow

@tool
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    '''Calculate tax amount'''
    return amount * rate

@workflow
async def shopping_workflow(items: list[str]) -> dict:
    '''Complete shopping workflow'''
    total = sum([get_price(item) for item in items])
    tax = calculate_tax(total)
    return {"total": total, "tax": tax, "grand_total": total + tax}
```

### Agent Routing

```python
from kagura.routing import SemanticRouter

router = SemanticRouter()
router.add_route("translation", translation_agent)
router.add_route("code_review", review_agent)

# Automatically selects the right agent
agent = await router.route("Translate this to Japanese")
result = await agent("Hello World")
```

### Custom Commands

Create `~/.kagura/commands/deploy.md`:

```markdown
---
name: deploy
description: Deploy application
parameters:
  env: string
---

# Task
Deploy to {{ env }} environment.

Current commit: !`git rev-parse HEAD`
```

Run:
```bash
kagura run deploy --param env=production
```

## 📚 Documentation

- [Full Documentation](https://www.kagura-ai.com/)
- [API Reference](https://www.kagura-ai.com/en/api/)
- [Examples](./examples/)
- [Contributing Guide](./CONTRIBUTING.md)

## 🎯 Recent Updates

Latest features:
- **Unified MCP Server**: All features via single Claude Desktop config (v2.5.4)
- **15 Built-in MCP Tools**: Memory, Web, File, Observability, Meta, Multimodal
- **Fast CLI Startup**: 98.7% faster (8.8s → 0.1s) with lazy loading (v2.5.3)
- **Context Compression**: Token counting and context window management
- **Memory-Aware Routing**: Intelligent routing with conversation context
- **Testing Framework**: AgentTestCase with semantic assertions
- **Observability**: Built-in telemetry and cost tracking
- **36 Comprehensive Examples**: Organized in 8 categories from basic to real-world applications

## 🎯 What's New in 2.0

Kagura AI 2.0 was a **complete redesign** from 1.x:

### Before (1.x)
```yaml
# agent.yml
type: atomic
llm:
  model: gpt-4
prompt:
  - language: en
    template: "You are a helpful assistant"
```

### After (2.0)
```python
@agent
async def assistant(query: str) -> str:
    '''You are a helpful assistant. Answer: {{ query }}'''
    pass
```

**Key Changes:**
- **Python-First**: No more YAML configuration
- **Simpler API**: One decorator instead of complex configs
- **Type Safety**: Full type hints and Pydantic support
- **Code Execution**: Built-in safe code generation and execution
- **Better DX**: Interactive REPL for rapid development

## 🔧 Core Concepts

### 1. Agent Decorator
Transform any async function into an AI agent:

```python
@agent
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass
```

### 2. Template Engine
Use Jinja2 templates in docstrings for dynamic prompts:

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
    pass
```

### 3. Type-based Parser
Automatic response parsing based on return type hints:

```python
@agent
async def extract_data(text: str) -> list[str]:
    '''Extract keywords from: {{ text }}'''
    pass
```

### 4. Code Executor
Safe Python code execution with security constraints:

```python
from kagura.core.executor import CodeExecutor

executor = CodeExecutor()
result = await executor.execute("""
import math
result = math.factorial(10)
""")
print(result.result)  # 3628800
```

## 🎨 Examples

### Basic Chat Agent
```python
from kagura import agent

@agent
async def chat(message: str) -> str:
    '''You are a friendly AI assistant. Respond to: {{ message }}'''
    pass

response = await chat("What is the meaning of life?")
print(response)
```

### Data Extraction
```python
from kagura import agent
from pydantic import BaseModel
from typing import List

class Task(BaseModel):
    title: str
    priority: int

class TaskList(BaseModel):
    tasks: List[Task]

@agent
async def extract_tasks(text: str) -> TaskList:
    '''Extract tasks from: {{ text }}'''
    pass

result = await extract_tasks("1. Fix bug (high priority), 2. Write docs (low priority)")
for task in result.tasks:
    print(f"{task.title} - Priority: {task.priority}")
```

### Multi-step Workflow
```python
from kagura import agent

@agent
async def plan(goal: str) -> list[str]:
    '''Break down this goal into steps: {{ goal }}'''
    pass

@agent
async def execute_step(step: str) -> str:
    '''Execute this step: {{ step }}'''
    pass

# Generate plan
steps = await plan("Build a web app")

# Execute each step
for step in steps:
    result = await execute_step(step)
    print(f"✓ {step}: {result}")
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --dev
```

Run tests:
```bash
pytest
```

Type checking:
```bash
pyright
```

## 📄 License

Apache License 2.0 - see [LICENSE](./LICENSE)

## 🙏 Acknowledgments

Kagura AI is named after the traditional Japanese performance art "Kagura (神楽)", embodying principles of harmony, connection, and creativity.

---

Built with ❤️ by the Kagura AI community
