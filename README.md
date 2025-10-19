# Kagura AI

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

> **The Python-First AI Agent SDK**

Build production-ready AI agents with one decorator. Full type safety, built-in tools, and comprehensive testing framework.

```bash
pip install kagura-ai[full]
```

---

## ⚡ Quick Start (30 seconds)

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

That's it. One decorator, type hints, done.

---

## 🎯 Why Kagura AI?

### Built for Python Developers

| What You Need | Other SDKs | Kagura AI |
|---------------|------------|-----------|
| **Simple API** | 50+ lines config | **1 decorator** ✅ |
| **Type Safety** | Runtime errors | **pyright strict** ✅ |
| **Memory System** | Manual setup | **Built-in** ✅ |
| **Web Search** | External plugins | **Built-in** ✅ |
| **Code Execution** | Unsafe | **Sandboxed** ✅ |
| **Testing** | DIY | **Framework included** ✅ |

### Designed for Production

```python
from kagura import agent
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    keywords: list[str]
    confidence: float

@agent(enable_memory=True, tools=["web_search"])
async def analyzer(text: str) -> Analysis:
    '''Analyze sentiment and extract keywords from: {{ text }}

    Use web_search(query) if you need current information.
    '''

# Type-safe, memory-enabled, web-connected
result = await analyzer("Latest AI trends")
print(result.sentiment)  # IDE autocomplete works!
```

---

## 🚀 Core Features

### 1. One-Line Agent Creation

```python
@agent
async def summarizer(text: str) -> str:
    '''Summarize in 3 points: {{ text }}'''
```

### 2. Type-Safe Structured Output

```python
from pydantic import BaseModel

class Report(BaseModel):
    summary: str
    action_items: list[str]

@agent
async def meeting_analyzer(transcript: str) -> Report:
    '''Analyze meeting: {{ transcript }}'''

report = await meeting_analyzer("...")
for item in report.action_items:  # Fully typed!
    print(f"TODO: {item}")
```

### 3. Built-in Tools

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using:
    - web_search(query): Brave Search API
    - web_fetch(url): Scrape webpage content
    '''
```

Built-in tools include: file operations, web search, code execution, YouTube data, and more.

### 4. Memory Management

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''You remember our conversation.

    User says: {{ message }}'''

# Multi-turn conversation with context
await assistant("My favorite color is blue")
await assistant("What's my favorite color?")  # Remembers!
```

### 5. Custom Tools

```python
from kagura import tool, agent

@tool
async def search_database(query: str) -> list[dict]:
    '''Search internal database'''
    return db.query(query)

@agent(tools=[search_database])
async def data_agent(question: str) -> str:
    '''Answer using database: {{ question }}'''
```

### 6. Multi-LLM Support

```python
# OpenAI
@agent(model="gpt-4o")
async def translator(text: str) -> str: ...

# Anthropic
@agent(model="claude-3-5-sonnet-20241022")
async def writer(prompt: str) -> str: ...

# Google
@agent(model="gemini/gemini-2.0-flash")
async def analyzer(text: str) -> str: ...
```

100+ models via LiteLLM integration.

---

## 💼 Real-World Use Cases

### SDK Integration Examples

#### Web Application (FastAPI)

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer customer support question: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}
```

#### Data Pipeline

```python
from kagura import agent

@agent(tools=["web_search"])
async def data_enricher(company_name: str) -> dict:
    '''Enrich company data for: {{ company_name }}

    Steps:
    1. Search web for company information
    2. Extract: industry, size, location, description
    3. Return as structured data
    '''

# Use in your ETL pipeline
enriched = await data_enricher("Anthropic")
```

#### Automation Script

```python
from kagura import agent, workflow

@agent
async def email_classifier(email: str) -> str:
    '''Classify email as: urgent/important/spam

    Email: {{ email }}'''

@workflow.chain
async def inbox_automation(emails: list[str]):
    for email in emails:
        category = await email_classifier(email)
        # Route based on category
```

---

## 🎨 Advanced Features

### Multimodal Analysis

```python
@agent
async def image_analyzer(image_path: str, question: str) -> str:
    '''Analyze image and answer: {{ question }}

    Image: {{ image_path }}'''

result = await image_analyzer("chart.png", "What's the trend?")
# Uses Gemini Vision API automatically
```

### Document RAG

