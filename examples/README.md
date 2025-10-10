# Kagura AI 2.0 Examples

This directory contains comprehensive examples demonstrating all features of Kagura AI 2.0, from basic agent creation to advanced production patterns.

## 📂 Example Categories

### 🎯 Quick Start Examples (`agents/`)

Basic examples for getting started with Kagura AI:

- **[Simple Chat](agents/simple_chat/)** - Basic conversational agent
- **[Data Extractor](agents/data_extractor/)** - Structured data extraction with Pydantic
- **[Code Generator](agents/code_generator/)** - Safe Python code execution
- **[Workflow Example](agents/workflow_example/)** - Multi-step agent composition

### 🏗️ v2.2.0 Feature Examples

#### [AgentBuilder](agent_builder/) - Fluent API for Agent Creation

Learn how to use the AgentBuilder fluent API to create complex agents with integrated features.

**Examples:**
- `basic_builder.py` - Simple agents with model selection
- `with_memory.py` - Agents with memory (context, persistent, RAG)
- `with_tools.py` - Tool integration and function calling
- `presets.py` - Built-in agent presets

**Key Concepts:** Method chaining, memory types, tool registration, agent presets

---

#### [Testing](testing/) - Agent Testing Framework

Comprehensive testing strategies for non-deterministic AI agents.

**Examples:**
- `test_basic.py` - AgentTestCase and semantic assertions
- `test_with_mocks.py` - Mocking LLM responses for fast tests
- `test_performance.py` - Latency, throughput, and cost testing

**Key Concepts:** AgentTestCase, semantic assertions, mocking, performance benchmarks

---

#### [Observability](observability/) - Monitoring and Cost Tracking

Monitor agent execution, track costs, and analyze performance.

**Examples:**
- `monitored_agent.py` - Telemetry collection and querying
- `cost_tracking.py` - Cost analysis and optimization
- `dashboard_demo.py` - Rich TUI dashboard features

**Key Concepts:** EventStore, Dashboard, telemetry, cost tracking, CLI commands

---

#### [Memory-Aware Routing](memory_routing/) - Context-Aware Agent Selection

Intelligent routing with conversation context and semantic understanding.

**Examples:**
- `context_routing.py` - Context-dependent query handling
- `semantic_routing.py` - RAG-enabled semantic routing

**Key Concepts:** MemoryAwareRouter, context enhancement, pronoun resolution, semantic search

---

#### [Advanced Workflows](advanced_workflows/) - Production Patterns

Build robust, efficient workflows for production environments.

**Examples:**
- `conditional_workflow.py` - Conditional branching and routing
- `parallel_workflow.py` - Parallel execution for performance
- `retry_workflow.py` - Retry logic and error handling

**Key Concepts:** Conditional branching, parallel execution, retry strategies, circuit breakers

---

## 📚 Learning Paths

### Path 1: Getting Started (1-2 hours)

For developers new to Kagura AI:

1. [Simple Chat](agents/simple_chat/) - Understand `@agent` decorator
2. [Data Extractor](agents/data_extractor/) - Learn structured outputs
3. [Code Generator](agents/code_generator/) - Explore code execution
4. [AgentBuilder Basic](agent_builder/basic_builder.py) - Try the fluent API

### Path 2: Production Features (3-4 hours)

For building production-ready agents:

1. [AgentBuilder](agent_builder/) - All examples
2. [Testing](testing/) - All examples
3. [Observability](observability/) - Monitoring and cost tracking
4. [Advanced Workflows](advanced_workflows/) - Robust patterns

### Path 3: Advanced Features (2-3 hours)

For complex systems:

1. [Memory-Aware Routing](memory_routing/) - Context and semantic routing
2. [Advanced Workflows](advanced_workflows/) - All examples
3. [Observability](observability/) - Production monitoring

---

## 🚀 Quick Start

### Prerequisites

1. **Install Kagura AI:**
   ```bash
   pip install kagura-ai
   ```

2. **Set API key:**
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

3. **Optional dependencies:**
   ```bash
   # For RAG features
   pip install chromadb

   # For all examples
   pip install kagura-ai[all]
   ```

### Run Examples

```bash
# Quick start examples
cd examples/agents/simple_chat
python agent.py

# AgentBuilder examples
cd examples/agent_builder
python basic_builder.py

# Testing examples
pytest examples/testing/test_basic.py -v

# Observability examples
cd examples/observability
python monitored_agent.py

# Memory routing examples
cd examples/memory_routing
python context_routing.py

# Advanced workflows
cd examples/advanced_workflows
python conditional_workflow.py
```

---

## 🔧 Common Patterns

