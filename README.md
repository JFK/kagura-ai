# Kagura AI

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

> **Build Production-Ready AI Agents in One Line of Python**

Kagura AI is the simplest way to build AI agents with real capabilities: memory, web search, code execution, and multimodal analysis - all with a single `@agent` decorator.

**3 reasons to choose Kagura AI:**
1. 🎯 **Simplest API** - One decorator, type hints, done
2. 🚀 **Production-Ready** - Memory, web, multimodal built-in
3. 💡 **Best Developer Experience** - Interactive chat, full type safety, 1,300+ tests

```bash
pip install kagura-ai[full]
```

[Documentation](https://www.kagura-ai.com/) • [Examples](./examples/) • [API Reference](https://www.kagura-ai.com/en/api/)

---

## ⚡ Quick Start

### Your First Agent (30 seconds)

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

That's it. No configuration files, no complex setup - just Python.

### Interactive Chat (Claude Code Experience)

```bash
kagura chat
```

Then try:
```
[You] > Read report.pdf and summarize in 3 points
[AI] > (analyzes PDF with Gemini, provides summary)

[You] > Search the web for similar reports
[AI] > (uses Brave Search, finds related content)

[You] > Analyze this image: chart.png
[AI] > (analyzes image with Gemini)
```

All file operations, web search, and multimodal analysis work automatically.

---

## 🌟 Why Kagura AI?

### vs Other Frameworks

| Feature | LangChain | AutoGen | CrewAI | **Kagura AI** |
|---------|-----------|---------|--------|--------------|
| **Setup Simplicity** | 50+ lines | 30+ lines | YAML config | **1 decorator** ✅ |
| **Type Safety** | ❌ No | ❌ No | ❌ No | **✅ Full (pyright strict)** |
| **Code Execution** | ⚠️ Manual | ⚠️ Limited | ❌ No | **✅ Built-in sandbox** |
| **Memory System** | ⚠️ Manual | ⚠️ Basic | ⚠️ Basic | **✅ 3-tier (Context/Persistent/RAG)** |
| **Web Search** | ⚠️ Plugin | ❌ No | ⚠️ Limited | **✅ Built-in (Brave + DDG)** |
| **Multimodal** | ⚠️ Manual | ❌ No | ❌ No | **✅ Built-in (Gemini)** |
| **Testing Framework** | ⚠️ Manual | ❌ No | ❌ No | **✅ Built-in (AgentTestCase)** |
| **Interactive Chat** | ❌ No | ❌ No | ❌ No | **✅ Claude Code-like** |

### What Makes Kagura Different?

#### 1. Truly Python-First

**Other frameworks:**
```yaml
# config.yaml - 20+ lines
agent:
  name: my_agent
  llm:
    provider: openai
    model: gpt-4
  tools: [web_search, calculator]
  memory:
    type: chromadb
    config: {...}
```

**Kagura AI:**
```python
@agent(enable_memory=True, tools=["web_search"])
async def my_agent(query: str) -> str:
    '''Answer: {{ query }}'''
```

#### 2. Type-Safe Structured Output

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    keywords: list[str]
    score: float

@agent
async def analyze(text: str) -> Analysis:
    '''Analyze: {{ text }}'''

result = await analyze("I love Python!")
print(result.sentiment)  # Type-safe! IDE autocomplete works!
```

#### 3. Real Production Features

Most frameworks require manual integration for:
- ❌ Memory management
- ❌ Web search
- ❌ Image/PDF analysis
- ❌ Code execution

**Kagura AI includes all of this out-of-the-box:**

```python
@agent(
    enable_memory=True,        # 3-tier memory
    tools=["web_search"],       # Web search built-in
    enable_code_execution=True  # Safe sandbox
)
async def research_agent(topic: str) -> str:
    '''Research {{ topic }}. You can:
    - Remember our conversation
    - Search the web for latest info
    - Write Python code to analyze data
    '''
```

---

## 🎨 See It in Action

### Example 1: Data Analysis with Code Execution

```python
@agent
async def data_analyst(question: str, csv_path: str) -> str:
    '''Analyze {{ csv_path }} and answer: {{ question }}

    You can write Python code using pandas, matplotlib, numpy.
    '''

result = await data_analyst("What's the sales trend?", "sales.csv")
# AI writes pandas code, executes safely, returns insights with charts
```

### Example 2: Multimodal RAG (Images + PDFs)

```python
@agent(enable_memory=True)
async def document_qa(question: str) -> str:
    '''Answer based on documents in ./docs/

    Available tools:
    - rag_search(query): Search indexed documents (PDFs, images)
    '''

# Index documents once
from kagura.core.memory import MemoryRAG
rag = MemoryRAG()
await rag.index_directory("./docs")

# Ask questions
result = await document_qa("What does the diagram in Q3-report.pdf show?")
# AI searches PDFs and images, finds diagram, analyzes with Gemini
```

### Example 3: Web Research Agent

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }}

    Steps:
    1. Search the web for latest information
    2. Fetch and analyze relevant pages
    3. Synthesize findings
    '''

result = await researcher("Python 3.13 new features")
# AI searches web, reads articles, summarizes findings
```

### Example 4: Memory-Aware Conversation

```python
@agent(enable_memory=True, memory_scope="session")
async def assistant(message: str) -> str:
    '''You are a helpful assistant. Remember our conversation.

    User says: {{ message }}'''

# Conversation with memory
await assistant("My favorite color is blue")
await assistant("What's my favorite color?")  # "Your favorite color is blue"
await assistant("Recommend a gift")  # Uses remembered preference
```

---

## 📦 Installation

### Basic

```bash
pip install kagura-ai
```

### With Features (Recommended)

```bash
# All features (memory, web, multimodal, auth, MCP)
pip install kagura-ai[full]

# Or pick what you need:
pip install kagura-ai[ai]    # Memory + Routing + Context Compression
pip install kagura-ai[web]   # Web search + Multimodal (images, PDFs, video)
pip install kagura-ai[auth]  # OAuth2 authentication
pip install kagura-ai[mcp]   # Claude Desktop integration
```

### Environment Setup

```bash
# At least one LLM API key required
export OPENAI_API_KEY=sk-...

# Optional: Web search
export BRAVE_SEARCH_API_KEY=...

# Optional: Multimodal (Gemini)
export GOOGLE_API_KEY=...
```

See [Configuration Guide](docs/en/configuration/environment-variables.md) for all options.

---

## 🚀 Usage

### Option A: Interactive Chat (Easiest)

Perfect for exploring Kagura's capabilities:

```bash
kagura chat
```

**What you can do:**
- 📄 Read and analyze files (PDF, images, code)
- 🌐 Search the web and fetch URLs
- 🎬 Summarize YouTube videos
- 💻 Execute Python code safely
- 🔍 Ask questions about your documents

**Example session:**
```
[You] > Read design.pdf and extract key requirements

[AI] > I'll analyze the PDF for you.

      Key requirements:
      1. User authentication system
      2. Real-time notifications
      3. Mobile responsive design

[You] > Search for best practices for requirement 1

[AI] > (searches web, provides best practices with sources)

[You] > Write sample code for the authentication

[AI] > (generates and shows code)
```

### Option B: Build Agents Programmatically

Perfect for integration and automation:

```python
from kagura import agent
from pydantic import BaseModel

class Report(BaseModel):
    summary: str
    action_items: list[str]
    priority: str

@agent
async def meeting_analyzer(transcript: str) -> Report:
    '''Analyze meeting transcript and extract:
    - Summary
    - Action items
    - Priority level

    Transcript: {{ transcript }}'''

# Use in your app
report = await meeting_analyzer("Today we discussed Q4 goals...")
for item in report.action_items:
    print(f"TODO: {item}")
```

---

## 📚 Learn More

### 5-Minute Tutorials

Start here if you're new:

1. **[Your First Agent](docs/en/tutorials/01-basic-agent.md)** - Hello World in 2 minutes
2. **[Structured Output](docs/en/tutorials/02-pydantic.md)** - Type-safe responses with Pydantic
3. **[Interactive Chat](docs/en/tutorials/03-chat.md)** - Claude Code-like experience
4. **[Memory & Context](docs/en/tutorials/04-memory.md)** - Remember conversations
5. **[Web & Multimodal](docs/en/tutorials/05-web-multimodal.md)** - Search web, analyze images

### Real-World Examples

See [examples/](./examples/) for 36+ examples:

- **[Data Analysis](examples/06_advanced/data_analysis.py)** - Pandas + AI
- **[Web Research](examples/05_web/research_agent.py)** - Web search + synthesis
- **[Image Analysis](examples/04_multimodal/image_analysis.py)** - Gemini-powered vision
- **[Document QA](examples/04_multimodal/multimodal_rag_demo.py)** - RAG with PDFs & images
- **[Real-World Use Cases](examples/08_real_world/)** - Production-ready examples

### Documentation

- **[Full Documentation](https://www.kagura-ai.com/)** - Complete guides
- **[API Reference](docs/en/api/)** - All decorators, classes, functions
- **[Configuration](docs/en/configuration/)** - Environment variables, LLM models
- **[MCP Integration](docs/en/guides/mcp-integration.md)** - Use in Claude Desktop

---

## 🛠️ Advanced Features

### Memory Management

3-tier memory system for context-aware agents:

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''You are a helpful assistant. {{ message }}'''

# Automatically remembers:
# - Context Memory: Current conversation
# - Persistent Memory: User preferences
# - RAG Memory: Semantic search across history
```

### Agent Routing

Automatically select the right agent:

```python
from kagura.routing import SemanticRouter

router = SemanticRouter()
router.add_route("translation", translator)
router.add_route("code_review", reviewer)
router.add_route("data_analysis", analyzer)

# Intelligent routing
agent = await router.route("Translate this to Japanese")
# Automatically selects 'translator'
```

### Multimodal RAG

Index and search images, PDFs, videos:

```python
from kagura.core.memory import MultimodalRAG

rag = MultimodalRAG()

# Index documents (PDFs, images, videos)
await rag.index_directory("./knowledge_base")

# Search semantically
results = await rag.search("quarterly sales chart")
# Finds relevant charts in PDFs/images
```

### Web Integration

Built-in web search and scraping:

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using:
    - web_search(query): Search the web (Brave/DuckDuckGo)
    - web_fetch(url): Fetch webpage content
    '''

result = await researcher("Latest Python frameworks")
```

### MCP Integration

Use your Kagura agents in Claude Desktop:

```bash
# One-time setup
kagura mcp start
kagura mcp config claude

# Then use in Claude Desktop!
# All your @agent functions become Claude tools
```

### Testing Framework

Built-in testing utilities:

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_sentiment_analysis(self):
        result = await my_agent("I love this!")

        # Semantic assertions
        self.assert_semantic_match(
            result,
            "positive sentiment"
        )
```

### Observability

Track performance and costs automatically:

```bash
kagura monitor stats
# Shows execution count, duration, costs per agent

kagura monitor cost --group-by agent
# Cost breakdown by agent
```

---

## 🎯 Core Features

### Framework Basics
- ✅ **@agent Decorator** - One-line AI agent creation
- ✅ **@tool Decorator** - Turn Python functions into agent tools
- ✅ **@workflow Decorator** - Multi-agent orchestration
- ✅ **Jinja2 Templates** - Dynamic prompts in docstrings
- ✅ **Type-Safe Parsing** - Automatic response parsing with Pydantic
- ✅ **Multi-LLM Support** - OpenAI, Anthropic, Google, 100+ providers via LiteLLM

### Production Features
- ✅ **Memory Management** - 3-tier system (Context/Persistent/RAG)
- ✅ **Agent Routing** - Semantic/Intent/Memory-aware routing
- ✅ **Code Execution** - Secure Python sandbox (AST validation)
- ✅ **Web Integration** - Search (Brave/DuckDuckGo) + scraping
- ✅ **Multimodal RAG** - Images, PDFs, audio, video (Gemini-powered)
- ✅ **Context Compression** - Token management for long conversations
- ✅ **Testing Framework** - AgentTestCase with semantic assertions
- ✅ **Observability** - Telemetry, cost tracking, monitoring

### Developer Experience
- ✅ **Interactive Chat** - Claude Code-like experience (`kagura chat`)
- ✅ **MCP Integration** - Use agents in Claude Desktop
- ✅ **Full Type Safety** - pyright strict mode, 100% typed
- ✅ **1,300+ Tests** - 90%+ coverage
- ✅ **36+ Examples** - From basic to real-world use cases

---

## 💡 Real-World Examples

### Data Analysis with Code

```python
@agent
async def data_scientist(question: str, data_file: str) -> str:
    '''Analyze {{ data_file }} and answer: {{ question }}

    You can write Python code using pandas, numpy, matplotlib.
    Code will be executed in a secure sandbox.
    '''

result = await data_scientist(
    "What's the monthly sales trend?",
    "sales.csv"
)
# AI writes pandas code, generates chart, returns insights
```

### Document Intelligence

```python
@agent(enable_memory=True)
async def doc_assistant(question: str) -> str:
    '''Answer questions about documents in ./knowledge_base/

    Use rag_search(query) to find relevant information from:
    - PDFs, Images, Videos (Gemini-powered analysis)
    - Semantic search with ChromaDB
    '''

# Ask questions across all documents
result = await doc_assistant(
    "Summarize all Q3 financial reports"
)
```

### Web Research Assistant

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }}:
    1. Search the web for latest information
    2. Fetch and analyze relevant articles
    3. Synthesize findings with sources

    Tools:
    - web_search(query): Search web (Brave Search / DuckDuckGo)
    - web_fetch(url): Fetch webpage content
    '''

result = await researcher("AI regulation 2025")
# Returns comprehensive research with sources
```

### Conversational Agent with Memory

```python
@agent(enable_memory=True, memory_scope="user")
async def personal_assistant(message: str) -> str:
    '''You are a personal assistant. Remember user preferences.

    Message: {{ message }}'''

# Multi-turn conversation with context
await personal_assistant("I prefer concise answers")
await personal_assistant("What's the capital of France?")
# "Paris." (remembers preference for brevity)

await personal_assistant("What did I say about my preference?")
# "You prefer concise answers."
```

---

## 🎓 Learn by Example

Browse [36+ examples](./examples/) organized by category:

- **[01_basic](examples/01_basic/)** - Hello World, templates, type hints (7 examples)
- **[02_memory](examples/02_memory/)** - Memory system, RAG (6 examples)
- **[03_routing](examples/03_routing/)** - Agent routing, selection (4 examples)
- **[04_multimodal](examples/04_multimodal/)** - Images, PDFs, audio, video (5 examples)
- **[05_web](examples/05_web/)** - Web search, scraping, YouTube (5 examples)
- **[06_advanced](examples/06_advanced/)** - Workflows, testing, hooks (4 examples)
- **[07_presets](examples/07_presets/)** - Pre-built agents (3 examples)
- **[08_real_world](examples/08_real_world/)** - Production use cases (2 examples)

Each example is fully documented and tested.

---

## 🚀 Advanced Usage

### Custom Tools

```python
from kagura import tool, agent

@tool
def search_database(query: str) -> list[dict]:
    '''Search internal database'''
    return db.query(query)

@agent(tools=[search_database])
async def data_agent(question: str) -> str:
    '''Answer using database: {{ question }}

    Use search_database(query) to find information.
    '''
```

### Multi-Agent Workflows

```python
from kagura import workflow

@workflow.stateful
async def research_workflow(topic: str) -> dict:
    '''Complete research workflow'''

    # Step 1: Plan
    plan = await planner_agent(topic)

    # Step 2: Research each point
    findings = []
    for point in plan.points:
        result = await research_agent(point)
        findings.append(result)

    # Step 3: Synthesize
    summary = await synthesis_agent(findings)

    return {"plan": plan, "findings": findings, "summary": summary}
```

### MCP Server (Claude Desktop Integration)

```bash
# Start MCP server
kagura mcp start

# Configure Claude Desktop
kagura mcp config claude

# Now use your agents in Claude Desktop!
```

All your `@agent` functions become available as Claude tools automatically.

---

## 📚 Documentation

### Getting Started
- [Installation Guide](docs/en/installation.md)
- [Quick Start (5 min)](docs/en/quickstart.md)
- [Interactive Chat Tutorial](docs/en/tutorials/03-chat.md)

### Tutorials
- [Basic Agent Creation](docs/en/tutorials/01-basic-agent.md)
- [Structured Output with Pydantic](docs/en/tutorials/02-pydantic.md)
- [Memory Management](docs/en/tutorials/04-memory.md)
- [Web & Multimodal](docs/en/tutorials/05-web-multimodal.md)
- [Code Execution](docs/en/tutorials/07-code-execution.md)

### Guides
- [Memory Management](docs/en/guides/memory-management.md)
- [Agent Routing](docs/en/guides/routing.md)
- [Multimodal RAG](docs/en/guides/multimodal-rag.md)
- [Web Integration](docs/en/guides/web-integration.md)
- [MCP Integration](docs/en/guides/mcp-integration.md)
- [Testing Agents](docs/en/guides/testing.md)

### Reference
- [API Reference](docs/en/api/)
- [Configuration](docs/en/configuration/)
- [Examples](./examples/)

---

## 🏗️ Architecture

Kagura AI is built on proven technologies:

- **LLM Integration**: [LiteLLM](https://github.com/BerriAI/litellm) (100+ providers)
- **Memory**: [ChromaDB](https://www.trychroma.com/) (vector storage)
- **Routing**: [Semantic Router](https://github.com/aurelio-labs/semantic-router)
- **Multimodal**: [Google Gemini API](https://ai.google.dev/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Testing**: [pytest](https://pytest.org/) + custom framework

All with full type safety (pyright strict) and 1,300+ tests.

---

## 🤝 Contributing

We welcome contributions!

```bash
# Setup
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras

# Run tests
pytest -n auto

# Type check
pyright src/kagura/

# Lint
ruff check src/
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## 📊 Project Stats

- **1,300+ tests** (90%+ coverage)
- **100% typed** (pyright strict mode)
- **36+ examples** (all tested)
- **31+ RFCs** (16+ implemented)
- **Active development** (50+ releases)

---

## 🗺️ Roadmap

### Recently Completed (v2.5.x)
- ✅ Centralized environment variable management
- ✅ CLI simplification (11,000+ lines removed)
- ✅ Context compression system
- ✅ MCP full feature integration
- ✅ Telemetry & observability

### Coming Soon (v2.6.0)
- 🔄 Auto-discovery & intent detection (RFC-033 Phase 1)
- 🔄 Secret management system (RFC-029)
- 🔄 Pre-installed agents collection

### Future (v2.7.0+)
- 🔮 Voice-first interface (RFC-004)
- 🔮 Google Workspace integration (RFC-023)
- 🔮 Multi-agent orchestration (RFC-009)

See [UNIFIED_ROADMAP.md](ai_docs/UNIFIED_ROADMAP.md) for details.

---

## 📄 License

Apache License 2.0 - see [LICENSE](./LICENSE)

---

## 🌸 About the Name

"Kagura (神楽)" is a traditional Japanese performing art that embodies harmony, connection, and creativity - the principles at the heart of this framework.

---

**Built with ❤️ by the Kagura AI community**

[GitHub](https://github.com/JFK/kagura-ai) • [Documentation](https://www.kagura-ai.com/) • [PyPI](https://pypi.org/project/kagura-ai/) • [Discord](https://discord.gg/kagura-ai)
