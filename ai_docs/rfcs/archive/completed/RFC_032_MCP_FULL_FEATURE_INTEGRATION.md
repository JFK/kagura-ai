# RFC-032: MCP Full Feature Integration

**ステータス**: Draft
**作成日**: 2025-10-15
**優先度**: 🔥🔥 Critical (Claude Desktop統合の要)
**関連Issue**: TBD
**依存RFC**: RFC-007 (MCP Integration Phase 1)

---

## 📋 概要

### 問題

現在のKagura MCP実装は**@agentのみ**を公開しており、以下の拡張機能が**全く使えません**：

**❌ 現在MCPで使えない機能**:
1. **@tool デコレータ** - Python関数をツールとして公開
2. **@workflow デコレータ** - マルチエージェントワークフロー
3. **Memory機能** - 会話履歴・長期記憶（MemoryManager, MemoryRAG）
4. **Routing機能** - 自動エージェント選択（AgentRouter）
5. **Multimodal RAG** - 画像・PDF・音声の検索
6. **Web検索** - `@web.enable`デコレータ、検索API
7. **Observability** - Telemetry、コスト追跡
8. **Secret Management** - API Key管理（RFC-029、未実装）
9. **File/Directory操作** - ShellExecutor、ファイル検索
10. **Meta Agent** - エージェント生成機能

**ユーザー影響**:
- ✅ Claude Desktopで全機能を使うには**個別設定が必要** ← 煩雑
- ✅ せっかくの拡張機能が**Claude経由で使えない**
- ✅ 設定ファイルが複雑化（各機能ごとにMCPサーバー追加）

### ユーザーの要望

> **「kagura mcp使えば全ての機能をClaude Desktopから使えるようになると、設定が1つでよいので楽」**

### 解決策

**Unified MCP Server** - 1つのMCPサーバーで全機能を公開

**メリット**:
- ✅ Claude Desktop設定が**1つだけ**で完結
- ✅ 全拡張機能がClaude経由で使える
- ✅ ユーザー体験が劇的に向上

---

## 🎯 目標

### 成功指標

1. **Claude Desktop統合**
   - ✅ `claude_desktop_config.json` **1つだけ**で全機能使用可能
   - ✅ @agent、@tool、@workflowすべてMCP公開
   - ✅ Memory、Routing、Multimodal、Web、すべて利用可能

2. **機能カバレッジ**
   - ✅ **10個の拡張機能**すべてMCP経由で使える
   - ✅ 既存機能との互換性100%
   - ✅ 新規機能も自動的にMCP公開

3. **UX**
   - ✅ セットアップ時間: **5分以下**
   - ✅ 設定ファイル: **1ファイルのみ**
   - ✅ Claude DesktopからKagura全機能にアクセス

---

## 🏗️ アーキテクチャ

### 現在の構成（❌ 問題あり）

```
Claude Desktop
   ↓
MCP Server (kagura mcp start)
   ↓
agent_registry のみ公開
   ├─ @agent デコレータで定義されたエージェント
   └─ （@tool、@workflowは公開されない！）

❌ Memory、Routing、Multimodal等は全く使えない
```

### 改善後の構成（✅ 理想）

