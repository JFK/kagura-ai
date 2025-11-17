# Kagura AI SDK Guide

Complete guide to building AI agents with Kagura AI v4.0 SDK.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Agent Decorator](#agent-decorator)
- [Custom Tools](#custom-tools)
- [Memory Management](#memory-management)
- [Parallel Execution](#parallel-execution)
- [Error Handling](#error-handling)
- [Testing](#testing)
- [Best Practices](#best-practices)

---

## Quick Start

### Installation

```bash
pip install kagura-ai
```

### Your First Agent

```python
import asyncio
from kagura import agent

@agent
async def hello(name: str) -> str:
    """Say hello to {{ name }} in a friendly way."""
    pass  # Implementation replaced by AI

# Run the agent
result = asyncio.run(hello("Alice"))
print(result)  # "Hello Alice! Welcome..."
```

**How it works:**
1. `@agent` decorator converts your function into an AI agent
2. The docstring becomes the AI prompt (Jinja2 template)
3. Function signature defines inputs and outputs
4. The AI generates the implementation at runtime

---

## Core Concepts

### 1. Agent Functions

Agent functions are Python functions decorated with `@agent`:

```python
@agent
async def my_agent(input: str) -> str:
    """Your prompt template here: {{ input }}"""
    pass
```

**Key components:**
- **Function name**: Identifies the agent (used in telemetry)
- **Parameters**: Define agent inputs (passed to prompt)
- **Return type**: Defines output structure (string, Pydantic model, etc.)
- **Docstring**: Jinja2 prompt template

### 2. Prompt Templates

Use Jinja2 syntax in docstrings to create dynamic prompts:

```python
@agent
async def translator(text: str, target_lang: str) -> str:
    """
    Translate the following text to {{ target_lang }}:

    {{ text }}

    Provide only the translation, no explanations.
    """
    pass
```

### 3. Structured Outputs

Use Pydantic models for type-safe, validated outputs:

```python
from pydantic import BaseModel, Field

class Sentiment(BaseModel):
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(ge=0, le=1, description="Confidence score")
    reasoning: str = Field(description="Brief explanation")

@agent
async def analyze_sentiment(text: str) -> Sentiment:
    """Analyze the sentiment of: {{ text }}"""
    pass

# Type-safe access
result = await analyze_sentiment("I love this!")
print(result.sentiment)  # IDE autocomplete works!
print(result.confidence)  # 0.95
```

---

## Agent Decorator

### Basic Usage

```python
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    """Process {{ input }}"""
    pass
```

### Configuration Options

```python
from kagura import agent, LLMConfig

config = LLMConfig(
    model="gpt-4o",                  # Model to use
    temperature=0.7,                 # Creativity (0-1)
    max_tokens=1000,                 # Max response length
    enable_cache=True,               # Enable response caching
)

@agent(config=config)
async def configured_agent(input: str) -> str:
    """Process {{ input }}"""
    pass
```

### Model Selection

Kagura uses [LiteLLM](https://github.com/BerriAI/litellm) for multi-provider support:

```python
# OpenAI
@agent(model="gpt-4o")
async def openai_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

# Anthropic Claude
@agent(model="claude-3-5-sonnet-20241022")
async def claude_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

# Google Gemini
@agent(model="gemini/gemini-2.0-flash")
async def gemini_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

# Ollama (local)
@agent(model="ollama/llama3.2")
async def local_agent(input: str) -> str:
    """Process {{ input }}"""
    pass
```

**Supported providers:** OpenAI, Anthropic, Google, Azure, AWS Bedrock, Ollama, and 100+ others.

### Memory-Enabled Agents

```python
from kagura import agent
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="assistant")

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """
    You are a helpful assistant with memory.
    User: {{ query }}
    """
    pass

# Conversation with context
await assistant("My name is Alice", memory_manager=memory)
await assistant("What's my name?", memory_manager=memory)
# Response: "Your name is Alice"
```

### Tool-Enabled Agents

```python
from kagura import agent, tool

@tool
async def search_web(query: str) -> str:
    """Search the web for: {{ query }}"""
    # Your search implementation
    return f"Results for {query}"

@agent(tools=[search_web])
async def researcher(topic: str) -> str:
    """
    Research {{ topic }} using search_web(query).
    Synthesize findings into a summary.
    """
    pass

# Agent can call search_web automatically
result = await researcher("latest AI trends")
```

---

## Custom Tools

Tools extend agent capabilities with custom functions.

### Creating a Tool

```python
from kagura import tool

@tool
async def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Math expression like "2 + 2" or "sqrt(16)"

    Returns:
        The calculated result
    """
    # Safe evaluation (use ast.literal_eval or similar)
    import ast
    return float(ast.literal_eval(expression))
```

### Using Tools in Agents

```python
from kagura import agent, tool

@tool
async def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Call weather API
    return f"Sunny, 72°F in {city}"

@tool
async def get_time(timezone: str = "UTC") -> str:
    """Get current time in a timezone."""
    from datetime import datetime
    return datetime.now().isoformat()

@agent(tools=[get_weather, get_time])
async def assistant(request: str) -> str:
    """
    Help with: {{ request }}

    Available tools:
    - get_weather(city): Get weather
    - get_time(timezone): Get current time
    """
    pass

# Agent automatically calls appropriate tools
result = await assistant("What's the weather in Tokyo and current time?")
```

### Tool Guidelines

**Best practices:**
1. **Clear docstrings**: Describe purpose, parameters, and return values
2. **Type hints**: Use for parameter validation
3. **Error handling**: Handle failures gracefully
4. **Idempotent**: Same input should produce same output when possible
5. **Side effects**: Document any state changes or external calls

**Example with error handling:**

```python
@tool
async def fetch_url(url: str) -> str:
    """Fetch content from a URL.

    Args:
        url: The URL to fetch

    Returns:
        Page content or error message
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.text[:5000]  # Limit size
    except httpx.HTTPError as e:
        return f"Error fetching {url}: {e}"
```

---

## Memory Management

Kagura provides a unified memory system with persistent storage and semantic search capabilities.

**Important:** As of v4.4.0, all memory is persistent. The `scope="working"` parameter and temporary memory methods (`set_temp()`, `get_temp()`) have been removed.

### 1. Context Memory (Conversation History)

Keep recent messages in context:

```python
from kagura import agent
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="chatbot",
    max_messages=10  # Keep last 10 messages
)

@agent(enable_memory=True)
async def chatbot(message: str, memory_manager: MemoryManager) -> str:
    """Conversational assistant. User: {{ message }}"""
    pass

# Multi-turn conversation
await chatbot("Hi, I'm learning Python", memory_manager=memory)
await chatbot("What's my name?", memory_manager=memory)
await chatbot("Recommend resources for what I'm learning", memory_manager=memory)
```

### 2. Persistent Memory (Long-term Storage)

Store facts across sessions with ChromaDB:

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="assistant",
    enable_session_memory=True,
    session_id="user_123"
)

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """Assistant with persistent memory. User: {{ query }}"""
    pass

# Store long-term facts
await assistant("My favorite color is blue", memory_manager=memory)

# Later session - memory persists
memory2 = MemoryManager(
    agent_name="assistant",
    enable_session_memory=True,
    session_id="user_123"
)
await assistant("What's my favorite color?", memory_manager=memory2)
# Response: "Your favorite color is blue"
```

### 3. RAG Memory (Semantic Search)

Index and search documents semantically:

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="docs_bot",
    enable_rag=True,
    rag_collection="my_docs"
)

# Index documents
await memory.rag_store(
    content="Kagura AI is an MCP-native memory platform",
    metadata={"source": "README.md"}
)

@agent(enable_memory=True)
async def docs_bot(question: str, memory_manager: MemoryManager) -> str:
    """
    Answer based on documentation: {{ question }}
    Use RAG memory to find relevant docs.
    """
    pass

result = await docs_bot("What is Kagura AI?", memory_manager=memory)
```

### 4. Graph Memory (Relationships)

Track entities and relationships:

```python
from kagura.core.graph import GraphMemory

graph = GraphMemory(user_id="user_123", agent_name="assistant")

# Store interactions
graph.add_interaction(
    user_query="I love hiking",
    ai_response="That's great! Hiking is a healthy outdoor activity.",
    metadata={"topic": "hobbies"}
)

# Find related information
related = graph.get_related_nodes(node_id="hiking_interest", depth=2)
```

### Memory Strategies

**Choose the right memory type:**

| Memory Type | Use Case | Persistence | Search |
|------------|----------|-------------|--------|
| **Context** | Recent messages | Persistent (SQLite) | Sequential |
| **Persistent** | User preferences | Persistent (SQLite) | Key-value lookup |
| **RAG** | Document QA | Persistent (ChromaDB) | Semantic |
| **Graph** | Relationships | Persistent (NetworkX) | Graph traversal |

**Migration from v4.3.x to v4.4.0:**
- All memory is now persistent - no temporary/session-only memory
- Remove `scope="working"` from all `memory_store()` calls
- Replace `set_temp()`/`get_temp()` with client-side variables or persistent storage
- Use `remember()`/`recall()` for all persistent data

---

## Parallel Execution

Speed up independent operations with concurrency.

### parallel_gather

Execute multiple operations concurrently:

```python
from kagura import agent
from kagura.core.parallel import parallel_gather

@agent
async def translator(text: str, lang: str) -> str:
    """Translate {{ text }} to {{ lang }}"""
    pass

# Serial (slow)
spanish = await translator("Hello", "Spanish")
french = await translator("Hello", "French")
japanese = await translator("Hello", "Japanese")

# Parallel (3x faster)
spanish, french, japanese = await parallel_gather(
    translator("Hello", "Spanish"),
    translator("Hello", "French"),
    translator("Hello", "Japanese")
)
```

### parallel_map

Process batches efficiently:

```python
from kagura.core.parallel import parallel_map

@agent
async def analyze(text: str) -> str:
    """Analyze sentiment of: {{ text }}"""
    pass

reviews = [
    "Amazing product!",
    "Terrible experience.",
    "Pretty good overall.",
    # ... 100 more reviews
]

# Process 10 at a time
results = await parallel_map(
    lambda review: analyze(review),
    reviews,
    max_concurrent=10
)
```

### Multi-Agent Pipelines

Parallelize independent steps:

```python
from kagura.core.parallel import parallel_gather

@agent
async def summarize(text: str) -> str:
    """Summarize: {{ text }}"""
    pass

@agent
async def extract_keywords(text: str) -> list[str]:
    """Extract keywords from: {{ text }}"""
    pass

@agent
async def categorize(text: str) -> str:
    """Categorize: {{ text }}"""
    pass

# All operations run in parallel
article = "Long article text..."
summary, keywords, category = await parallel_gather(
    summarize(article),
    extract_keywords(article),
    categorize(article)
)
```

---

## Error Handling

### Basic Error Handling

```python
from kagura import agent
from kagura.core.exceptions import AgentError, LLMError

@agent
async def my_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

try:
    result = await my_agent("test")
except LLMError as e:
    print(f"LLM error: {e}")
    # Handle API failures, rate limits, etc.
except AgentError as e:
    print(f"Agent error: {e}")
    # Handle agent-specific errors
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Retry with Tenacity

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from kagura import agent

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_agent_with_retry(input: str) -> str:
    return await my_agent(input)

# Automatically retries on failure
result = await call_agent_with_retry("test")
```

### Fallback Patterns

```python
@agent(model="gpt-4o")
async def primary_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

@agent(model="gpt-4o-mini")
async def fallback_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

async def robust_call(input: str) -> str:
    try:
        return await primary_agent(input)
    except Exception:
        # Fallback to cheaper/simpler model
        return await fallback_agent(input)

result = await robust_call("test")
```

---

## Testing

### Unit Testing Agents

```python
import pytest
from kagura import agent

@agent
async def sentiment_analyzer(text: str) -> str:
    """Analyze sentiment of: {{ text }}
    Return: positive, negative, or neutral"""
    pass

@pytest.mark.asyncio
async def test_sentiment_analyzer():
    # Positive sentiment
    result = await sentiment_analyzer("I love this!")
    assert "positive" in result.lower()

    # Negative sentiment
    result = await sentiment_analyzer("This is terrible")
    assert "negative" in result.lower()
```

### Mocking LLM Calls

```python
from unittest.mock import AsyncMock, patch
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

@pytest.mark.asyncio
@patch('kagura.core.llm.call_llm')
async def test_agent_with_mock(mock_llm):
    # Mock LLM response
    mock_llm.return_value = "Mocked response"

    result = await my_agent("test")
    assert result == "Mocked response"

    # Verify LLM was called
    mock_llm.assert_called_once()
```

### Testing Tools

```python
from kagura import tool

@tool
async def calculate(expression: str) -> float:
    """Calculate: {{ expression }}"""
    import ast
    return float(ast.literal_eval(expression))

@pytest.mark.asyncio
async def test_calculate_tool():
    assert await calculate("2 + 2") == 4.0
    assert await calculate("10 * 5") == 50.0

    # Test error handling
    with pytest.raises(Exception):
        await calculate("invalid")
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_agent_with_memory():
    from kagura.core.memory import MemoryManager

    memory = MemoryManager(agent_name="test_agent")

    # First interaction
    result1 = await chatbot("My name is Alice", memory_manager=memory)
    assert "Alice" in result1

    # Memory should persist
    result2 = await chatbot("What's my name?", memory_manager=memory)
    assert "Alice" in result2
```

---

## Best Practices

### 1. Prompt Engineering

**Be specific and clear:**

```python
# ❌ Vague
@agent
async def bad_agent(input: str) -> str:
    """Do something with {{ input }}"""
    pass

# ✅ Specific
@agent
async def good_agent(text: str) -> str:
    """
    Analyze the sentiment of the following text: {{ text }}

    Respond with one of: positive, negative, neutral
    Include a confidence score (0-1) and brief reasoning.
    """
    pass
```

**Provide examples in prompts:**

```python
@agent
async def extractor(text: str) -> dict:
    """
    Extract person information from: {{ text }}

    Examples:
    - "John is 30 years old" -> {"name": "John", "age": 30}
    - "Alice works as a teacher" -> {"name": "Alice", "occupation": "teacher"}

    Return JSON with available fields.
    """
    pass
```

### 2. Type Safety

**Use Pydantic models for complex outputs:**

```python
from pydantic import BaseModel, Field

class Analysis(BaseModel):
    sentiment: str = Field(description="positive/negative/neutral")
    confidence: float = Field(ge=0, le=1)
    keywords: list[str] = Field(max_length=10)

@agent
async def analyze(text: str) -> Analysis:
    """Analyze: {{ text }}"""
    pass

# Type-safe, validated
result = await analyze("Great product!")
print(result.sentiment)  # IDE autocomplete
```

### 3. Resource Management

**Use connection pooling and limits:**

```python
from kagura import LLMConfig

config = LLMConfig(
    model="gpt-4o-mini",
    max_tokens=500,          # Limit response length
    enable_cache=True,       # Cache identical requests
    timeout=30,              # Prevent hanging
)

@agent(config=config)
async def efficient_agent(input: str) -> str:
    """Process {{ input }}"""
    pass
```

**Limit parallel execution:**

```python
from kagura.core.parallel import parallel_map

# Don't overwhelm API with 1000 concurrent requests
results = await parallel_map(
    agent_func,
    inputs,
    max_concurrent=10  # Reasonable limit
)
```

### 4. Monitoring

**Track costs and usage:**

```bash
# CLI monitoring
kagura monitor stats
kagura monitor cost --agent my_agent
```

**Instrument agents:**

```python
import logging

logger = logging.getLogger(__name__)

@agent
async def monitored_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

try:
    result = await monitored_agent("test")
    logger.info("Agent succeeded", extra={"input": "test"})
except Exception as e:
    logger.error("Agent failed", exc_info=True)
    raise
```

### 5. Security

**Validate inputs:**

```python
from pydantic import BaseModel, Field, validator

class SafeInput(BaseModel):
    query: str = Field(max_length=1000)

    @validator('query')
    def no_injection(cls, v):
        dangerous = ['DROP', 'DELETE', 'EXEC']
        if any(word in v.upper() for word in dangerous):
            raise ValueError("Potentially dangerous input")
        return v

@agent
async def safe_agent(input: SafeInput) -> str:
    """Process {{ input.query }}"""
    pass
```

**Sanitize tool outputs:**

```python
@tool
async def safe_search(query: str) -> str:
    """Search safely"""
    # Validate query
    if len(query) > 500:
        return "Query too long"

    # Execute search
    results = execute_search(query)

    # Sanitize results
    return sanitize_html(results[:5000])
```

---

## Next Steps

### Learn More

- [API Reference](api-reference.md) - Complete API documentation
- [Tutorials](en/tutorials/) - Step-by-step guides
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - Real-world code samples
- [Architecture](architecture.md) - System design

### Integration

- [MCP Integration](mcp-setup.md) - Connect to Claude Desktop
- [REST API](rest-api-usage.md) - HTTP API access
- [Self-Hosting](self-hosting.md) - Deploy your own instance

### Community

- [GitHub](https://github.com/JFK/kagura-ai) - Report issues, contribute
- [Contributing Guide](https://github.com/JFK/kagura-ai/blob/main/CONTRIBUTING.md)

---

## Summary

**Key takeaways:**

1. **`@agent` decorator** converts functions into AI agents
2. **Jinja2 prompts** make dynamic, contextual interactions
3. **Pydantic models** provide type-safe, validated outputs
4. **Custom tools** extend agent capabilities
5. **Memory tiers** handle different persistence needs
6. **Parallel execution** speeds up independent operations
7. **Error handling** and **testing** ensure reliability

**Start building:**

```python
from kagura import agent

@agent
async def my_first_agent(task: str) -> str:
    """Complete this task: {{ task }}"""
    pass

result = await my_first_agent("Summarize quantum computing in 3 sentences")
print(result)
```

Happy coding with Kagura AI! 🎉
