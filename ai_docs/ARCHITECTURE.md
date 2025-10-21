# Kagura AI Architecture - v3.0

**Last Updated**: 2025-10-22
**Version**: 3.0

---

## Overview

Kagura AI is a **Python-First AI Agent SDK** - build production-ready AI agents with one `@agent` decorator.

**Design Philosophy**: SDK-first, Chat as bonus

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────┐
│        Developer Interface          │
│  from kagura import agent, tool     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         Core Decorators             │
│  @agent  @tool  @workflow           │
│  (Function transformation layer)    │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│          LLM Integration            │
│  OpenAI SDK (direct) + LiteLLM      │
│  (Multi-provider support)           │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       Built-in Features             │
│  Memory │ Tools │ Testing │ MCP     │
└─────────────────────────────────────┘
```

### Component Layers

**Layer 1: SDK Interface**
- `@agent`, `@tool`, `@workflow` decorators
- Type-safe function transformation
- Jinja2 template rendering

**Layer 2: LLM Backend**
- OpenAI SDK (gpt-*, o1-* models)
- LiteLLM (100+ other providers)
- Hybrid routing for optimal performance

**Layer 3: Built-in Features**
- Memory: 3-tier system (Context/Persistent/RAG)
- Tools: Web search, file ops, code execution
- Testing: AgentTestCase framework
- MCP: Claude Desktop integration (with telemetry)
- Observability: Automatic telemetry & cost tracking

**Layer 4: Bonus Features**
- Interactive Chat (`kagura chat`)
- Real-time monitoring (`kagura monitor`)
- Meta Agent (`/create` command)

---

## Directory Structure

```
src/kagura/
├── __init__.py              # SDK exports
├── core/                    # Core SDK
│   ├── decorators.py        # @agent, @tool, @workflow
│   ├── llm.py               # LLM integration
│   ├── llm_openai.py        # OpenAI SDK (direct)
│   ├── llm_gemini.py        # Gemini SDK (direct)
│   ├── parser.py            # Type-based parsing
│   ├── executor.py          # Code execution
│   ├── memory/              # Memory system
│   ├── compression/         # Context compression
│   ├── tool_registry.py     # Tool management
│   └── workflow_registry.py # Workflow management
│
├── chat/                    # Interactive Chat (bonus)
│   ├── session.py           # ChatSession
│   ├── tools.py             # Chat-specific tools
│   └── shell_tool.py        # Shell execution
│
├── tools/                   # Built-in tools
│   ├── web.py               # Web search, scraping
│   ├── youtube.py           # YouTube tools
│   └── ...
│
├── agents/                  # Built-in agents (personal tools)
│   ├── news.py              # daily_news
│   ├── weather.py           # weather_forecast
│   ├── recipes.py           # search_recipes
│   └── events.py            # find_events
│
├── routing/                 # Agent routing
│   ├── router.py            # AgentRouter
│   └── context_analyzer.py  # Context analysis
│
├── testing/                 # Testing framework
│   ├── testcase.py          # AgentTestCase
│   └── mocking.py           # LLM mocking
│
├── mcp/                     # MCP integration
│   ├── server.py            # MCP server (with telemetry)
│   ├── schema.py            # JSON schema generation
│   └── builtin/             # Built-in MCP tools
│       ├── memory.py        # Memory operations
│       ├── web.py           # Web search
│       └── observability.py # Telemetry access
│
├── cli/                     # CLI commands
│   ├── main.py              # Entry point
│   ├── chat.py              # kagura chat
│   ├── mcp.py               # kagura mcp
│   └── monitor.py           # kagura monitor
│
└── observability/           # Observability
    ├── telemetry.py         # Telemetry collection
    ├── collector.py         # Event collection
    ├── store.py             # Event storage (SQLite)
    ├── dashboard.py         # Rich terminal UI
    ├── instrumentation.py   # Decorator integration
    └── pricing.py           # Cost calculation