```
Claude Desktop
   ↓
Unified MCP Server (kagura mcp start)
   ↓
┌─────────────────────────────────────────────────┐
│  MCP Tools (全機能統合)                          │
├─────────────────────────────────────────────────┤
│ 1. Agents (@agent)                              │
│    - kagura_translate                           │
│    - kagura_summarize                           │
│    - kagura_code_review                         │
│                                                 │
│ 2. Tools (@tool)                                │
│    - kagura_tool_search                         │
│    - kagura_tool_calculator                     │
│    - kagura_tool_file_read                      │
│                                                 │
│ 3. Workflows (@workflow)                        │
│    - kagura_workflow_research                   │
│    - kagura_workflow_data_pipeline              │
│                                                 │
│ 4. Memory Operations                            │
│    - kagura_memory_store                        │
│    - kagura_memory_recall                       │
│    - kagura_memory_search (RAG)                 │
│                                                 │
│ 5. Routing                                      │
│    - kagura_route_query (自動エージェント選択)  │
│                                                 │
│ 6. Multimodal RAG                               │
│    - kagura_multimodal_index                    │
│    - kagura_multimodal_search                   │
│                                                 │
│ 7. Web Search                                   │
│    - kagura_web_search                          │
│    - kagura_web_scrape                          │
│                                                 │
│ 8. Observability                                │
│    - kagura_telemetry_stats                     │
│    - kagura_telemetry_cost                      │
│                                                 │
│ 9. File/Directory Operations                    │
│    - kagura_file_read                           │
│    - kagura_file_write                          │
│    - kagura_dir_list                            │
│    - kagura_shell_exec (安全な実行)             │
│                                                 │
│ 10. Meta Agent                                  │
│    - kagura_meta_create_agent                   │
│    - kagura_meta_validate_agent                 │
└─────────────────────────────────────────────────┘
```

**Claude Desktop設定**:
```json
{
  "mcpServers": {
    "kagura-ai": {
      "command": "kagura",
      "args": ["mcp", "start"]
    }
  }
}
```

**これだけ！** 全機能が使える ✅

---

## 📦 Phase 1: Tool & Workflow Registry統合 (Week 1)

### 実装内容

#### 1.1 MCPサーバー拡張 - Tool対応

```python
# src/kagura/mcp/server.py

from kagura.core.registry import agent_registry
from kagura.core.tool_registry import tool_registry  # NEW
from kagura.core.workflow_registry import workflow_registry  # NEW

def create_mcp_server(name: str = "kagura-ai") -> Server:
    server = Server(name)

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """List all Kagura agents, tools, and workflows"""
        mcp_tools: list[Tool] = []

        # 1. Agents
        agents = agent_registry.get_all()
        for agent_name, agent_func in agents.items():
            input_schema = generate_json_schema(agent_func)
            description = agent_func.__doc__ or f"Kagura agent: {agent_name}"

            mcp_tools.append(Tool(
                name=f"kagura_{agent_name}",
                description=description,
                inputSchema=input_schema,
            ))

        # 2. Tools (NEW)
        tools = tool_registry.get_all()
        for tool_name, tool_func in tools.items():
            input_schema = generate_json_schema(tool_func)
            description = tool_func.__doc__ or f"Kagura tool: {tool_name}"

            mcp_tools.append(Tool(
                name=f"kagura_tool_{tool_name}",
                description=description,
                inputSchema=input_schema,
            ))

        # 3. Workflows (NEW)
        workflows = workflow_registry.get_all()
        for workflow_name, workflow_func in workflows.items():
            input_schema = generate_json_schema(workflow_func)
            description = workflow_func.__doc__ or f"Kagura workflow: {workflow_name}"

            mcp_tools.append(Tool(
                name=f"kagura_workflow_{workflow_name}",
                description=description,
                inputSchema=input_schema,
            ))

        return mcp_tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        """Execute agent, tool, or workflow"""
        args = arguments or {}

        # Route to appropriate registry
        if name.startswith("kagura_tool_"):
            tool_name = name.replace("kagura_tool_", "", 1)
            tool_func = tool_registry.get(tool_name)
            if tool_func is None:
                raise ValueError(f"Tool not found: {tool_name}")

            # Execute tool
            result = tool_func(**args)
            return [TextContent(type="text", text=str(result))]

        elif name.startswith("kagura_workflow_"):
            workflow_name = name.replace("kagura_workflow_", "", 1)
            workflow_func = workflow_registry.get(workflow_name)
            if workflow_func is None:
                raise ValueError(f"Workflow not found: {workflow_name}")

            # Execute workflow
            if inspect.iscoroutinefunction(workflow_func):
                result = await workflow_func(**args)
            else:
                result = workflow_func(**args)
            return [TextContent(type="text", text=str(result))]

        elif name.startswith("kagura_"):
            # Agent (existing logic)
            agent_name = name.replace("kagura_", "", 1)
            agent_func = agent_registry.get(agent_name)
            if agent_func is None:
                raise ValueError(f"Agent not found: {agent_name}")

            if inspect.iscoroutinefunction(agent_func):
                result = await agent_func(**args)
            else:
                result = agent_func(**args)
            return [TextContent(type="text", text=str(result))]

        else:
            raise ValueError(f"Invalid tool name: {name}")

    return server
```

