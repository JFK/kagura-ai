# Kagura AI 戦略的開発計画

## エグゼクティブサマリー

Kagura AIを**Claude Code風のAIエージェントライクな作り**に進化させ、開発者フレンドリーな次世代AIエージェントフレームワークへと変革する。YAML設定の煩雑さを解消し、Pythonコードファーストのアプローチを提供しつつ、後方互換性を維持する。

**目標**: 開発者が数行のPythonコードでエージェントを定義・実行でき、Claude Codeのようにコード自体がエージェントとして振る舞うフレームワーク

---

## 現状分析

### 🎯 既存Issue分析

| Issue | 重要度 | 影響範囲 | 現状の問題点 |
|-------|--------|----------|------------|
| #1: `kagura install` | High | インストール | GitHubからのエージェント配布が手動 |
| #5: Agent API Server | High | 統合 | REST API化されておらず外部連携が困難 |
| #6: MCP Server | High | 統合 | Claude Desktop等との連携不可 |
| #7: Qdrant RAG | Medium | 機能拡張 | RAG機能が未実装 |
| #8: Python State Models | **Critical** | DX | YAML設定が煩雑で開発者体験が悪い |

### 💡 現状の強み

1. **LangGraph/LangChain統合**: 強力なワークフローオーケストレーション
2. **LiteLLM統合**: 複数LLMプロバイダー対応
3. **型安全性**: Pydantic v2ベースの堅牢な設計
4. **3種類のエージェント**: Atomic/Tool/Workflow の明確な分離

### ⚠️ 現状の課題

1. **YAML地獄**: エージェント定義に多数のYAMLファイルが必要
   ```yaml
   # agent.yml, state_model.yml, system.yml...
   # 開発者は最低3ファイル編集が必要
   ```

2. **コードとYAMLの分離**: ロジックがtools.pyと設定が分散
   ```python
   # tools.py にロジック
   # agent.yml にプロンプト
   # state_model.yml に型定義
   # → 一元管理できず、認知負荷が高い
   ```

3. **学習曲線が急峻**:
   - エージェント作成までのステップ数: **5-10ステップ**
   - ドキュメント参照回数: **平均3-5回**

4. **Claude Codeとの対比**:
   ```python
   # Claude Codeの場合
   result = claude_code.run("タスク実行")

   # Kagura AIの場合
   # 1. YAMLファイル作成
   # 2. state_model.yml作成
   # 3. tools.py作成
   # 4. Pythonコードで実行
   agent = Agent.assigner("agent_name", state)
   result = await agent.execute()
   ```

---

## 戦略的ビジョン: "Claude Code-like Kagura"

### コンセプト

**"エージェント定義 = Pythonコード"**

開発者が1つのPythonファイルでエージェントを定義し、そのコードがそのままエージェントとして実行される。

### 目指す開発者体験

#### Before (現状)
```python
# 1. state_model.yml
"""
state_fields:
  - name: summary
    type: str
"""

# 2. agent.yml
"""
description: Summarizer
prompt:
  - template: "Summarize: {content}"
"""

# 3. main.py
from kagura.core.agent import Agent

agent = Agent.assigner("summarizer", {"content": {"text": text}})
result = await agent.execute()
```

#### After (目標)
```python
from kagura import Agent, task

@task("Summarize the following content")
class SummarizerAgent(Agent):
    content: str
    summary: str = None

    async def execute(self):
        # LLMが自動で呼ばれる
        return await self.run()

# 1行で実行
result = await SummarizerAgent(content=text).execute()
print(result.summary)
```

または、さらにシンプルに:

```python
from kagura import agent

@agent
async def summarize(content: str) -> str:
    """Summarize the following content"""
    # この関数自体がエージェントになる
    # docstringがプロンプトになる
    pass

# 直接呼び出し
summary = await summarize(text)
```

---

## 開発ロードマップ

### Phase 1: Python-First Foundation (4-6週間)

**優先度: Critical**

#### 1.1 Python State Models (#8)

