# Kagura AI v2.5.0 Examples

This directory contains 36 comprehensive examples demonstrating all features of Kagura AI v2.5.0, from basic agent creation to advanced production patterns.

## 📂 Example Categories

Examples are organized into 8 categories by feature and complexity level:

### 01. Basic (`01_basic/`) - Getting Started

Fundamental concepts and core functionality:

- **hello_world.py** - Your first Kagura agent
- **simple_chat.py** - Basic conversational agent
- **pydantic_parsing.py** - Structured output with Pydantic models
- **code_execution.py** - Safe Python code generation and execution
- **config_usage.py** - Agent configuration and model selection

**Start here if you're new to Kagura AI!**

---

### 02. Memory (`02_memory/`) - Conversation Context

Memory management for stateful agents:

- **working_memory.py** - Short-term context memory
- **session_memory.py** - Persistent session storage
- **persistent_memory.py** - Long-term memory with ChromaDB
- **rag_memory.py** - Retrieval-Augmented Generation

**Learn**: Context windows, memory persistence, semantic search

---

### 03. Routing (`03_routing/`) - Agent Selection

Intelligent routing to the right agent:

- **keyword_routing.py** - Intent-based keyword matching
- **semantic_routing.py** - Embedding-based semantic routing
- **memory_aware_routing.py** - Context-aware routing with conversation history

**Learn**: Multi-agent systems, dynamic agent selection, context handling

---

### 04. Multimodal (`04_multimodal/`) - Beyond Text

Working with images, audio, video, and PDFs:

- **image_analysis.py** - Analyze images with Gemini Vision
- **pdf_processing.py** - Extract and understand PDF documents
- **multimodal_rag.py** - Index and search multimodal content

**Learn**: Vision AI, document understanding, multimodal indexing

---

### 05. Web (`05_web/`) - Internet Integration

Real-time web search and content scraping:

- **web_search.py** - Search the web for current information
- **web_scraping.py** - Extract content from websites
- **hybrid_rag.py** - Combine local files with web data

**Learn**: Web APIs, content extraction, hybrid knowledge sources

---

### 06. Advanced (`06_advanced/`) - Production Patterns

Advanced workflows and optimization:

- **workflows.py** - Multi-step agent orchestration
- **parallel_execution.py** - Concurrent agent execution
- **error_handling.py** - Robust error handling and retry logic
- **caching.py** - Response caching for performance
- **compression.py** - Context compression for long conversations

**Learn**: Workflows, parallelization, error handling, optimization

---

### 07. Presets (`07_presets/`) - Ready-to-Use Templates

Pre-configured agents and patterns:

- **agent_builder.py** - AgentBuilder fluent API
- **testing_agents.py** - Testing framework and assertions
- **observability.py** - Monitoring and cost tracking
- **preset_agents.py** - Common agent patterns

**Learn**: AgentBuilder, testing, monitoring, best practices

---

### 08. Real World (`08_real_world/`) - Complete Applications

Full-featured production examples:

- **chatbot.py** - Complete chatbot with memory and tools
- **code_assistant.py** - AI coding assistant
- **research_assistant.py** - Research tool with web search
- **document_qa.py** - Document Q&A with multimodal RAG
- **multi_agent_system.py** - Coordinated multi-agent system

**Learn**: Production architectures, feature integration, deployment patterns

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
   # or
   export GOOGLE_API_KEY="your-key-here"
   ```

3. **Optional extras for advanced features:**
   ```bash
   # AI features (memory, routing, compression)
   pip install kagura-ai[ai]

   # Web & multimodal features
   pip install kagura-ai[web]

   # All features
   pip install kagura-ai[full]
   ```

### Run Examples

```bash
# Basic examples
python examples/01_basic/hello_world.py
python examples/01_basic/simple_chat.py

# Memory examples
python examples/02_memory/working_memory.py

# Routing examples
python examples/03_routing/keyword_routing.py

# Multimodal examples (requires GOOGLE_API_KEY)
python examples/04_multimodal/image_analysis.py

# Web examples
python examples/05_web/web_search.py

# Advanced examples
python examples/06_advanced/workflows.py

