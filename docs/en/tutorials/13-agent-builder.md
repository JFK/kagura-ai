# Tutorial 13: Agent Builder

Learn how to use the AgentBuilder fluent API to create complex agents with integrated features.

## Prerequisites

- Python 3.11 or higher
- Kagura AI installed (`pip install kagura-ai`)
- Completion of [Tutorial 1: Basic Agent](01-basic-agent.md)
- OpenAI API key (or other LLM provider)

## Goal

By the end of this tutorial, you will:
- Understand the AgentBuilder fluent API pattern
- Build agents with memory, tools, and hooks
- Configure LLM generation parameters
- Create reusable agent configurations

## What is AgentBuilder?

`AgentBuilder` is a fluent API that simplifies creating complex agents with multiple features. Instead of manually wiring together memory, tools, hooks, and routing, you can use method chaining to build agents declaratively.

### Before AgentBuilder

```python
from kagura import agent
from kagura.core.memory import MemoryManager

# Manually configure everything
memory = MemoryManager(agent_name="my_agent", enable_rag=True)

@agent(model="gpt-4o-mini", temperature=0.7)
async def my_agent(prompt: str) -> str:
    '''Process: {{ prompt }}'''
    pass
```

### With AgentBuilder

```python
from kagura import AgentBuilder

# Declarative configuration
agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .with_memory(type="rag", enable_rag=True)
    .with_context(temperature=0.7)
    .build()
)
```

## Step 1: Basic Agent Creation

Create a file called `builder_demo.py`:

```python
import asyncio
from kagura import AgentBuilder


async def main():
    # Create a basic agent with AgentBuilder
    agent = (
        AgentBuilder("greeter")
        .with_model("gpt-4o-mini")
        .build()
    )

    result = await agent("Say hello!")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python builder_demo.py
```

**Explanation:**
1. `AgentBuilder("greeter")` - Initialize builder with agent name
2. `.with_model("gpt-4o-mini")` - Set the LLM model
3. `.build()` - Build the final agent

## Step 2: Adding Memory

Let's add memory so the agent can remember conversation history:

```python
agent = (
    AgentBuilder("assistant")
    .with_model("gpt-4o-mini")
    .with_memory(
        max_messages=50,
        enable_rag=False
    )
    .build()
)

# Agent can now access conversation history
result = await agent("My name is Alice")
print(result)  # "Nice to meet you, Alice!"

result = await agent("What's my name?")
print(result)  # "Your name is Alice."
```

**Memory Configuration:**
- All memory is persistent (stored in SQLite)
- `max_messages` - Number of recent messages to keep in context
- `enable_rag` - Enable semantic search with ChromaDB

## Step 3: RAG (Semantic Memory)

For semantic search over conversation history:

```python
agent = (
    AgentBuilder("smart_assistant")
    .with_model("gpt-4o-mini")
    .with_memory(
        enable_rag=True,
        max_messages=100
    )
    .build()
)

# Store various facts
await agent("Python is a programming language created by Guido van Rossum")
await agent("I love hiking in the mountains")
await agent("My favorite food is sushi")

# Semantic search finds relevant context
result = await agent("Tell me about programming")
# Agent recalls: "Python is a programming language..."

result = await agent("What do I like to eat?")
# Agent recalls: "My favorite food is sushi"
```

**Note:** RAG requires ChromaDB installation:
```bash
pip install chromadb
```

## Step 4: Adding Tools

Tools extend agents with external capabilities:

```python
def search_web(query: str) -> str:
    """Search the web for information."""
    # Simulate web search
    return f"Search results for: {query}"


def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)  # Note: Use safely in production!


agent = (
    AgentBuilder("researcher")
    .with_model("gpt-4o-mini")
    .with_tools([search_web, calculate])
    .build()
)

# Agent can now use tools
result = await agent("What is 15 * 23?")
# Agent calls calculate("15 * 23") and returns: "345"

result = await agent("Search for Python tutorials")
# Agent calls search_web("Python tutorials")
```