**目標**: YAMLからの脱却第一歩

```python
# state_model.py (新方式)
from pydantic import BaseModel, Field

class SummarizerState(BaseModel):
    content: str = Field(description="Content to summarize")
    summary: str | None = Field(default=None, description="Generated summary")
```

**実装タスク**:
- [ ] `state_model.py`のローディング機構
- [ ] YAML ↔ Python 変換ツール
- [ ] 後方互換性の保証
- [ ] ドキュメント・マイグレーションガイド

#### 1.2 Decorator-Based Agent Definition

**目標**: Pythonデコレータでエージェント定義

```python
from kagura import atomic_agent, workflow_agent

@atomic_agent(
    description="Text summarizer",
    model="gpt-4",
    temperature=0.7
)
class Summarizer:
    content: str
    summary: str = None

    def prompt(self) -> str:
        return f"Summarize: {self.content}"
```

**実装タスク**:
- [ ] `@atomic_agent` デコレータ
- [ ] `@tool_agent` デコレータ
- [ ] `@workflow_agent` デコレータ
- [ ] プロンプトテンプレートのインライン化
- [ ] LLM設定のデコレータ引数化

#### 1.3 Fluent API

**目標**: メソッドチェーンによる直感的な記述

```python
from kagura import Agent

agent = (
    Agent()
    .with_model("gpt-4")
    .with_state(SummarizerState)
    .with_prompt("Summarize: {content}")
    .with_temperature(0.7)
)

result = await agent.run(content=text)
```

**実装タスク**:
- [ ] Builder パターン実装
- [ ] メソッドチェーンAPI設計
- [ ] 型推論の最適化

---

### Phase 2: Developer Experience Enhancement (6-8週間)

**優先度: High**

#### 2.1 CLI Improvements

**現状の問題**: CLIが基本的すぎる

**目標**: 開発者フレンドリーなCLI

```bash
# エージェント作成
kagura create agent summarizer --type atomic --template python

# 生成されたファイル
agents/summarizer/
  ├── agent.py          # Pythonベース定義
  ├── __init__.py
  └── tests/

# インタラクティブ実行
kagura run summarizer --interactive

# デバッグモード
kagura debug summarizer --step-by-step
```

**実装タスク**:
- [ ] `kagura create` コマンド拡張
- [ ] Pythonテンプレート生成
- [ ] インタラクティブモード
- [ ] デバッグモード
- [ ] ホットリロード機能

#### 2.2 Agent Package Manager (#1)

**目標**: `pip install`のようにエージェントをインストール

```bash
# GitHubからインストール
kagura install github:username/awesome-summarizer

# レジストリからインストール (将来)
kagura install summarizer

# ローカル開発
kagura link ./my-agent

# アップデート
kagura update summarizer
```

**実装タスク**:
- [ ] GitHub連携
- [ ] バージョン管理
- [ ] 依存関係解決
- [ ] プラグインシステム
- [ ] レジストリ構想(将来)

#### 2.3 IDE Integration

**目標**: VSCode拡張などでの開発支援

```json
// .vscode/settings.json
{
  "kagura.autoComplete": true,
  "kagura.linting": true,
  "kagura.agentPreview": true
}
```

**実装タスク**:
- [ ] VSCode拡張の調査
- [ ] 型定義の充実
- [ ] Language Server Protocol検討
- [ ] スニペット提供

---

### Phase 3: Claude Code-like Intelligence (8-12週間)

**優先度: High**

#### 3.1 Agent API Server (#5)

**目標**: エージェントをREST APIとして公開

```python
# server.py
from kagura import serve

@serve(port=8000)
class SummarizerAPI:
    agent = Summarizer

    # 自動的にFastAPIエンドポイント生成
    # POST /execute
    # GET /status/{execution_id}
    # GET /schema
```

```bash
# CLI起動
kagura serve summarizer --port 8000

# Docker対応
kagura serve summarizer --docker --build
```