# Presets examples
python examples/07_presets/agent_builder.py

# Real-world examples
python examples/08_real_world/chatbot.py
```

---

## 📚 Learning Paths

### Path 1: Beginner (1-2 hours)

For developers new to Kagura AI:

1. **01_basic/hello_world.py** - Understand `@agent` decorator
2. **01_basic/simple_chat.py** - Build a conversational agent
3. **01_basic/pydantic_parsing.py** - Learn structured outputs
4. **01_basic/code_execution.py** - Explore code generation

**Goal**: Understand core concepts and build your first agents

---

### Path 2: Intermediate (2-3 hours)

For building stateful, intelligent agents:

1. **02_memory/** - All memory examples
2. **03_routing/** - All routing examples
3. **07_presets/agent_builder.py** - Learn the fluent API
4. **07_presets/testing_agents.py** - Test your agents

**Goal**: Build agents with memory and intelligent routing

---

### Path 3: Advanced (3-4 hours)

For production-ready systems:

1. **04_multimodal/** - Multimodal understanding
2. **05_web/** - Web integration
3. **06_advanced/** - Workflows and optimization
4. **07_presets/observability.py** - Monitoring and cost tracking
5. **08_real_world/** - Complete applications

**Goal**: Build production-ready, feature-rich systems

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

### 2. Agent with Memory

```python
from kagura import agent

@agent(
    model="gpt-4o-mini",
    enable_memory=True,
    memory_scope="session"
)
async def chatbot(message: str, memory) -> str:
    '''You are a helpful assistant. User says: {{ message }}'''
    pass
```

### 3. Multimodal Agent

```python
from kagura import agent
from pathlib import Path

@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./docs")
)
async def docs_assistant(query: str, rag) -> str:
    '''Answer questions about documentation: {{ query }}'''
    pass
```

### 4. Web-Enabled Agent

```python
from kagura import agent
from kagura.web import web_search

async def search_tool(query: str) -> str:
    return await web_search(query)

