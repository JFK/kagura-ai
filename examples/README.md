# Kagura AI v3.0 Examples

Comprehensive examples demonstrating Kagura AI v4.0 MCP-first architecture, from basic agent creation to production-ready MCP tools.

---

## 📦 Installation

### Quick Start

```bash
# Install all example dependencies
pip install -e "examples/[all]"
```

### Install by Category

```bash
# Broadlistening Analysis (UMAP, scikit-learn, Plotly)
pip install -e "examples/[broadlistening]"
```

### Environment Setup

```bash
# At least one LLM API key required
export OPENAI_API_KEY=sk-...

# Optional features
export GOOGLE_API_KEY=...         # Multimodal (Gemini)
```

---

## 📂 Example Categories

### 01. Basic (`01_basic/`) - Getting Started

Fundamental concepts and core functionality:

- **hello_world.py** - Your first Kagura agent
- **simple_chat.py** - Basic conversational agent
- **pydantic_parsing.py** - Structured output with Pydantic models
- **code_execution.py** - Safe Python code generation and execution
- **config_usage.py** - Agent configuration and model selection

**Start here if you're new to Kagura AI!**

```bash
python examples/01_basic/hello_world.py
```

---

### 02. Memory (`02_memory/`) - Conversation Context

Memory management for stateful agents:

- **working_memory.py** - Short-term context memory
- **session_memory.py** - Persistent session storage
- **persistent_memory.py** - Long-term memory with ChromaDB
- **rag_memory.py** - Retrieval-Augmented Generation

**Learn**: Context windows, memory persistence, semantic search

```bash
python examples/02_memory/working_memory.py
```

---

### 03. Routing (`03_routing/`) - Agent Selection

Intelligent routing to the right agent:

- **keyword_routing.py** - Intent-based keyword matching
- **semantic_routing.py** - Embedding-based semantic routing

**Learn**: Multi-agent systems, dynamic agent selection

```bash
python examples/03_routing/semantic_routing.py
```

---

### 04. Multimodal (`04_multimodal/`) - Beyond Text

Working with images, audio, video, and PDFs:

- **image_analysis.py** - Analyze images with Gemini Vision
- **pdf_processing.py** - Extract and understand PDF documents
- **multimodal_rag.py** - Index and search multimodal content

**Learn**: Vision AI, document understanding, multimodal indexing

```bash
python examples/04_multimodal/image_analysis.py
```

---

### 05. Web (`05_web/`) - Internet Integration

Real-time web search and content scraping:

- **web_search.py** - Search the web for current information
- **web_scraping.py** - Extract content from websites
- **research_agent.py** - Research assistant with web search

**Learn**: Web APIs, content extraction, real-time data

```bash
python examples/05_web/web_search.py
```

---

### 06. Advanced (`06_advanced/`) - Production Patterns

Advanced workflows and optimization:

- **workflows.py** - Multi-step agent orchestration
- **parallel_execution.py** - Concurrent agent execution
- **error_handling.py** - Robust error handling and retry logic
- **caching.py** - Response caching for performance
- **compression.py** - Context compression for long conversations

**Learn**: Workflows, parallelization, error handling, optimization

```bash
python examples/06_advanced/workflows.py
```

---

### 07. Real World (`07_real_world/`) - Complete Applications

Full-featured production examples:

- **broadlistening_analysis/** - Public comment analysis pipeline (UMAP + KMeans + LLM)
- **code_review_agent.py** - AI code reviewer
- **content_generator.py** - Content generation system
- **customer_support_bot.py** - Customer support chatbot
- **research_assistant.py** - Research tool with web search

**Learn**: Production architectures, feature integration, deployment patterns

```bash
cd examples/07_real_world/broadlistening_analysis
python pipeline.py sample_data.csv --n-clusters 5
```

---

## 🚀 Quick Start Paths

### Path 1: Beginner (1-2 hours)

For developers new to Kagura AI:

1. **01_basic/hello_world.py** - Understand `@agent` decorator
2. **01_basic/simple_chat.py** - Build a conversational agent
3. **01_basic/pydantic_parsing.py** - Learn structured outputs
4. **02_memory/working_memory.py** - Memory management basics

**Goal**: Understand core concepts and build your first agents

---

### Path 2: Advanced (3-4 hours)

For production-ready systems:

1. **02_memory/** - Memory management
2. **03_routing/** - Agent routing
3. **04_multimodal/** - Multimodal understanding
4. **05_web/** - Web integration
5. **06_advanced/** - Workflows and optimization
6. **07_real_world/broadlistening_analysis/** - Complete pipeline

**Goal**: Build production-ready, feature-rich systems

---

## 🔧 Common Patterns

### Pattern 1: Basic Agent

```python
from kagura import agent

@agent(model="gpt-4o-mini")
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''

result = await my_agent("Hello")
```

### Pattern 2: Type-Safe Structured Output

```python
from pydantic import BaseModel
from kagura import agent

class Analysis(BaseModel):
    sentiment: str
    confidence: float
    keywords: list[str]

@agent
async def analyzer(text: str) -> Analysis:
    '''Analyze: {{ text }}'''

result = await analyzer("Great product!")
print(result.sentiment)  # IDE autocomplete works!
```

### Pattern 3: Web-Enabled Agent

```python
from kagura import agent

@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query)'''

result = await researcher("Latest AI trends")
```

### Pattern 4: FastAPI Integration

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer customer support question: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    return await support_bot(question)
```

### Pattern 5: Data Pipeline

```python
from kagura import agent
import pandas as pd

@agent(tools=["web_search"])
async def enrich_company(name: str) -> dict:
    '''Enrich company data for: {{ name }}

    Use web_search(query) to find:
    - Industry, size, location, description
    '''

# Process in parallel
companies = ["Anthropic", "OpenAI", "Google DeepMind"]
tasks = [enrich_company(name) for name in companies]
profiles = await asyncio.gather(*tasks)

df = pd.DataFrame(profiles)
```

---

## 📚 Documentation

### For Developers (SDK)
- [API Reference](../docs/api/) - All decorators, classes, functions
- [SDK Guide](../docs/sdk-guide.md) - @agent, @tool, memory, workflows
- [Testing Guide](../docs/en/tutorials/14-testing.md) - Test your agents

### For Users (Chat)
- [Chat Guide](../docs/chat-guide.md) - Interactive chat features
- [Quick Start](../docs/quickstart.md) - Get started in 5 minutes

### Integration
- [MCP Integration](../docs/en/guides/claude-code-mcp-setup.md) - Claude Desktop setup

---

## 🧪 Testing

All examples include error handling and can be tested:

```bash
# Run all tests
pytest examples/ -v

# Run specific category
pytest examples/01_basic/ -v

# With coverage
pytest examples/ --cov=kagura --cov-report=html

# Parallel execution
pytest examples/ -n auto
```

---

## 💡 Tips and Best Practices

### Development

**Use type hints for automatic parsing**:
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent
async def extract_person(text: str) -> Person:
    '''Extract person from: {{ text }}'''
```

**Enable memory for conversational agents**:
```python
@agent(enable_memory=True, memory_scope="session")
async def chatbot(message: str) -> str:
    '''Conversational assistant'''
```

**Use tools for external functionality**:
```python
@agent(tools=["web_search", "file_read", "code_exec"])
async def assistant(request: str) -> str:
    '''Smart assistant with tools'''
```

### Production

**Monitor costs**:
```bash
kagura monitor cost
kagura monitor stats --agent my_agent
```

**Implement retry logic**:
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def call_agent():
    return await agent("input")
```

**Error handling**:
```python
try:
    result = await agent("input")
except Exception as e:
    logger.error(f"Agent failed: {e}")
    result = fallback_value
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

# Full-featured mode
kagura chat --full --dir ./docs
```

### Monitoring

```bash
# Execution list
kagura monitor list

# Statistics
kagura monitor stats

# Cost tracking
kagura monitor cost
```

---

## ❓ FAQ

### General

**Q: Which LLM providers are supported?**

A: Kagura uses LiteLLM, supporting OpenAI, Anthropic, Google, Azure, Ollama, and 100+ providers.

**Q: Can I use these examples in production?**

A: Examples demonstrate core patterns. For production, add proper error handling, logging, monitoring, and security measures.

### Features

**Q: What's new in v4.0?**

A:
- **MCP-First Architecture** - Universal Memory Platform via MCP
- **REST API** - Production-ready FastAPI server
- **GraphMemory** - Knowledge graph for interaction patterns
- **Streamlined Examples** - Focus on core MCP capabilities

**Q: What's the difference between memory types?**

A:
- **Working memory**: Short-term (last N messages)
- **Session memory**: Persistent across runs (ChromaDB)
- **RAG memory**: Semantic search across documents

**Q: How do I switch between LLM providers?**

A: Set the `model` parameter:
```python
@agent(model="gpt-4o")  # OpenAI
@agent(model="claude-3-5-sonnet-20241022")  # Anthropic
@agent(model="gemini/gemini-2.0-flash")  # Google
```

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
2. **Add tools** - Try `05_web/` for web search
3. **Use MCP** - Set up Kagura MCP Server with Claude Desktop
4. **Deploy to production** - Study `07_real_world/`

**Happy coding with Kagura AI v4.0! 🎉**

---

Built with ❤️ by the Kagura AI community