**実装タスク**:
- [ ] FastAPI統合
- [ ] 自動エンドポイント生成
- [ ] OpenAPI仕様生成
- [ ] WebSocket対応(ワークフロー用)
- [ ] 認証・認可機構
- [ ] レートリミット

#### 3.2 MCP Server Support (#6)

**目標**: Claude Desktop等との連携

```python
# mcp_server.py
from kagura import mcp_server

@mcp_server
class KaguraMCP:
    agents = [
        Summarizer,
        SearchPlanner,
        ContentFetcher,
    ]
    # 自動的にMCPツールとして公開
```

```bash
# MCP起動
kagura mcp --transport stdio

# Claude Desktop設定
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "--transport", "stdio"]
    }
  }
}
```

**実装タスク**:
- [ ] MCP protocol実装
- [ ] stdio/SSE transport
- [ ] エージェント→ツール変換
- [ ] Claude Desktop連携テスト
- [ ] ドキュメント整備

#### 3.3 自己改善エージェント

**目標**: エージェント自身が学習・改善

```python
@atomic_agent(self_improving=True)
class SmartSummarizer:
    content: str
    summary: str = None

    async def post_process(self, result):
        # フィードバックを元に自己改善
        await self.learn_from_feedback(result)
```

**実装タスク**:
- [ ] フィードバックループ機構
- [ ] プロンプト最適化
- [ ] Few-shot学習機能
- [ ] パフォーマンストラッキング

---

### Phase 4: Advanced Features (12-16週間)

**優先度: Medium**

#### 4.1 RAG Integration (#7)

**目標**: Qdrant統合でRAG対応

```python
from kagura import rag_agent

@rag_agent(
    vector_db="qdrant",
    collection="knowledge_base"
)
class KnowledgeAgent:
    query: str
    answer: str = None
    sources: list = []

    # 自動的にRAG処理
```

**実装タスク**:
- [ ] Qdrant統合
- [ ] ベクトル埋め込み自動化
- [ ] ハイブリッド検索
- [ ] リランキング
- [ ] チャンキング戦略

#### 4.2 Multi-Agent Orchestration

**目標**: 複数エージェントの協調

```python
from kagura import workflow

@workflow
class ResearchWorkflow:
    async def execute(self, topic: str):
        # 並列実行
        results = await asyncio.gather(
            self.search(topic),
            self.summarize(topic),
            self.analyze(topic)
        )

        # 結果を統合
        return await self.synthesize(results)
```

**実装タスク**:
- [ ] 並列実行サポート
- [ ] 依存関係グラフ
- [ ] 条件分岐最適化
- [ ] エラーハンドリング強化

#### 4.3 Monitoring & Observability

**目標**: プロダクション運用対応

```python
from kagura import monitor

@monitor(
    metrics=["latency", "tokens", "cost"],
    tracing=True,
    logging=True
)
class ProductionAgent:
    pass
```

**実装タスク**:
- [ ] OpenTelemetry統合
- [ ] メトリクス収集
- [ ] トレーシング
- [ ] ダッシュボード
- [ ] アラート機能

---

## 技術的アーキテクチャ変更

### 新しいディレクトリ構造

```
src/kagura/
├── __init__.py              # 主要APIをエクスポート
├── core/
│   ├── agent.py            # 新Agent基底クラス
│   ├── decorators.py       # @atomic_agent等
│   ├── builder.py          # Fluent API
│   ├── config.py           # 設定管理(拡張)
│   ├── models.py           # Pydanticモデル
│   └── state.py            # 状態管理(新)
├── api/
│   ├── server.py           # FastAPI統合
│   ├── mcp_server.py       # MCP Server
│   └── client.py           # APIクライアント
├── cli/
│   ├── create.py           # エージェント作成
│   ├── serve.py            # サーバー起動
│   ├── install.py          # パッケージ管理
│   └── debug.py            # デバッグモード
├── integrations/
│   ├── qdrant.py           # Qdrant統合
│   ├── redis.py            # Redis統合
│   └── monitoring.py       # 監視ツール
└── templates/              # エージェントテンプレート
    ├── atomic/
    ├── tool/
    └── workflow/
```

