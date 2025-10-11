# RFC-007: MCP Integration - Model Context Protocol統合

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #67
- **優先度**: Very High

## 概要

Kagura AIをAnthropicのModel Context Protocol (MCP)に統合し、Claude Code、Cline、その他のMCP対応ツールと相互運用できるようにします。

### 目標
- Kaguraエージェントを**MCPツール**として公開
- Claude Code内で`mcp install kagura-ai`で即座に利用可能
- Kagura側から**MCPツールを呼び出せる**双方向統合
- 標準プロトコルによるエコシステム拡大

### 非目標
- MCP仕様の独自拡張（標準仕様に準拠）
- 既存のKagura APIの破壊的変更

## モチベーション

### 現在の課題
1. Kaguraエージェントは単体でしか動作しない
2. Claude Code等のツールとの統合が手動
3. エコシステムが孤立している

### 解決するユースケース
- **Claude Code連携**: Claude Code内でKaguraエージェントを直接呼び出し
- **相互運用**: 他のMCP対応ツール（Cline、Zed等）でも利用可能
- **双方向統合**: Kaguraから既存のMCPツール（fetch、filesystem等）を利用
- **標準化**: プロトコル標準化によるメンテナンスコスト削減

### なぜ今実装すべきか
- Anthropic公式のMCP仕様が公開済み
- Claude Code等で既にMCPが採用され始めている
- エコシステムの初期段階で参入すべき

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         MCP Client Applications             │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Claude   │  │  Cline   │  │   Zed    │ │
│  │  Code    │  │          │  │          │ │
│  └────┬─────┘  └─────┬────┘  └────┬─────┘ │
│       │              │             │       │
│       └──────────────┼─────────────┘       │
│                      │                     │
│              MCP Protocol                  │
│                      │                     │
└──────────────────────┼─────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│         Kagura MCP Server                   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    MCP Protocol Handler             │   │
│  │  - tools/list                       │   │
│  │  - tools/call                       │   │
│  │  - resources/list                   │   │
│  │  - prompts/list                     │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │    Agent Registry                   │   │
│  │  - Discover agents                  │   │
│  │  - Schema generation                │   │
│  │  - Execution wrapper                │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│                 ▼                           │
│  ┌─────────────────────────────────────┐   │
│  │    Kagura Core Agents               │   │
│  │  - @agent decorated functions       │   │
│  │  - Custom tools                     │   │
│  │  - Workflows                        │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│      Kagura MCP Client (Optional)           │
│  - Call external MCP tools                  │
│  - Filesystem, fetch, etc.                  │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Kagura MCP Server

KaguraエージェントをMCPツールとして公開：

```python
# src/kagura/mcp/server.py
from mcp import MCPServer
from kagura import agent_registry

server = MCPServer("kagura-ai")

@server.list_tools()
async def list_tools():
    """全てのKaguraエージェントをMCPツールとしてリスト"""
    agents = agent_registry.get_all()

    return [
        {
            "name": f"kagura_{agent.name}",
            "description": agent.description,
            "inputSchema": generate_json_schema(agent.signature)
        }
        for agent in agents
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """エージェントを実行"""
    agent_name = name.replace("kagura_", "")
    agent = agent_registry.get(agent_name)

    result = await agent(**arguments)

    return {
        "content": [
            {
                "type": "text",
                "text": str(result)
            }
        ]
    }
```

#### 2. Agent Auto-Discovery

既存のKaguraエージェントを自動検出：

```python
from kagura import agent
from kagura.mcp import register_as_tool

@agent(model="gpt-4o-mini")
@register_as_tool  # MCPツールとして自動登録
async def analyze_code(code: str, language: str = "python") -> dict:
    """
    Analyze code quality and suggest improvements.

    Args:
        code: Source code to analyze
        language: Programming language

    Returns:
        Analysis results with suggestions
    """
    pass

# 自動的にMCPツールとして公開される：
# - Name: kagura_analyze_code
# - Description: Analyze code quality...
# - Input Schema: {code: string, language?: string}
```

#### 3. MCP Client Integration

Kaguraから外部MCPツールを呼び出し：

```python
from kagura import agent, mcp

@agent(model="gpt-4o-mini")
async def fetch_and_summarize(url: str) -> str:
    """
    Fetch webpage and summarize content.

    Uses MCP tools:
    - fetch: Get webpage content
    - summarize: AI summarization
    """
    # MCPのfetchツールを呼び出し
    content = await mcp.call_tool("fetch", {"url": url})

    # Kaguraのエージェントで要約
    summary = f"Summarize this content: {content}"
    return summary
```

### API設計

#### インストールとセットアップ

```bash
# Kagura MCPサーバーのインストール
pip install kagura-ai[mcp]

# MCPサーバー起動（自動検出モード）
kagura mcp serve

# または設定ファイルで指定
kagura mcp serve --config ~/.kagura/mcp.toml
```

#### Claude Code統合