@agent(
    model="gpt-4o-mini",
    tools=[search_tool]
)
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web search'''
    pass
```

### 5. Agent Routing

```python
from kagura import agent
from kagura.routing import AgentRouter

@agent
async def coder(request: str) -> str:
    '''Write code for: {{ request }}'''
    pass

@agent
async def translator(text: str, lang: str) -> str:
    '''Translate {{ text }} to {{ lang }}'''
    pass

router = AgentRouter()
router.register(coder, intents=["code", "program", "write"])
router.register(translator, intents=["translate", "翻訳"])

# Automatic routing
result = await router.route("Write a function to sort a list")
```

### 6. Testing Agents

```python
import pytest
from kagura import agent
from kagura.testing import AgentTestCase

@agent
async def greeter(name: str) -> str:
    '''Greet {{ name }}'''
    pass

class TestGreeter(AgentTestCase):
    agent = greeter

    @pytest.mark.asyncio
    async def test_greeting(self):
        result = await self.agent("Alice")
        self.assert_contains(result, "Alice")
        self.assert_not_empty(result)
```

---

## 📖 Documentation

### API References

- [@agent Decorator](../docs/en/api/agent.md)
- [Memory Management](../docs/en/api/memory.md)
- [Agent Routing](../docs/en/api/routing.md)
- [Context Compression](../docs/en/api/compression.md)
- [Testing Framework](../docs/en/api/testing.md)
- [Observability](../docs/en/api/observability.md)

### Tutorials

- [Quick Start](../docs/en/quickstart.md)
- [Memory Management](../docs/en/tutorials/08-memory-management.md)
- [Agent Routing](../docs/en/tutorials/09-agent-routing.md)
- [Multimodal RAG](../docs/en/tutorials/13-multimodal-rag.md)
- [Testing Agents](../docs/en/tutorials/14-testing.md)

### Guides

- [Chat Multimodal](../docs/en/guides/chat-multimodal.md)
- [Web Integration](../docs/en/guides/web-integration.md)
- [Full-Featured Mode](../docs/en/guides/full-featured-mode.md)
- [Context Compression](../docs/en/guides/context-compression.md)

---

## 💡 Tips and Best Practices

### Development

**Use type hints for automatic parsing:**
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent
async def extract_person(text: str) -> Person:
    '''Extract person from: {{ text }}'''
    pass
```

**Enable memory for conversational agents:**
```python
@agent(enable_memory=True, memory_scope="session")
async def chatbot(message: str, memory) -> str:
    '''Conversational assistant'''
    pass
```

**Use tools for external functionality:**
```python
@agent(tools=[search_web, calculate, send_email])
async def assistant(request: str) -> str:
    '''Smart assistant with tools'''
    pass
```

### Testing

**Mock LLM responses for fast tests:**
```python
from kagura.testing import LLMMock

with LLMMock("Mocked response"):
    result = await agent("test input")
```

**Use semantic assertions:**
```python
self.assert_contains(result, "keyword")
self.assert_matches_regex(result, r"pattern")
```

### Production

**Monitor costs:**
```bash
kagura monitor cost
kagura monitor stats --agent my_agent
```

**Implement retry logic:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def call_agent():
    return await agent("input")
```

**Use context compression for long conversations:**
```python
from kagura.core.compression import ContextMonitor

monitor = ContextMonitor(counter, max_tokens=10000)
usage = monitor.check_usage(messages)

if usage.should_compress:
    # Implement compression strategy
    pass
```

---

## 🛠️ CLI Commands

### Chat REPL

```bash
# Basic chat
kagura chat

# With memory
kagura chat --enable-memory

# With multimodal RAG
kagura chat --enable-multimodal --dir ./docs

# With web search
kagura chat --enable-web

# Full-featured mode
kagura chat --full --dir ./docs
```

### Monitoring

```bash
# Live monitoring dashboard
kagura monitor

# Execution list
kagura monitor list

# Statistics
kagura monitor stats

# Cost tracking
kagura monitor cost

# Execution trace
kagura monitor trace <execution_id>
```

### Testing

```bash
# Run all examples
pytest examples/ -v

# Run specific category
pytest examples/01_basic/ -v

# With coverage
pytest examples/ --cov=kagura --cov-report=html

# Parallel execution
pytest examples/ -n auto
```

---

## ❓ FAQ

### General

**Q: Which LLM providers are supported?**

A: Kagura uses LiteLLM, supporting OpenAI, Anthropic, Google, Azure, Ollama, and 100+ providers.

**Q: Do I need API keys for all examples?**

A: Most examples work with any provider (OpenAI, Anthropic). Multimodal examples require `GOOGLE_API_KEY`.

**Q: Can I use these examples in production?**

A: These are learning examples. For production, add proper error handling, logging, monitoring, and security measures.

### Features

**Q: What's the difference between memory types?**

A:
- **Working memory**: Short-term (last N messages)
- **Session memory**: Persistent across runs (ChromaDB)
- **RAG memory**: Semantic search across documents

**Q: How do I switch between LLM providers?**

A: Set the `model` parameter:
```python
@agent(model="gpt-4o")  # OpenAI
@agent(model="claude-3-5-sonnet")  # Anthropic
@agent(model="gemini/gemini-1.5-flash")  # Google
```

**Q: Is code execution safe?**

A: The executor has security constraints (no file I/O, network, dangerous imports), but use with caution in production.

### Installation

**Q: What extras do I need for specific features?**

A:
- Memory, Routing, Compression → `pip install kagura-ai[ai]`
- Multimodal, Web Search → `pip install kagura-ai[web]`
- OAuth2 Authentication → `pip install kagura-ai[auth]`
- All features → `pip install kagura-ai[full]`

---

## 🤝 Contributing

Want to add more examples? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Example Guidelines

Each example should:
- Have clear, runnable code
- Include comprehensive docstrings
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

1. **Build your first agent** - Start with `01_basic/`
2. **Add memory** - Explore `02_memory/`
3. **Enable routing** - Try `03_routing/`
4. **Go multimodal** - Check out `04_multimodal/`
5. **Deploy to production** - Study `08_real_world/`

**Happy coding with Kagura AI! 🎉**

---

Built with ❤️ by the Kagura AI community