### 後方互換性戦略

```python
# 旧方式(YAML) - 引き続きサポート
agent = Agent.assigner("summarizer", state)

# 新方式(Python) - 優先推奨
agent = Summarizer(content=text)

# 段階的移行
# 1. state_model.yml → state_model.py
# 2. agent.yml の一部を Python化
# 3. 完全Python化
```

---

## 実装優先順位

### 🔴 Critical (即座に着手)

1. **#8: Python State Models** (2週間)
   - 最大のDX改善ポイント
   - 他の改善の基礎

2. **Decorator API設計** (2週間)
   - コアAPI確定
   - プロトタイプ実装

### 🟡 High (1-2ヶ月以内)

3. **#1: kagura install** (2週間)
   - エコシステム拡大に必須

4. **#5: API Server** (3週間)
   - 外部統合の基盤

5. **#6: MCP Server** (2週間)
   - Claude Desktop連携

### 🟢 Medium (2-3ヶ月以内)

6. **#7: RAG Integration** (3週間)
   - 機能強化

7. **CLI Enhancement** (2週間)
   - DX改善

---

## マイルストーン

### M1: Python-First (Week 1-6)
- [ ] Python State Models実装
- [ ] Decorator API設計・実装
- [ ] 基本的なテスト・ドキュメント

### M2: Developer Tools (Week 7-14)
- [ ] CLI改善
- [ ] `kagura install`実装
- [ ] IDE統合調査

### M3: Integration (Week 15-26)
- [ ] API Server
- [ ] MCP Server
- [ ] RAG統合

### M4: Production Ready (Week 27-40)
- [ ] 監視・ロギング
- [ ] パフォーマンス最適化
- [ ] セキュリティ監査

---

## 成功指標(KPI)

### 開発者体験
- **エージェント作成時間**: 30分 → 5分
- **必要ファイル数**: 3-5ファイル → 1ファイル
- **ドキュメント参照回数**: 3-5回 → 0-1回

### 採用率
- **月間ダウンロード**: 現在 → 10x成長
- **GitHub Stars**: 現在 → 3x成長
- **コミュニティエージェント数**: 0 → 50+

### 技術的品質
- **テストカバレッジ**: 80% → 90%
- **型安全性**: 70% → 95%
- **ドキュメント充実度**: 60% → 90%

---

## リスクと対策

### リスク1: 後方互換性の崩壊

**対策**:
- デュアルモード運用(YAML/Python両対応)
- 段階的非推奨化(v1.0で警告、v2.0で削除)
- 自動マイグレーションツール

### リスク2: 複雑性の増大

**対策**:
- シンプルなデフォルト、強力なオプション
- 段階的学習曲線
- 豊富なサンプルコード

### リスク3: パフォーマンス劣化

**対策**:
- ベンチマーク継続実施
- プロファイリング
- 最適化の優先実施

---

## 次のアクション

### 即座に実施
1. **Issue #8対応**: Python State Models実装開始
2. **プロトタイプ作成**: Decorator APIのPoC
3. **チーム合意**: アーキテクチャレビュー

### 1週間以内
4. **詳細設計**: Phase 1の詳細仕様
5. **テストケース**: 新APIのテスト設計
6. **ドキュメント**: マイグレーションガイド草案

---

## まとめ

Kagura AIを**"YAML地獄から解放されたPython-First AIエージェントフレームワーク"**に進化させる。Claude Codeのような直感的なDXを提供しつつ、マルチエージェントオーケストレーションの強みを活かす。

**キャッチフレーズ案**:
> "Define Once, Run Anywhere - Python-First AI Agent Framework"

**目指す姿**:
```python
from kagura import agent

@agent
async def solve(problem: str) -> str:
    """Solve the given problem intelligently"""
    pass

# Just this simple.
answer = await solve("何でもできるAIエージェント")
```

これが、Kagura AIの未来です。