```json
// Claude Code設定 (~/.config/claude-code/mcp.json)
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "KAGURA_MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

または：

```bash
# Claude Code内で
mcp install kagura-ai

# 自動的に設定が追加される
```

#### カスタムエージェントの公開

```python
# my_agents.py
from kagura import agent
from kagura.mcp import MCPToolConfig

@agent(model="gpt-4o-mini")
@MCPToolConfig(
    name="github_issue_analyzer",
    description="Analyze GitHub issues and generate insights",
    category="development"
)
async def analyze_github_issues(repo: str, since_days: int = 7) -> dict:
    """
    Analyze GitHub issues for {{ repo }} in the last {{ since_days }} days.
    """
    pass

# MCPサーバー起動時に自動検出される
```

### 統合例

#### 例1: Claude Code内でKaguraエージェントを使用

**Claude Codeでの対話:**
```
User: このコードの品質を分析して

Claude: Kaguraのcode analyzerを使います
[MCPツール呼び出し: kagura_analyze_code]

結果:
- 複雑度: 8/10（やや高い）
- 型ヒント: 不足（60%）
- テストカバレッジ: 85%

提案:
1. 関数を分割してください
2. 型ヒントを追加してください
```

#### 例2: Kagura内で外部MCPツールを使用

```python
from kagura import agent, mcp

@agent(model="gpt-4o-mini")
async def research_and_report(topic: str) -> str:
    """
    Research a topic using web search and create a report.
    """
    # 外部MCPツール: brave_search
    search_results = await mcp.call_tool("brave_search", {
        "query": topic,
        "count": 10
    })

    # 外部MCPツール: fetch（各URLの内容取得）
    contents = []
    for result in search_results["results"][:3]:
        content = await mcp.call_tool("fetch", {"url": result["url"]})
        contents.append(content)

    # Kaguraエージェントでレポート生成
    report = f"""
    Create a comprehensive report on: {topic}

    Based on these sources:
    {contents}
    """

    return report
```

#### 例3: エージェント連携

```python
from kagura import agent, workflow, mcp

@workflow.chain
async def code_review_workflow(repo: str, pr_number: int):
    """Complete code review workflow using multiple tools"""

    # 1. GitHub MCP tool: PRの内容取得
    pr_data = await mcp.call_tool("github_get_pr", {
        "repo": repo,
        "pr_number": pr_number
    })

    # 2. Kagura agent: コード分析
    @agent(model="gpt-4o-mini")
    async def analyze(code: str) -> dict:
        """Analyze code: {{ code }}"""
        pass

    analysis = await analyze(pr_data["diff"])

    # 3. Kagura agent: レビューコメント生成
    @agent(model="gpt-4o-mini")
    async def generate_review(analysis: dict) -> str:
        """Generate review comment from: {{ analysis }}"""
        pass

    comment = await generate_review(analysis)

    # 4. GitHub MCP tool: コメント投稿
    await mcp.call_tool("github_post_comment", {
        "repo": repo,
        "pr_number": pr_number,
        "body": comment
    })

    return {"status": "completed", "comment": comment}
```

## 実装計画

### Phase 1: MCP Server (v2.2.0)
- [ ] MCP Protocolの実装（tools/list, tools/call）
- [ ] Kaguraエージェントの自動検出
- [ ] JSON Schema生成
- [ ] `kagura mcp serve` コマンド

### Phase 2: Claude Code Integration (v2.3.0)
- [ ] Claude Code設定の自動生成
- [ ] `mcp install kagura-ai` 対応
- [ ] インストーラースクリプト
- [ ] ドキュメント・サンプル

### Phase 3: MCP Client (v2.4.0)
- [ ] 外部MCPツール呼び出し
- [ ] `mcp.call_tool()` API
- [ ] MCPツールの自動検出
- [ ] エラーハンドリング

### Phase 4: Advanced Features (v2.5.0)
- [ ] Resources対応（ファイル、ドキュメント）
- [ ] Prompts対応（テンプレート共有）
- [ ] Sampling対応（LLM呼び出し委譲）
- [ ] パフォーマンス最適化

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
mcp = [
    "mcp>=0.1.0",              # MCP SDK
    "jsonschema>=4.20.0",      # JSON Schema validation
    "pydantic>=2.10.0",        # Schema generation
]
```

### MCP仕様準拠

```python
# src/kagura/mcp/protocol.py
from mcp.server import Server
from mcp.types import Tool, TextContent

class KaguraMCPServer(Server):
    """Kagura MCP Server implementation"""

    async def list_tools(self) -> list[Tool]:
        """List all available Kagura agents as tools"""
        from kagura.core.registry import agent_registry

        tools = []
        for agent_name, agent_func in agent_registry.items():
            schema = self._generate_input_schema(agent_func)

            tools.append(Tool(
                name=f"kagura_{agent_name}",
                description=agent_func.__doc__ or f"Kagura agent: {agent_name}",
                inputSchema=schema
            ))

        return tools

    async def call_tool(self, name: str, arguments: dict) -> list[TextContent]:
        """Execute a Kagura agent"""
        from kagura.core.registry import agent_registry

        agent_name = name.replace("kagura_", "")
        agent_func = agent_registry.get(agent_name)

        if not agent_func:
            raise ValueError(f"Unknown agent: {agent_name}")

        result = await agent_func(**arguments)

        return [
            TextContent(
                type="text",
                text=str(result)
            )
        ]
```