### 1. Basic Agent

```python
from kagura import agent

@agent(model="gpt-4o-mini")
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass

result = await my_agent("Hello")
```

### 2. AgentBuilder (Recommended)

```python
from kagura import AgentBuilder

agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .with_memory(type="context", max_messages=50)
    .build()
)

result = await agent("Hello")
```

### 3. Structured Output

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent(model="gpt-4o-mini")
async def extract_person(text: str) -> Person:
    '''Extract person from: {{ text }}'''
    pass
```

### 4. Testing Agents

```python
import pytest
from kagura import agent
from kagura.testing import AgentTestCase

@agent(model="gpt-4o-mini")
async def greeter(name: str) -> str:
    """Greet {{ name }}"""
    pass

class TestGreeter(AgentTestCase):
    agent = greeter

    @pytest.mark.asyncio
    async def test_greeting(self):
        result = await self.agent("Alice")
        self.assert_not_empty(result)
        self.assert_contains(result, "Alice")
```

### 5. Monitoring Agents

```python
from kagura import agent
from kagura.observability import EventStore

@agent(model="gpt-4o-mini")
async def translator(text: str, lang: str) -> str:
    """Translate "{{ text }}" to {{ lang }}"""
    pass

# Use agent...
result = await translator("Hello", "French")

# Check telemetry
store = EventStore()
executions = store.get_executions(agent_name="translator")
print(f"Executed {len(executions)} times")
```

### 6. Memory-Aware Routing

```python
from kagura import agent
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

@agent(model="gpt-4o-mini")
async def translator(text: str, lang: str) -> str:
    """Translate "{{ text }}" to {{ lang }}"""
    pass

memory = MemoryManager(agent_name="router")
router = MemoryAwareRouter(memory=memory, context_window=5)
router.register(translator, intents=["translate"])

# First query
await router.route("Translate 'hello' to French")

# Context-aware follow-up
await router.route("What about Spanish?")  # Understands context
```

### 7. Parallel Workflows

```python
import asyncio
from kagura import agent, workflow

@agent(model="gpt-4o-mini")
async def sentiment(text: str) -> str:
    """Analyze sentiment: {{ text }}"""
    pass

@agent(model="gpt-4o-mini")
async def keywords(text: str) -> str:
    """Extract keywords: {{ text }}"""
    pass

@workflow
async def analyze(text: str) -> dict:
    """Run parallel analysis."""
    sentiment_result, keywords_result = await asyncio.gather(
        sentiment(text),
        keywords(text)
    )
    return {
        "sentiment": sentiment_result,
        "keywords": keywords_result
    }
```

---

## 📖 Documentation

### API References

- [@agent Decorator](../docs/en/api/agent.md)
- [AgentBuilder](../docs/en/api/builder.md)
- [Testing Framework](../docs/en/api/testing.md)
- [Observability](../docs/en/api/observability.md)
- [Memory Management](../docs/en/api/memory.md)
- [Routing](../docs/en/api/routing.md)
- [Workflows](../docs/en/api/workflows.md)

### Tutorials

- [Quick Start](../docs/en/quickstart.md)
- [Installation Guide](../docs/en/installation.md)
- [AgentBuilder Tutorial](../docs/en/tutorials/13-agent-builder.md)
- [Testing Tutorial](../docs/en/tutorials/14-testing.md)
- [Observability Tutorial](../docs/en/tutorials/15-observability.md)

---

## 🏗️ Directory Structure

```
examples/
├── agents/                      # Quick start examples
│   ├── simple_chat/            # Basic conversational agent
│   ├── data_extractor/         # Structured data extraction
│   ├── code_generator/         # Code execution
│   └── workflow_example/       # Multi-step workflows
│
├── agent_builder/              # AgentBuilder fluent API
│   ├── basic_builder.py        # Simple agent creation
│   ├── with_memory.py          # Memory integration
│   ├── with_tools.py           # Tool integration
│   ├── presets.py              # Built-in presets
│   └── README.md
│
├── testing/                    # Testing framework
│   ├── test_basic.py           # Basic testing
│   ├── test_with_mocks.py      # Mocking strategies
│   ├── test_performance.py     # Performance testing
│   └── README.md
│
├── observability/              # Monitoring and cost tracking
│   ├── monitored_agent.py      # Telemetry collection
│   ├── cost_tracking.py        # Cost analysis
│   ├── dashboard_demo.py       # Dashboard features
│   └── README.md
│
├── memory_routing/             # Context-aware routing
│   ├── context_routing.py      # Contextdependent routing
│   ├── semantic_routing.py     # RAG-enabled routing
│   └── README.md
│
├── advanced_workflows/         # Production patterns
│   ├── conditional_workflow.py # Conditional branching
│   ├── parallel_workflow.py    # Parallel execution
│   ├── retry_workflow.py       # Retry logic
│   └── README.md
│
└── README.md                   # This file
```

---

## 💡 Tips and Best Practices

### Development

**Use AgentBuilder for complex agents:**
```python
# ✅ Recommended
agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .with_memory(type="context")
    .with_tools([search_tool])
    .build()
)