## Step 5: Pre and Post Hooks

Hooks let you inject logic before and after agent execution:

```python
def log_input(*args, **kwargs):
    """Log agent input."""
    print(f"[PRE] Input: {args}, {kwargs}")


def log_output(result):
    """Log agent output."""
    print(f"[POST] Output: {result}")


agent = (
    AgentBuilder("monitored_agent")
    .with_model("gpt-4o-mini")
    .with_hooks(
        pre=[log_input],
        post=[log_output]
    )
    .build()
)

result = await agent("Hello!")
# Console output:
# [PRE] Input: ('Hello!',), {}
# [POST] Output: Hi there! How can I help you?
```

**Use Cases for Hooks:**
- Logging and monitoring
- Input validation
- Output sanitization
- Rate limiting
- Caching

## Step 6: LLM Generation Parameters

Control how the LLM generates responses:

```python
# More deterministic (factual tasks)
factual_agent = (
    AgentBuilder("fact_checker")
    .with_model("gpt-4o-mini")
    .with_context(
        temperature=0.2,
        max_tokens=500
    )
    .build()
)

# More creative (story generation)
creative_agent = (
    AgentBuilder("storyteller")
    .with_model("gpt-4o-mini")
    .with_context(
        temperature=1.5,
        max_tokens=1000,
        top_p=0.9
    )
    .build()
)
```

**Common Parameters:**
- `temperature` (0.0-2.0): Randomness (lower = more deterministic)
- `max_tokens`: Maximum response length
- `top_p` (0.0-1.0): Nucleus sampling threshold
- `frequency_penalty`: Discourage repetition
- `presence_penalty`: Encourage new topics

## Complete Example: Multi-Feature Agent

Here's an agent with all features combined:

```python
import asyncio
from pathlib import Path
from kagura import AgentBuilder


def web_search(query: str) -> str:
    """Search the web."""
    return f"Results for: {query}"


def log_execution(result):
    """Log each execution."""
    print(f"[LOG] Agent returned: {result}")


async def main():
    # Build a powerful multi-feature agent
    agent = (
        AgentBuilder("advanced_assistant")
        .with_model("gpt-4o-mini")
        .with_memory(
            type="persistent",
            persist_dir=Path.home() / ".kagura" / "agents",
            max_messages=100,
            enable_rag=True
        )
        .with_tools([web_search])
        .with_hooks(
            post=[log_execution]
        )
        .with_context(
            temperature=0.7,
            max_tokens=800
        )
        .build()
    )

    # Test the agent
    result = await agent("Search for Python tutorials")
    print(f"Response: {result}")

    result = await agent("What did I just ask you?")
    print(f"Response: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Agent Configuration Object

You can also work with configuration separately:

```python
from kagura import AgentBuilder
from kagura.builder import AgentConfiguration, MemoryConfig

# Create configuration
config = AgentConfiguration(
    name="my_agent",
    model="gpt-4o-mini"
)

# Build agent from config
builder = AgentBuilder(config.name)
builder._config = config
agent = builder.build()
```

## Best Practices

### 1. Descriptive Agent Names

```python
# Good
AgentBuilder("customer_support_chatbot")
AgentBuilder("data_analysis_assistant")

# Less clear
AgentBuilder("agent1")
AgentBuilder("my_agent")
```

### 2. Choose Appropriate Memory Configuration

```python
# Short conversations - basic memory
AgentBuilder("quick_qa").with_memory(max_messages=20)

# Long-term knowledge - RAG enabled
AgentBuilder("knowledge_base").with_memory(enable_rag=True)

# Custom persistence directory
AgentBuilder("assistant").with_memory(
    persist_dir=Path.home() / ".kagura"
)
```

### 3. Model Selection

```python
# Fast, cheap tasks
.with_model("gpt-4o-mini")

# Complex reasoning
.with_model("gpt-4o")
.with_model("claude-3-5-sonnet-20241022")