### Agent Registry

```python
# src/kagura/core/registry.py
from typing import Callable, Dict
import inspect

class AgentRegistry:
    """Global registry for all Kagura agents"""

    def __init__(self):
        self._agents: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """Register an agent"""
        self._agents[name] = func

    def get(self, name: str) -> Callable | None:
        """Get agent by name"""
        return self._agents.get(name)

    def get_all(self) -> Dict[str, Callable]:
        """Get all registered agents"""
        return self._agents.copy()

    def auto_discover(self, module_path: str):
        """Auto-discover agents in a module"""
        import importlib
        module = importlib.import_module(module_path)

        for name, obj in inspect.getmembers(module):
            if hasattr(obj, '_is_agent'):
                self.register(name, obj)

# Global instance
agent_registry = AgentRegistry()
```

### 設定ファイル

`~/.kagura/mcp.toml`:

```toml
[mcp]
# MCPサーバー設定
enabled = true
port = 3000
auto_discover = true

# エージェント検出パス
agent_paths = [
    "~/.kagura/agents",
    "~/projects/my_agents"
]

# MCPクライアント設定
[mcp.client]
enabled = true

# 外部MCPツール
[[mcp.client.tools]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]

[[mcp.client.tools]]
name = "brave_search"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-brave-search"]
env = { BRAVE_API_KEY = "${BRAVE_API_KEY}" }
```

## テスト戦略

### ユニットテスト

```python
# tests/mcp/test_server.py
import pytest
from kagura.mcp import KaguraMCPServer
from kagura import agent

@pytest.mark.asyncio
async def test_list_tools():
    server = KaguraMCPServer()

    @agent
    async def test_agent(x: int) -> int:
        """Test agent"""
        return x * 2

    tools = await server.list_tools()

    assert len(tools) > 0
    assert any(t.name == "kagura_test_agent" for t in tools)

@pytest.mark.asyncio
async def test_call_tool():
    server = KaguraMCPServer()

    result = await server.call_tool("kagura_test_agent", {"x": 5})

    assert len(result) == 1
    assert result[0].text == "10"
```

### 統合テスト

```python
# tests/mcp/test_integration.py
import pytest
from mcp import ClientSession
from kagura.mcp import KaguraMCPServer

@pytest.mark.asyncio
async def test_mcp_client_integration():
    """Test MCP client can call Kagura tools"""
    server = KaguraMCPServer()

    async with ClientSession(server) as client:
        tools = await client.list_tools()
        assert len(tools) > 0

        result = await client.call_tool("kagura_test_agent", {"x": 5})
        assert result is not None
```

## セキュリティ考慮事項

1. **アクセス制御**
   - エージェント実行の認証・認可
   - APIキーによるアクセス制限

2. **入力検証**
   - JSON Schemaによる厳格な入力検証
   - インジェクション攻撃対策

3. **リソース制限**
   - エージェント実行のタイムアウト
   - 同時実行数の制限

## マイグレーション

既存のKaguraユーザーへの影響なし。MCP機能はオプトイン：

```bash
# MCP機能のインストール
pip install kagura-ai[mcp]

# MCPサーバー起動
kagura mcp serve
```

## ドキュメント

### 必要なドキュメント
1. MCP Integration クイックスタートガイド
2. Claude Code連携ガイド
3. カスタムエージェントのMCP公開方法
4. 外部MCPツール利用ガイド
5. トラブルシューティングFAQ

### サンプルコード
- Claude Code内でのKagura利用例
- Kaguraから外部MCPツール利用例
- エージェント連携パターン

## 代替案

### 案1: 独自プロトコル
- Kagura専用のRPC実装
- **却下理由**: エコシステムに参加できない

### 案2: REST API
- HTTP/RESTでエージェント公開
- **却下理由**: MCP標準に劣る、双方向通信が困難

### 案3: gRPC
- 高速バイナリプロトコル
- **却下理由**: MCP標準ではない、複雑

## 未解決の問題

1. **MCP仕様の進化**
   - MCP仕様が変更された場合の対応
   - バージョニング戦略

2. **パフォーマンス**
   - 大量のエージェント公開時のオーバーヘッド
   - キャッシング戦略

3. **エラーハンドリング**
   - エージェント失敗時のMCPエラー表現
   - リトライ戦略

## 参考資料

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [Claude Code MCP Integration](https://docs.claude.com/)

## 改訂履歴

- 2025-10-04: 初版作成