### テスト

```python
# tests/mcp/test_tool_workflow_integration.py

import pytest
from kagura import tool, workflow
from kagura.mcp.server import create_mcp_server

@tool
def calculate_tax(amount: float, rate: float = 0.1) -> float:
    """Calculate tax amount"""
    return amount * rate

@workflow
async def data_pipeline(source: str) -> dict:
    """Run data processing pipeline"""
    return {"source": source, "processed": True}

@pytest.mark.asyncio
async def test_tool_exposed_via_mcp():
    """Test that @tool is exposed via MCP"""
    server = create_mcp_server()

    # List tools
    tools = await server._handlers["list_tools"]()

    # Check tool is present
    tool_names = [t.name for t in tools]
    assert "kagura_tool_calculate_tax" in tool_names

@pytest.mark.asyncio
async def test_workflow_exposed_via_mcp():
    """Test that @workflow is exposed via MCP"""
    server = create_mcp_server()

    tools = await server._handlers["list_tools"]()
    tool_names = [t.name for t in tools]
    assert "kagura_workflow_data_pipeline" in tool_names

@pytest.mark.asyncio
async def test_tool_execution_via_mcp():
    """Test that tool can be executed via MCP"""
    server = create_mcp_server()

    result = await server._handlers["call_tool"](
        "kagura_tool_calculate_tax",
        {"amount": 100.0, "rate": 0.15}
    )

    assert result[0].text == "15.0"

# 20+ more tests...
```

### 完了条件

- [ ] MCPサーバーに@tool、@workflow統合
- [ ] 20+ tests全パス
- [ ] Claude Desktopで動作確認
- [ ] ドキュメント更新

---

## 📦 Phase 2: Built-in Feature Tools (Week 2)

### 実装内容

#### 2.1 Memory Operations

```python
# src/kagura/mcp/builtin/memory.py

from kagura import tool
from kagura.core.memory import MemoryManager

@tool
async def memory_store(
    agent_name: str,
    key: str,
    value: str,
    scope: str = "session"
) -> str:
    """Store information in agent memory

    Args:
        agent_name: Name of the agent
        key: Memory key
        value: Information to store
        scope: Memory scope (session/persistent)

    Returns:
        Confirmation message
    """
    memory = MemoryManager(agent_name=agent_name)

    if scope == "persistent":
        await memory.persistent.store(key, value)
    else:
        memory.working[key] = value

    return f"Stored '{key}' in {scope} memory for {agent_name}"

@tool
async def memory_recall(
    agent_name: str,
    key: str,
    scope: str = "session"
) -> str:
    """Recall information from agent memory

    Args:
        agent_name: Name of the agent
        key: Memory key
        scope: Memory scope (session/persistent)

    Returns:
        Stored value or empty string
    """
    memory = MemoryManager(agent_name=agent_name)

    if scope == "persistent":
        value = await memory.persistent.recall(key)
    else:
        value = memory.working.get(key, "")

    return str(value) if value else ""

@tool
async def memory_search(agent_name: str, query: str, k: int = 5) -> str:
    """Search agent memory using RAG

    Args:
        agent_name: Name of the agent
        query: Search query
        k: Number of results

    Returns:
        JSON string of search results
    """
    from kagura.core.memory import MemoryRAG
    import json

    rag = MemoryRAG(agent_name=agent_name)
    results = await rag.recall_semantic(query, k=k)

    return json.dumps(results, indent=2)
```

#### 2.2 Routing