# ⚠️ Basic (for simple cases only)
@agent
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass
```

**Enable telemetry for all agents:**
```python
# Telemetry is automatic, just query it
from kagura.observability import EventStore

store = EventStore()
stats = store.get_summary_stats()
print(f"Success rate: {stats['completed']/stats['total_executions']:.1%}")
```

**Use context window for conversational agents:**
```python
memory = MemoryManager(agent_name="chatbot")
router = MemoryAwareRouter(memory=memory, context_window=10)
# Keeps last 10 messages for context
```

### Testing

**Mock LLM responses for fast tests:**
```python
with self.mock_llm_response("Mocked output"):
    result = await agent("input")
    assert result == "Mocked output"
```

**Use semantic assertions:**
```python
# ✅ Flexible
self.assert_contains(result, "key_term")

# ❌ Brittle
assert result == "exact output"  # Will break
```

### Production

**Monitor costs:**
```bash
kagura monitor cost  # Check spending
kagura monitor stats --agent my_agent  # Agent-specific
```

**Implement retry logic:**
```python
for attempt in range(3):
    try:
        return await agent(input)
    except Exception:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Use parallel execution:**
```python
# Run independent tasks in parallel
results = await asyncio.gather(
    agent1(input),
    agent2(input),
    agent3(input)
)
```

---

## 🛠️ CLI Commands

### Monitoring

```bash
# Live monitoring
kagura monitor

# View execution list
kagura monitor list

# View statistics
kagura monitor stats

# View costs
kagura monitor cost

# View specific execution trace
kagura monitor trace <execution_id>
```

### Testing

```bash
# Run all tests
pytest examples/testing/ -v

# Run specific test file
pytest examples/testing/test_basic.py -v

# Run with coverage
pytest examples/testing/ --cov=kagura --cov-report=html

# Skip slow tests
pytest examples/testing/ -v -m "not slow"
```

---

## ❓ FAQ

### General

**Q: Can I use these examples in production?**

A: These examples are for learning. For production, add proper error handling, logging, monitoring, and testing.

**Q: Which LLM providers are supported?**

A: Kagura uses LiteLLM, supporting OpenAI, Anthropic, Google, Azure, Ollama, and 100+ providers.

**Q: How do I switch models?**

A: Set the `model` parameter:
```python
@agent(model="gpt-4o")  # or "claude-3-5-sonnet", "gemini-pro", etc.
async def my_agent(input: str) -> str:
    pass
```

### Features

**Q: Do I need RAG for memory routing?**

A: No, basic context memory works without RAG. RAG enhances semantic understanding but requires ChromaDB: `pip install chromadb`

**Q: How secure is code execution?**

A: The code executor has security constraints (no file I/O, network, dangerous imports), but use with caution in production.

**Q: Can agents call other agents?**

A: Yes! See [workflow_example](agents/workflow_example/) and [advanced_workflows](advanced_workflows/) for composition patterns.

**Q: How much does telemetry cost?**

A: Telemetry is free - it's stored locally in SQLite (`~/.kagura/telemetry.db`).

### Testing

**Q: Why are my tests slow?**

A: Use mocks to avoid real API calls:
```python
with self.mock_llm_response("Mocked"):
    result = await agent("input")
```

**Q: How do I test non-deterministic outputs?**

A: Use semantic assertions:
```python
self.assert_contains(result, "expected_term")
self.assert_matches_regex(result, r"pattern")
```

---

## 🤝 Contributing

Want to add more examples? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Example Guidelines

Each example should:
- Have clear, runnable code
- Include comprehensive README.md
- Follow Kagura coding standards
- Demonstrate best practices
- Include error handling
- Be tested and working

---

## 📝 License

Apache License 2.0 - see [LICENSE](../LICENSE)

---

## 🌟 Next Steps

After exploring these examples:

1. **Build your first agent** using AgentBuilder
2. **Add tests** with AgentTestCase
3. **Monitor performance** with observability tools
4. **Deploy to production** with retry logic and monitoring

**Happy coding with Kagura AI! 🎉**

---

Built with ❤️ by the Kagura AI community