```

---

## Core Components

### @agent Decorator

Transforms async functions into AI agents:

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
```

**Flow**:
1. Extract function signature → parameters
2. Render docstring with Jinja2 → prompt
3. Call LLM (OpenAI/LiteLLM) → response
4. Parse response by return type → result

### @tool Decorator

Registers Python functions as agent tools:

```python
@tool
async def search_db(query: str) -> list[dict]:
    '''Search database'''
    return db.query(query)
```

**Features**:
- Auto-registration to tool_registry
- Type validation
- Unified tool management (Chat/MCP/SDK)

### Memory System

3-tier memory architecture:

```
┌─────────────────────────────────┐
│    Context Memory (Short-term)  │
│    - Current conversation        │
│    - Session-scoped              │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Persistent Memory (Long-term)  │
│    - User preferences            │
│    - Key-value storage           │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│     RAG Memory (Semantic)        │
│    - ChromaDB vector search      │
│    - Semantic retrieval          │
└─────────────────────────────────┘
```

---

## Data Flow

### Agent Execution Flow

```
1. User calls agent function
   await translator("Hello", lang="ja")
   ↓
2. Decorator intercepts
   Extract: text="Hello", lang="ja"
   ↓
3. Template rendering
   "Translate to ja: Hello"
   ↓
4. LLM call (OpenAI SDK / LiteLLM)
   → Response: "こんにちは"
   ↓
5. Type-based parsing
   str type → direct return
   ↓
6. Return to user
   "こんにちは"
```

### Tool Execution Flow

```
1. Agent uses tool
   web_search("Python SDK")
   ↓
2. tool_registry lookup
   Find registered tool function
   ↓
3. Tool execution
   Call Brave Search API
   ↓
4. Return result to LLM
   Search results as context
   ↓
5. LLM generates response
   Using tool results
```

---

## Technology Stack

### Core Dependencies
- **Pydantic v2**: Data validation, type parsing
- **OpenAI SDK**: Direct gpt-* model support
- **LiteLLM**: 100+ provider support
- **Jinja2**: Template engine
- **Click**: CLI framework
- **Rich**: Terminal UI

### Optional Dependencies
- **ChromaDB**: Vector storage (memory, RAG)
- **Semantic Router**: Semantic routing
- **Google Generativeai**: Gemini API (multimodal)
- **Brave Search**: Web search
- **MCP SDK**: Model Context Protocol

### Development Tools
- **pytest**: Testing framework
- **pytest-xdist**: Parallel execution
- **pyright**: Type checker (strict mode)
- **ruff**: Linter & formatter
- **uv**: Package manager

---

## Design Principles

### 1. SDK-First

**Primary**: Python SDK for app integration
- One `@agent` decorator
- Full type safety
- Production-ready

**Secondary**: Interactive Chat for exploration
- Try SDK features without code
- Prototype quickly

### 2. Type Safety

- **pyright strict mode**: Zero tolerance
- **Pydantic validation**: Structured output
- **IDE support**: Full autocomplete

### 3. Production-Ready

- **Memory**: Built-in, not manual
- **Tools**: Web search, file ops included
- **Testing**: Framework provided
- **Observability**: Cost tracking automatic

### 4. Simplicity

- No config files
- No complex orchestration
- Focus on core SDK features

---

## MCP & Observability Integration

### Overview

All MCP tool executions are automatically tracked in the observability system, providing unified monitoring across SDK and MCP usage.

### Architecture

```
┌─────────────────────────────────────┐
│      MCP Server (handle_call_tool)  │
│      - Receives tool requests       │
│      - Routes to tool_registry      │
└───────────────┬─────────────────────┘
                │
                ├─→ TelemetryCollector.track_execution()
                │   - Wraps tool execution
                │   - Records start/end time
                │   - Captures errors
                │
                ├─→ Tool Execution
                │   - Execute @tool function
                │   - Collect results
                │
                └─→ TelemetryCollector.record_tool_call()
                    - Store execution metadata
                    - Save to EventStore (SQLite)
                    - Calculate costs
```