```python
# src/kagura/mcp/builtin/routing.py

from kagura import tool
from kagura.routing import AgentRouter

@tool
async def route_query(
    query: str,
    router_type: str = "llm",
    agents: list[str] | None = None
) -> str:
    """Route query to appropriate agent

    Args:
        query: User query
        router_type: Router type (llm/keyword/semantic)
        agents: List of agent names to consider

    Returns:
        Selected agent name
    """
    from kagura.routing import LLMRouter, KeywordRouter, SemanticRouter

    if router_type == "llm":
        router = LLMRouter()
    elif router_type == "keyword":
        router = KeywordRouter()
    elif router_type == "semantic":
        router = SemanticRouter()
    else:
        raise ValueError(f"Unknown router type: {router_type}")

    # Register agents if provided
    if agents:
        for agent_name in agents:
            from kagura.core.registry import agent_registry
            agent_func = agent_registry.get(agent_name)
            if agent_func:
                router.register(agent_func)

    # Route query
    selected = await router.route(query)
    return selected.__name__ if selected else "No agent selected"
```

#### 2.3 Multimodal RAG

```python
# src/kagura/mcp/builtin/multimodal.py

from kagura import tool
from pathlib import Path

@tool
async def multimodal_index(
    directory: str,
    collection_name: str = "default"
) -> str:
    """Index multimodal files (images, PDFs, audio)

    Args:
        directory: Directory path to index
        collection_name: RAG collection name

    Returns:
        Indexing status
    """
    from kagura.core.memory import MultimodalRAG

    rag = MultimodalRAG(
        directory=Path(directory),
        collection_name=collection_name
    )

    await rag.index_directory()

    return f"Indexed directory '{directory}' into collection '{collection_name}'"

@tool
async def multimodal_search(
    query: str,
    collection_name: str = "default",
    k: int = 5
) -> str:
    """Search multimodal content

    Args:
        query: Search query
        collection_name: RAG collection name
        k: Number of results

    Returns:
        JSON string of search results
    """
    from kagura.core.memory import MultimodalRAG
    import json

    rag = MultimodalRAG(collection_name=collection_name)
    results = await rag.query(query, k=k)

    return json.dumps(results, indent=2)
```

#### 2.4 Web Search

```python
# src/kagura/mcp/builtin/web.py

from kagura import tool

@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web using Brave Search API

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        JSON string of search results
    """
    from kagura.web import search
    import json

    results = await search(query, max_results=max_results)

    return json.dumps(results, indent=2)

@tool
async def web_scrape(url: str) -> str:
    """Scrape web page content

    Args:
        url: URL to scrape

    Returns:
        Page text content
    """
    from kagura.web import scrape

    content = await scrape(url)

    return content
```

#### 2.5 File/Directory Operations

```python
# src/kagura/mcp/builtin/file_ops.py

from kagura import tool
from pathlib import Path

@tool
def file_read(path: str, encoding: str = "utf-8") -> str:
    """Read file content

    Args:
        path: File path
        encoding: File encoding

    Returns:
        File content
    """
    return Path(path).read_text(encoding=encoding)

@tool
def file_write(path: str, content: str, encoding: str = "utf-8") -> str:
    """Write content to file

    Args:
        path: File path
        content: Content to write
        encoding: File encoding

    Returns:
        Confirmation message
    """
    Path(path).write_text(content, encoding=encoding)
    return f"Wrote {len(content)} characters to {path}"

@tool
def dir_list(path: str = ".", pattern: str = "*") -> str:
    """List directory contents

    Args:
        path: Directory path
        pattern: Glob pattern

    Returns:
        JSON string of file list
    """
    import json
    from pathlib import Path

    files = [str(f) for f in Path(path).glob(pattern)]
    return json.dumps(files, indent=2)

@tool
async def shell_exec(command: str, cwd: str = ".") -> str:
    """Execute shell command safely

    Args:
        command: Shell command
        cwd: Working directory

    Returns:
        Command output
    """
    from kagura.core.shell import ShellExecutor

    executor = ShellExecutor()
    result = await executor.exec(command, cwd=cwd)

    return result.stdout
```