# Local models
.with_model("ollama/llama3.2")
```

### 4. Method Chaining Formatting

```python
# Good - readable
agent = (
    AgentBuilder("name")
    .with_model("gpt-4o-mini")
    .with_memory(type="rag")
    .with_tools([tool1, tool2])
    .build()
)

# Less readable
agent = AgentBuilder("name").with_model("gpt-4o-mini").with_memory(type="rag").with_tools([tool1, tool2]).build()
```

## Common Patterns

### Pattern 1: Chatbot with Memory

```python
chatbot = (
    AgentBuilder("chatbot")
    .with_model("gpt-4o-mini")
    .with_memory(max_messages=20)
    .with_context(temperature=0.8)
    .build()
)
```

### Pattern 2: Researcher with Tools

```python
researcher = (
    AgentBuilder("researcher")
    .with_model("gpt-4o")
    .with_tools([web_search, summarize, extract_facts])
    .with_context(temperature=0.3)
    .build()
)
```

### Pattern 3: Monitored Agent

```python
monitored = (
    AgentBuilder("monitored")
    .with_model("gpt-4o-mini")
    .with_hooks(
        pre=[validate_input, rate_limit],
        post=[log_output, cache_result]
    )
    .build()
)
```

## Common Mistakes

### 1. Forgetting `.build()`

```python
# Wrong - returns AgentBuilder, not an agent
agent = AgentBuilder("name").with_model("gpt-4o-mini")

# Correct
agent = AgentBuilder("name").with_model("gpt-4o-mini").build()
```

### 2. Enabling RAG Without ChromaDB

```python
# This will fail if chromadb is not installed
agent = (
    AgentBuilder("agent")
    .with_memory(enable_rag=True)
    .build()
)

# Install first:
# pip install chromadb
```

### 3. Not Cleaning Up Persistent Memory

```python
# Be aware: all memory persists
agent = (
    AgentBuilder("agent")
    .with_memory(enable_rag=True)
    .build()
)

# Good practice: Clean up when done
await agent.memory_manager.forget("temporary_key")
```

## Practice Exercises

### Exercise 1: Build a Knowledge Assistant

Create an agent that:
- Uses GPT-4o-mini
- Has RAG-enabled memory
- Logs all interactions

```python
# Your code here
knowledge_assistant = (
    AgentBuilder("knowledge_assistant")
    # Add configurations
    .build()
)

# Test it
await knowledge_assistant("Python is a programming language")
await knowledge_assistant("What did I tell you about Python?")
```

### Exercise 2: Tool-Equipped Researcher

Create an agent with:
- GPT-4o model
- Web search and calculator tools
- Low temperature (0.2) for accuracy

```python
# Your code here
```

### Exercise 3: Multi-Agent System

Build two agents with different configurations and have them work together:

```python
# Analyst (factual)
analyst = AgentBuilder("analyst")...

# Storyteller (creative)
storyteller = AgentBuilder("storyteller")...

# Workflow
facts = await analyst("Analyze: quantum computing")
story = await storyteller(f"Write a story about: {facts}")
```

## Key Concepts Learned

### 1. Fluent API Pattern

Method chaining for readable configuration:
```python
builder.method1().method2().method3()
```

### 2. Declarative Agent Configuration

Specify what you want, not how to build it:
```python
AgentBuilder("name").with_feature().build()
```

### 3. Feature Integration

Combine memory, tools, and hooks seamlessly:
```python
.with_memory().with_tools().with_hooks()
```

## Next Steps

- [Tutorial 14: Agent Testing](14-testing.md) - Learn to test your agents
- [Tutorial 15: Observability](15-observability.md) - Monitor agent performance
- [API Reference: Builder](../api/builder.md) - Complete API documentation

## Summary

You learned:
- ✓ How to use AgentBuilder's fluent API
- ✓ How to add memory (working, persistent, RAG)
- ✓ How to integrate tools and hooks
- ✓ How to configure LLM generation parameters
- ✓ Best practices for agent configuration

Continue to [Tutorial 14: Agent Testing](14-testing.md) to learn how to test your agents!
