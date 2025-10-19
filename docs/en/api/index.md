# API Reference

Complete API documentation for Kagura AI SDK.

---

## Core Decorators

### [@agent](agent.md)

Convert async functions into AI agents.

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
```

**Features:**
- One-line agent creation
- Type-based response parsing
- Jinja2 template support
- Multi-LLM support

[Full documentation →](agent.md)

---

### [@tool](tools.md)

Turn Python functions into agent tools.

```python
from kagura import tool

@tool
async def search_db(query: str) -> list[dict]:
    '''Search database'''
    return db.query(query)
```

**Features:**
- Auto-registration to tool_registry
- Type validation
- Docstring-based descriptions

[Full documentation →](tools.md)

---

### [@workflow](workflows.md)

Orchestrate multi-agent workflows.

```python
from kagura import workflow

@workflow.chain
async def pipeline(data: str):
    step1 = await agent1(data)
    step2 = await agent2(step1)
    return step2
```

**Features:**
- Sequential chains
- Parallel execution
- Stateful workflows

[Full documentation →](workflows.md)

---

## Features

### [Memory System](memory.md)

3-tier memory management for context-aware agents.

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''Remember conversation: {{ message }}'''
```

**Types:**
- Context Memory: Current conversation
- Persistent Memory: Long-term storage
- RAG Memory: Semantic search

[Full documentation →](memory.md)

---

### [Agent Builder](builder.md)

Fluent API for building complex agents.

```python
from kagura.builder import AgentBuilder

agent = (
    AgentBuilder()
    .with_memory()
    .with_tools(["web_search"])
    .build()
)
```

[Full documentation →](builder.md)

---

### [Testing Framework](testing.md)

Built-in testing utilities for AI agents.

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_sentiment(self):
        result = await analyzer("I love this!")
        self.assert_semantic_match(result, "positive")
```

[Full documentation →](testing.md)

---

## Integrations

### [Chat Session](chat.md)

Interactive chat interface (bonus feature).

```python
from kagura.chat import ChatSession

session = ChatSession()
await session.run()
```

[Full documentation →](chat.md)

---

### [MCP Integration](mcp.md)

Use agents in Claude Desktop via Model Context Protocol.

```bash
kagura mcp serve
```

[Full documentation →](mcp.md)

---

### [Authentication](auth.md)

OAuth2 authentication support (advanced).

```python
from kagura.auth import OAuth2Manager

oauth = OAuth2Manager(provider="google")
await oauth.authenticate()
```

[Full documentation →](auth.md)

---

## Advanced

### [Code Executor](executor.md)

Deep dive into code execution engine.

[Full documentation →](executor.md)

---

### [Context Compression](compression.md)

Token management for long conversations.

```python
@agent(enable_compression=True)
async def assistant(message: str) -> str:
    '''{{ message }}'''
```

[Full documentation →](compression.md)

---

### [Observability](observability.md)

Cost tracking and performance monitoring.

```bash
kagura monitor stats
```

[Full documentation →](observability.md)

---

## Quick Reference

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google API key |
| `BRAVE_SEARCH_API_KEY` | Web search (optional) |

### Type Support

| Return Type | Example |
|-------------|---------|
| `str` | `-> str` |
| `int`, `float`, `bool` | `-> int` |
| `list[T]` | `-> list[str]` |
| `dict` | `-> dict` |
| `BaseModel` | `-> Person` |
| `Optional[T]` | `-> Optional[str]` |

---

## Next Steps

- [Quick Start](../quickstart.md) - Get started in 5 minutes
- [SDK Guide](../../sdk-guide.md) - Complete SDK guide
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - Code examples
