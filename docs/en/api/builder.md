# AgentBuilder API

Fluent API for building agents with integrated features like memory, tools, and hooks.

## Overview

`AgentBuilder` provides a declarative, method-chaining interface for creating complex agents. Instead of manually wiring together components, you specify what features you want, and the builder handles the integration.

**Key Features:**
- Fluent API with method chaining
- Memory configuration (working, persistent, RAG)
- Tool integration
- Pre/post execution hooks
- LLM parameter configuration
- Agent routing

## Class: AgentBuilder

```python
from kagura import AgentBuilder

builder = AgentBuilder(name="my_agent")
```

### Constructor

```python
def __init__(self, name: str) -> None
```

**Parameters:**
- **name** (`str`, required): Agent name used for identification and logging

**Returns:** `AgentBuilder` instance

**Example:**
```python
builder = AgentBuilder("customer_support_bot")
```

---

## Methods

### with_model()

Set the LLM model to use.

```python
def with_model(self, model: str) -> AgentBuilder
```

**Parameters:**
- **model** (`str`): Model identifier (e.g., `"gpt-4o-mini"`, `"claude-3-5-sonnet-20241022"`)

**Returns:** Self for method chaining

**Supported Models:**
- OpenAI: `"gpt-4o"`, `"gpt-4o-mini"`, `"gpt-3.5-turbo"`
- Anthropic: `"claude-3-5-sonnet-20241022"`, `"claude-3-haiku-20240307"`
- Google: `"gemini/gemini-pro"`, `"gemini/gemini-1.5-flash"`
- Ollama: `"ollama/llama3.2"`, `"ollama/gemma2"`

**Example:**
```python
agent = (
    AgentBuilder("translator")
    .with_model("gpt-4o-mini")
    .build()
)
```

---

### with_memory()

Configure the memory system.

```python
def with_memory(
    self,
    type: str = "working",
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    enable_rag: bool = False,
) -> AgentBuilder
```

**Parameters:**
- **type** (`str`, default: `"working"`): Memory type
  - `"working"`: In-memory storage (fast, temporary)
  - `"context"`: Conversation context for LLM
  - `"persistent"`: SQLite storage (survives restarts)
  - `"rag"`: Vector-based semantic search
- **persist_dir** (`Optional[Path]`, default: `None`): Directory for persistent storage
- **max_messages** (`int`, default: `100`): Maximum messages to store
- **enable_rag** (`bool`, default: `False`): Enable RAG (requires ChromaDB)

**Returns:** Self for method chaining

**Example:**
```python
# In-memory working memory
agent = (
    AgentBuilder("chatbot")
    .with_memory(type="working", max_messages=50)
    .build()
)

# Persistent memory with RAG
agent = (
    AgentBuilder("knowledge_bot")
    .with_memory(
        type="persistent",
        persist_dir=Path.home() / ".kagura" / "memory",
        enable_rag=True,
        max_messages=200
    )
    .build()
)
```

---

### with_routing()

Configure agent routing strategies.

```python
def with_routing(
    self,
    strategy: str = "semantic",
    routes: Optional[dict] = None,
) -> AgentBuilder
```

**Parameters:**
- **strategy** (`str`, default: `"semantic"`): Routing strategy
  - `"keyword"`: Keyword-based routing
  - `"llm"`: LLM-powered routing
  - `"semantic"`: Semantic similarity routing
- **routes** (`Optional[dict]`, default: `None`): Route definitions mapping route names to agents

**Returns:** Self for method chaining

**Example:**
```python
routes = {
    "translate": translator_agent,
    "summarize": summarizer_agent,
}

agent = (
    AgentBuilder("router")
    .with_routing(strategy="semantic", routes=routes)
    .build()
)
```

---

### with_tools()

Add tools to the agent.

```python
def with_tools(self, tools: list[Callable]) -> AgentBuilder
```

**Parameters:**
- **tools** (`list[Callable]`): List of tool functions

**Returns:** Self for method chaining

**Example:**
```python
def search_web(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"

def calculate(expression: str) -> float:
    """Calculate math expression."""
    return eval(expression)

agent = (
    AgentBuilder("assistant")
    .with_tools([search_web, calculate])
    .build()
)
```

---

### with_hooks()

Add pre and post execution hooks.

```python
def with_hooks(
    self,
    pre: Optional[list[Callable]] = None,
    post: Optional[list[Callable]] = None,
) -> AgentBuilder
```

**Parameters:**
- **pre** (`Optional[list[Callable]]`, default: `None`): Pre-execution hooks
- **post** (`Optional[list[Callable]]`, default: `None`): Post-execution hooks

**Returns:** Self for method chaining

**Hook Signatures:**
- **Pre-hook:** `def pre_hook(*args, **kwargs) -> None`
- **Post-hook:** `def post_hook(result: Any) -> None`

**Example:**
```python
def log_input(*args, **kwargs):
    print(f"Input: {args}, {kwargs}")

def log_output(result):
    print(f"Output: {result}")

agent = (
    AgentBuilder("monitored_agent")
    .with_hooks(
        pre=[log_input],
        post=[log_output]
    )
    .build()
)
```

---

### with_context()

Set LLM generation parameters.

```python
def with_context(self, **kwargs: Any) -> AgentBuilder
```