#### 2.6 Observability

```python
# src/kagura/mcp/builtin/observability.py

from kagura import tool

@tool
def telemetry_stats(agent_name: str | None = None) -> str:
    """Get telemetry statistics

    Args:
        agent_name: Filter by agent name (optional)

    Returns:
        JSON string of statistics
    """
    from kagura.observability import EventStore
    import json

    store = EventStore()
    stats = store.get_summary_stats(agent_name=agent_name)

    return json.dumps(stats, indent=2)

@tool
def telemetry_cost(agent_name: str | None = None) -> str:
    """Get cost summary

    Args:
        agent_name: Filter by agent name (optional)

    Returns:
        JSON string of cost breakdown
    """
    from kagura.observability import EventStore
    import json

    store = EventStore()
    executions = store.get_executions(agent_name=agent_name)

    # Calculate costs
    total_cost = sum(
        e.get("metrics", {}).get("total_cost", 0.0)
        for e in executions
    )

    return json.dumps({"total_cost": total_cost, "executions": len(executions)}, indent=2)
```

#### 2.7 Meta Agent

```python
# src/kagura/mcp/builtin/meta.py

from kagura import tool

@tool
async def meta_create_agent(description: str) -> str:
    """Create agent from natural language description

    Args:
        description: Agent description

    Returns:
        Generated agent code
    """
    from kagura.meta import MetaAgent

    meta = MetaAgent()
    spec = await meta.create_spec(description)
    code = meta.generate_code(spec)

    return code
```

### テスト

```python
# tests/mcp/builtin/test_memory_tools.py

import pytest
from kagura.mcp.builtin.memory import memory_store, memory_recall

@pytest.mark.asyncio
async def test_memory_store():
    """Test memory_store tool"""
    result = await memory_store(
        agent_name="test",
        key="user_name",
        value="Alice",
        scope="session"
    )

    assert "Stored" in result
    assert "test" in result

@pytest.mark.asyncio
async def test_memory_recall():
    """Test memory_recall tool"""
    # Store first
    await memory_store("test", "user_name", "Alice", "session")

    # Recall
    result = await memory_recall("test", "user_name", "session")

    assert result == "Alice"

# 50+ more tests across all builtin tools...
```

### 完了条件

- [ ] 7つのBuilt-in機能ツール実装（Memory、Routing、Multimodal、Web、File、Observability、Meta）
- [ ] MCPサーバーに自動登録
- [ ] 50+ tests全パス
- [ ] Claude Desktopで動作確認
- [ ] ドキュメント完成

---

## 📦 Phase 3: Auto-Discovery & Registration (Week 3)

### 実装内容

#### 3.1 自動ツール発見

```python
# src/kagura/mcp/discovery.py

from pathlib import Path
import importlib

def discover_builtin_tools() -> None:
    """Discover and register all builtin MCP tools"""
    from kagura.core.tool_registry import tool_registry

    # Builtin tools directory
    builtin_dir = Path(__file__).parent / "builtin"

    # Import all Python files
    for file in builtin_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue

        module_name = f"kagura.mcp.builtin.{file.stem}"
        importlib.import_module(module_name)

    # Tools are auto-registered via @tool decorator
```

#### 3.2 MCP起動時の自動発見

```python
# src/kagura/cli/mcp.py

from kagura.mcp.discovery import discover_builtin_tools

@mcp.command()
def start(...):
    """Start MCP server"""
    # Auto-discover builtin tools
    discover_builtin_tools()

    # Start server
    # ...
```

### 完了条件

- [ ] Auto-discovery実装
- [ ] MCP起動時に自動登録
- [ ] 10+ tests全パス
- [ ] ドキュメント更新

---

## 📦 Phase 4: Claude Desktop Integration Guide (Week 4)

### 実装内容

#### 4.1 セットアップガイド

