# AgentBuilder Examples

This directory contains examples demonstrating the **AgentBuilder** fluent API for creating complex agents with integrated features.

## Overview

AgentBuilder provides a chainable, intuitive API for constructing agents with:
- **Memory management** (context, persistent, RAG)
- **Tool integration** (function calling)
- **Custom configurations** (model, temperature, tokens)
- **Built-in presets** (quick, conversational, research, creative, analytical)

## Examples

### 1. Basic Builder (`basic_builder.py`)

Demonstrates the fundamentals of AgentBuilder:
- Simple agent with just a model
- Agent with custom parameters (temperature, max_tokens)
- Creative vs factual agent configurations

**Run:**
```bash
python examples/agent_builder/basic_builder.py
```

**Key Concepts:**
- Method chaining
- Model selection
- Context configuration

---

### 2. Memory Integration (`with_memory.py`)

Shows different memory configurations:
- Basic memory (conversation context)
- Persistent memory (long-term storage)
- RAG-enabled memory (semantic search)
- Session-based memory
- Custom memory configuration

**Run:**
```bash
python examples/agent_builder/with_memory.py
```

**Key Concepts:**
- Memory types: `context`, `persistent`
- RAG integration for semantic retrieval
- Session management
- Custom persist directories

---

### 3. Tool Integration (`with_tools.py`)

Demonstrates tool/function calling:
- Single tool integration
- Multiple tools
- Tools with memory
- Tool-enabled workflows
- Custom tool configurations

**Run:**
```bash
python examples/agent_builder/with_tools.py
```

**Key Concepts:**
- Function calling
- Tool registration
- Combining tools with memory
- Multi-step workflows

---

### 4. Built-in Presets (`presets.py`)

Shows how to use built-in agent presets:
- Quick preset (fast, minimal)
- Conversational preset (with memory)
- Research preset (with tools)
- Creative preset (high temperature)
- Analytical preset (low temperature)
- Custom preset overrides

**Run:**
```bash
python examples/agent_builder/presets.py
```

**Key Concepts:**
- Preset types
- Preset customization
- Comparing different presets

---

## Quick Start

```python
from kagura import AgentBuilder

# Basic agent
agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .build()
)

result = await agent("Hello!")
```

## Common Patterns

### Pattern 1: Conversational Agent with Memory

```python
agent = (
    AgentBuilder("chatbot")
    .with_model("gpt-4o-mini")
    .with_memory(type="context", max_messages=50)
    .build()
)
```

### Pattern 2: Research Agent with Tools

```python
agent = (
    AgentBuilder("researcher")
    .with_model("gpt-4o")
    .with_memory(type="persistent", enable_rag=True)
    .with_tools([search_web, calculate])
    .build()
)
```

### Pattern 3: Using Presets

```python
# Quick setup with preset
agent = (
    AgentBuilder("assistant")
    .with_preset("conversational")
    .build()
)

# Preset with overrides
agent = (
    AgentBuilder("custom")
    .with_preset("analytical")
    .with_model("gpt-4o")  # Override default model
    .build()
)
```

## API Reference

For complete API documentation, see:
- [AgentBuilder API Reference](../../docs/en/api/builder.md)
- [Memory API Reference](../../docs/en/api/memory.md)

## Related Examples

- [Testing Examples](../testing/) - How to test agents created with AgentBuilder
- [Observability Examples](../observability/) - Monitoring and cost tracking
- [Memory-Aware Routing](../memory_routing/) - Context-aware agent routing

## Next Steps

After exploring these examples, you can:
1. Learn about [Testing Agents](../testing/)
2. Explore [Observability](../observability/) for monitoring
3. Build [Advanced Workflows](../advanced_workflows/)

---

**Note:** Make sure you have set up your API keys (e.g., `OPENAI_API_KEY`) before running these examples.