**Parameters:**
- **kwargs**: LLM generation parameters
  - `temperature` (`float`): Sampling temperature (0.0-2.0)
  - `max_tokens` (`int`): Maximum response tokens
  - `top_p` (`float`): Nucleus sampling threshold
  - `frequency_penalty` (`float`): Repetition penalty
  - `presence_penalty` (`float`): Topic diversity penalty
  - Other LiteLLM-supported parameters

**Returns:** Self for method chaining

**Example:**
```python
# Deterministic agent (factual tasks)
factual = (
    AgentBuilder("fact_checker")
    .with_context(
        temperature=0.2,
        max_tokens=500
    )
    .build()
)

# Creative agent (story generation)
creative = (
    AgentBuilder("storyteller")
    .with_context(
        temperature=1.5,
        max_tokens=2000,
        top_p=0.9
    )
    .build()
)
```

---

### build()

Build and return the final agent.

```python
def build(self) -> Callable
```

**Returns:** Callable agent function

**Raises:**
- `ValueError`: If configuration is invalid

**Example:**
```python
agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .with_memory(type="working")
    .build()
)

# Use the agent
result = await agent("Hello!")
```

---

## Complete Example

```python
import asyncio
from pathlib import Path
from kagura import AgentBuilder


def search_web(query: str) -> str:
    """Search the web."""
    return f"Search results for: {query}"


def log_execution(result):
    """Log agent executions."""
    print(f"[LOG] Result: {result}")


async def main():
    # Build a complex agent
    agent = (
        AgentBuilder("advanced_assistant")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            persist_dir=Path.home() / ".kagura" / "agents",
            max_messages=100,
            enable_rag=True
        )
        .with_tools([search_web])
        .with_hooks(post=[log_execution])
        .with_context(
            temperature=0.7,
            max_tokens=800
        )
        .build()
    )

    # Use the agent
    result = await agent("Search for Python tutorials")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Configuration Classes

### AgentConfiguration

```python
from kagura.builder import AgentConfiguration

config = AgentConfiguration(
    name="my_agent",
    model="gpt-4o-mini"
)
```

**Fields:**
- **name** (`str`): Agent name
- **model** (`str`): LLM model
- **memory** (`Optional[MemoryConfig]`): Memory configuration
- **routing** (`Optional[RoutingConfig]`): Routing configuration
- **tools** (`list[Callable]`): Tool functions
- **hooks** (`Optional[HooksConfig]`): Hook configuration
- **context** (`dict[str, Any]`): LLM parameters

### MemoryConfig

```python
from kagura.builder import MemoryConfig

memory = MemoryConfig(
    type="persistent",
    persist_dir=Path(".kagura"),
    max_messages=100,
    enable_rag=True
)
```

**Fields:**
- **type** (`str`): Memory type
- **persist_dir** (`Optional[Path]`): Storage directory
- **max_messages** (`int`): Message limit
- **enable_rag** (`bool`): Enable RAG

### RoutingConfig

```python
from kagura.builder import RoutingConfig

routing = RoutingConfig(
    strategy="semantic",
    routes={"translate": translator_agent}
)
```

**Fields:**
- **strategy** (`str`): Routing strategy
- **routes** (`dict`): Route mappings

### HooksConfig

```python
from kagura.builder import HooksConfig

hooks = HooksConfig(
    pre=[pre_hook1, pre_hook2],
    post=[post_hook1, post_hook2]
)
```

**Fields:**
- **pre** (`list[Callable]`): Pre-execution hooks
- **post** (`list[Callable]`): Post-execution hooks

---

## Best Practices

### 1. Use Descriptive Names

```python
# Good
AgentBuilder("customer_support_chatbot")

# Less clear
AgentBuilder("agent1")
```

### 2. Chain Methods Vertically

```python
# Good - readable
agent = (
    AgentBuilder("name")
    .with_model("gpt-4o-mini")
    .with_memory(type="rag")
    .build()
)

# Less readable
agent = AgentBuilder("name").with_model("gpt-4o-mini").with_memory(type="rag").build()
```

### 3. Choose Appropriate Memory Type

```python
# Short conversations
.with_memory(type="working")

# Long-term knowledge
.with_memory(type="persistent", enable_rag=True)

# Context-aware
.with_memory(type="context", max_messages=20)
```

### 4. Temperature Selection

```python
# Factual tasks (low temperature)
.with_context(temperature=0.2)

# Balanced (medium temperature)
.with_context(temperature=0.7)

# Creative tasks (high temperature)
.with_context(temperature=1.5)
```

---

## Error Handling

```python
from kagura import AgentBuilder

try:
    agent = (
        AgentBuilder("my_agent")
        .with_model("invalid-model")
        .build()
    )
except ValueError as e:
    print(f"Configuration error: {e}")

try:
    agent = (
        AgentBuilder("my_agent")
        .with_memory(enable_rag=True)  # Without ChromaDB
        .build()
    )
except ImportError as e:
    print(f"Missing dependency: {e}")
```

---

## Related

- [Tutorial: Agent Builder](../tutorials/13-agent-builder.md) - Step-by-step guide
- [@agent Decorator](agent.md) - Core agent decorator
- [Memory Management](memory.md) - Memory system details
- [Agent Routing](routing.md) - Routing strategies

---

## See Also

- [Quick Start](../quickstart.md) - Getting started guide
- [Tutorial: Testing](../tutorials/14-testing.md) - Testing agents
- [Tutorial: Observability](../tutorials/15-observability.md) - Monitoring agents