```markdown
# docs/en/guides/claude-desktop-integration.md

## Claude Desktop Integration

Use all Kagura features from Claude Desktop with **one simple configuration**.

### Setup

1. **Install Kagura**
   ```bash
   pip install kagura-ai[full]
   ```

2. **Configure Claude Desktop**

   Edit `~/.config/claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "kagura-ai": {
         "command": "kagura",
         "args": ["mcp", "start"]
       }
     }
   }
   ```

3. **Restart Claude Desktop**

That's it! All Kagura features are now available.

### Available Features

#### Agents
- `kagura_translate` - Translate text
- `kagura_summarize` - Summarize text
- `kagura_code_review` - Review code

#### Memory Operations
- `kagura_tool_memory_store` - Store information
- `kagura_tool_memory_recall` - Recall information
- `kagura_tool_memory_search` - Search with RAG

#### Web Search
- `kagura_tool_web_search` - Search the web
- `kagura_tool_web_scrape` - Scrape web pages

#### Multimodal
- `kagura_tool_multimodal_index` - Index files
- `kagura_tool_multimodal_search` - Search images/PDFs/audio

#### File Operations
- `kagura_tool_file_read` - Read files
- `kagura_tool_file_write` - Write files
- `kagura_tool_dir_list` - List directory

#### And more...
- Routing, Observability, Meta Agent, etc.

### Examples

**Example 1: Store & Recall Memory**
```
User: Remember that my favorite color is blue
Claude: [Uses kagura_tool_memory_store]

User: What's my favorite color?
Claude: [Uses kagura_tool_memory_recall] → "blue"
```

**Example 2: Web Search + Summarize**
```
User: What's the latest news about AI?
Claude: [Uses kagura_tool_web_search]
        [Uses kagura_summarize]
```

**Example 3: Multimodal RAG**
```
User: Index my documents folder
Claude: [Uses kagura_tool_multimodal_index]

User: Find documents about Python
Claude: [Uses kagura_tool_multimodal_search]
```
```

### 完了条件

- [ ] Claude Desktop統合ガイド完成
- [ ] セットアップ検証（実際のClaude Desktopで）
- [ ] 使用例10+
- [ ] トラブルシューティングガイド

---

## 📊 成功指標

### 全Phase完了時

**機能カバレッジ**:
- ✅ **10個の拡張機能**すべてMCP公開
- ✅ @agent、@tool、@workflowすべて公開
- ✅ Built-in機能すべて公開

**Claude Desktop統合**:
- ✅ 設定ファイル: **1つだけ**
- ✅ セットアップ時間: **5分以下**
- ✅ 全機能がClaude経由で使用可能

**テスト**:
- ✅ 100+ 新規テスト全パス
- ✅ 既存テスト（1,213+）全パス
- ✅ Claude Desktopで動作確認

---

## 🚀 実装順序

### Week 1: Tool & Workflow Registry統合
- Day 1-2: MCPサーバー拡張
- Day 3-4: テスト（20+ tests）
- Day 5-7: Claude Desktop動作確認、ドキュメント

### Week 2: Built-in Feature Tools
- Day 1: Memory、Routing
- Day 2: Multimodal、Web
- Day 3: File、Observability、Meta
- Day 4-5: テスト（50+ tests）
- Day 6-7: Claude Desktop検証

### Week 3: Auto-Discovery
- Day 1-2: Auto-discovery実装
- Day 3-4: テスト（10+ tests）
- Day 5-7: 統合テスト

### Week 4: ドキュメント・完成
- Day 1-3: Claude Desktop統合ガイド
- Day 4-5: セットアップ検証
- Day 6-7: PR作成、リリース準備

---

## 📝 Migration Guide

### 既存ユーザー向け

**Before (複雑)**:
```json
{
  "mcpServers": {
    "kagura-agents": {...},
    "kagura-tools": {...},
    "kagura-memory": {...},
    "kagura-web": {...}
  }
}
```

**After (シンプル)** ✅:
```json
{
  "mcpServers": {
    "kagura-ai": {
      "command": "kagura",
      "args": ["mcp", "start"]
    }
  }
}
```

---

**このRFCにより、Kagura AIは**Claude Desktop統合のベストプラクティス**となります！**