```python
from kagura.core.memory import MemoryRAG

@agent(enable_memory=True)
async def doc_qa(question: str) -> str:
    '''Answer based on indexed documents

    Use rag_search(query) to find relevant information.
    '''

# Index once
rag = MemoryRAG()
await rag.index_directory("./docs")

# Query anytime
answer = await doc_qa("What does Q3 report say about sales?")
```

### Agent Testing

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_translation(self):
        result = await translator("Hello", lang="ja")

        # Semantic assertions (LLM-powered)
        self.assert_semantic_match(
            result,
            "Japanese greeting"
        )
```

### Cost Tracking

```python
from kagura.observability import track_cost

@agent
@track_cost
async def expensive_agent(query: str) -> str:
    '''Complex analysis: {{ query }}'''

# Automatic cost tracking
# View with: kagura monitor stats
```

---

## 🎮 Bonus: Interactive Chat

Want to try Kagura without writing code?

```bash
kagura chat
```

You get a Claude Code-like experience with all features built-in:

```
[You] > Read report.pdf and summarize

[AI] > (Analyzes PDF with Gemini Vision)

      Key findings:
      1. Revenue up 23% YoY
      2. New market expansion successful
      3. Engineering team doubled

[You] > Search for similar reports

[AI] > (Uses Brave Search, finds relevant content)

[You] > Create a comparison chart

[AI] > (Writes Python code, executes in sandbox, shows chart)
```

All file operations, web search, code execution, and multimodal analysis work automatically.

---

## 📦 Installation

### Basic

```bash
pip install kagura-ai
```

### With All Features (Recommended)

```bash
pip install kagura-ai[full]  # Memory + Web + Multimodal + Auth + MCP
```

### Pick What You Need

```bash
pip install kagura-ai[ai]    # Memory + Routing + Context Compression
pip install kagura-ai[web]   # Web search + Multimodal
pip install kagura-ai[auth]  # OAuth2
pip install kagura-ai[mcp]   # Claude Desktop integration
```

### Environment Setup

```bash
# At least one LLM API key required
export OPENAI_API_KEY=sk-...

# Optional features
export BRAVE_SEARCH_API_KEY=...  # Web search
export GOOGLE_API_KEY=...         # Multimodal (Gemini)
```

---

## 📚 Documentation

### For Developers (SDK)
- [API Reference](docs/api/) - All decorators, classes, functions
- [SDK Guide](docs/sdk-guide.md) - @agent, @tool, memory, workflows
- [Examples](./examples/) - 30+ code examples

### For Users (Chat)
- [Chat Guide](docs/chat-guide.md) - Interactive chat features
- [Quick Start](docs/quickstart.md) - Get started in 5 minutes

### Integration
- [MCP Integration](docs/en/guides/mcp-integration.md) - Claude Desktop setup
- [Testing Guide](docs/en/guides/testing.md) - Test your agents

---

## 🏗️ Architecture

Built on proven technologies:

- **LLM**: OpenAI SDK (direct) + LiteLLM (100+ providers)
- **Memory**: ChromaDB (vector storage)
- **Validation**: Pydantic v2
- **Testing**: pytest + custom framework
- **Type Safety**: pyright strict mode

**Quality Metrics**:
- 1,300+ tests (90%+ coverage)
- 100% typed
- Production-ready

---

## 🔧 Development

```bash
# Setup
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras

# Test
pytest -n auto

# Type check
pyright src/kagura/

# Lint
ruff check src/
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

---

## 🗺️ Roadmap

### Recently Released (v2.7.x)
- ✅ Streaming support (90% faster UX)
- ✅ User config system (`kagura init`)
- ✅ Personal tools (news, weather, recipes, events)
- ✅ MCP full integration (15 built-in tools)
- ✅ Context compression (handle 10,000+ messages)

### Coming in v3.0
- 🔄 Documentation refresh (SDK-first)
- 🔄 Enhanced Meta Agent (`/create` in chat)
- 🔄 Cost visibility (`/stats` in chat)

### Future (v3.1+)
- 🔮 Auto-discovery & intent detection
- 🔮 Voice interface
- 🔮 Google Workspace integration

---

## 📄 License

Apache License 2.0 - see [LICENSE](./LICENSE)

---

## 🌸 About the Name

"Kagura (神楽)" is traditional Japanese performing art embodying harmony and creativity - principles at the heart of this SDK.

---

**Built with ❤️ for developers who want type-safe AI**

[GitHub](https://github.com/JFK/kagura-ai) • [PyPI](https://pypi.org/project/kagura-ai/) • [Documentation](https://www.kagura-ai.com/)