### Data Flow

```
1. Claude Desktop → MCP Server
   Tool request: kagura_tool_web_search(query="...")
   ↓
2. MCP Server → Telemetry
   track_execution("mcp_kagura_tool_web_search")
   ↓
3. Tool Execution
   web_search(query="...") → results
   ↓
4. Telemetry Recording
   record_tool_call(name="web_search", duration=1.2s, ...)
   ↓
5. EventStore (SQLite)
   ~/.kagura/telemetry.db
   ↓
6. Dashboard (kagura monitor)
   Real-time monitoring, cost analysis
```

### Monitoring Commands

```bash
# Live monitoring (auto-refresh)
kagura monitor

# Statistics summary
kagura monitor stats

# Cost analysis
kagura monitor cost --group-by agent

# Execution trace
kagura monitor trace <execution_id>

# List recent executions
kagura monitor list --limit 50
```

### Telemetry Data Schema

**EventStore (SQLite)**:
```sql
CREATE TABLE executions (
    id TEXT PRIMARY KEY,              -- exec_abc123
    agent_name TEXT NOT NULL,         -- mcp_kagura_tool_web_search
    started_at REAL NOT NULL,         -- Unix timestamp
    ended_at REAL,
    duration REAL,                    -- Seconds
    status TEXT,                      -- completed/failed
    error TEXT,
    kwargs TEXT,                      -- JSON: tool arguments
    events TEXT,                      -- JSON: [tool_call, llm_call, ...]
    metrics TEXT                      -- JSON: {tool_calls: 1, total_cost: 0.0}
)
```

**Event Types**:
- `tool_call`: Tool execution (name, duration, args)
- `llm_call`: LLM API call (model, tokens, cost)
- `memory_operation`: Memory access (operation, duration)

### Benefits

1. **Unified Monitoring**: SDK and MCP usage in one place
2. **Cost Tracking**: Automatic cost calculation per tool/agent
3. **Performance Analysis**: Identify slow tools
4. **Error Tracking**: Failed executions with stack traces
5. **Usage Analytics**: Most-used tools, execution patterns

### Implementation

Implemented in Issue #339, PR #341:
- `src/kagura/mcp/server.py`: Added telemetry integration to `handle_call_tool()`
- `src/kagura/observability/`: Complete observability system
- `src/kagura/cli/monitor.py`: Monitoring dashboard

---

## Integration Points

### FastAPI

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}
```

### Data Pipelines

```python
@agent(tools=["web_search"])
async def data_enricher(company: str) -> dict:
    '''Enrich data for: {{ company }}'''

enriched = await data_enricher("Anthropic")
```

### Automation Scripts

```python
@agent
async def email_classifier(email: str) -> str:
    '''Classify: {{ email }}'''

for email in inbox:
    category = await email_classifier(email)
```

---

## Security

### Code Execution
- AST validation (no dangerous imports)
- Timeout limits
- Resource constraints
- Sandbox environment

### API Keys
- Environment variables only
- Never logged
- Encrypted storage (OAuth2)

### Tools
- Whitelist-based (approved tools only)
- Type validation
- Error handling

---

## Performance

### CLI Startup
- **Lazy loading**: 98.7% faster (8.8s → 0.1s)
- **Module imports**: On-demand only
- **No heavy deps**: Until actually used

### LLM Calls
- **Direct OpenAI SDK**: For gpt-* models (fastest)
- **LiteLLM fallback**: For other providers
- **Parallel execution**: pytest-xdist (60-80% faster tests)

### Caching
- Search results caching (70% faster, 30-50% cost reduction)
- Memory RAG indexing

---

## Quality Metrics

- **Tests**: 1,300+ (90%+ coverage)
- **Type Safety**: 100% (pyright strict)
- **Documentation**: Comprehensive
- **CI/CD**: Automated testing, deployment

---

**Built with ❤️ for developers who value type safety and simplicity**
