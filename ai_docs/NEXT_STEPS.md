# Kagura AI - Next Steps（次のアクション）

**最終更新**: 2025-10-10
**現在地**: ✅ **v2.2.0 リリース完了！** 🎉 → v2.3.0準備中 🚀

---

## 📍 現在の状況

### ✅ 完了済み（v2.1.0）

#### Core Features (v2.0.0-v2.0.2)
- **v2.0.2**: PyPI公開完了、安定版リリース
- **Core Engine**: @agent, Prompt Template, Type Parser（#14, #15, #16）
- **Code Executor**: AST検証、安全実行（#20, #21）
- **CLI & REPL**: Click CLI、prompt_toolkit REPL（#24, #25, #27, #56, #72）
- **テスト**: 統合テスト、カバレッジ80%+
- **ドキュメント**: README、チュートリアル、サンプル（#32, #33, #34, #45, #54）
- **RFC作成**: 全18個のRFC（002-018）作成完了、Issue作成済み
- **統合ロードマップ**: `UNIFIED_ROADMAP.md`作成完了

#### RFC-007: MCP Integration Phase 1 ✅
**PR #89, #90, #91** (2025-10-09)

- `src/kagura/core/registry.py`: Agent Registry（117行）
- `src/kagura/mcp/schema.py`: JSON Schema生成（146行）
- `src/kagura/mcp/server.py`: MCP Server（130行）
- `src/kagura/cli/mcp.py`: CLI commands（121行）
- `tests/mcp/`: 21テスト（100%パス）
- `docs/en/tutorials/06-mcp-integration.md`: チュートリアル（400行）
- `docs/en/api/mcp.md`: APIリファレンス（350行）

**成果**: Kaguraエージェントを**Claude Desktop**で即座に利用可能に！

#### RFC-017: Shell Integration ✅
**PR #92** (2025-10-09)

- `src/kagura/core/shell.py`: ShellExecutor（261行）
- `src/kagura/builtin/shell.py`: shell() 関数
- `src/kagura/builtin/git.py`: Git操作（commit, push, status, PR）
- `src/kagura/builtin/file.py`: File操作（search, grep）
- `tests/builtin/`: 26テスト（全パス）
- `docs/en/tutorials/07-shell-integration.md`: チュートリアル（216行）
- `docs/en/api/shell.md`: APIリファレンス（289行）

**成果**: セキュアなシェルコマンド実行、Git自動化、ファイル操作が可能に！

#### RFC-018: Memory Management Phase 1 & 2 ✅
**PR #94** (2025-10-09) - Phase 1: Core Memory Types
- `src/kagura/core/memory/working.py`: WorkingMemory（99行）
- `src/kagura/core/memory/context.py`: ContextMemory（166行）
- `src/kagura/core/memory/persistent.py`: PersistentMemory（249行）
- `src/kagura/core/memory/manager.py`: MemoryManager（263行）
- `@agent` デコレータにメモリ統合
- `tests/core/memory/`: 66テスト（100%カバレッジ）
- `docs/en/tutorials/08-memory-management.md`: チュートリアル（429行）
- `docs/en/api/memory.md`: APIリファレンス（479行）

**PR #105** (2025-10-10) - Phase 2: Memory RAG
- `src/kagura/core/memory/rag.py`: MemoryRAG（167行）
- ChromaDB統合でベクトル検索
- `store_semantic()` / `recall_semantic()` メソッド
- エージェントスコープのセマンティック検索
- `tests/core/test_memory_rag.py`: 9テスト（全パス）
- `pyproject.toml`: memory optional dependency追加

**成果**: Working/Context/Persistent の3層メモリ + RAG検索システムを実装！

#### RFC-012: Commands & Hooks Phase 1 & 2 ✅
**PR #95** (2025-10-09) - Phase 1-A: Command Loader
- `src/kagura/commands/command.py`: Command dataclass（66行）
- `src/kagura/commands/loader.py`: CommandLoader（104行）
- Markdownファイルから YAML frontmatter + template 読み込み
- `tests/commands/`: 23テスト（100%カバレッジ）
- `docs/en/api/commands.md`: APIリファレンス（421行）
- `docs/en/guides/commands-quickstart.md`: クイックスタート（418行）

**PR #96** (2025-10-09) - Phase 1-B: Inline Execution
- `src/kagura/commands/executor.py`: InlineCommandExecutor + CommandExecutor（157行）
- `src/kagura/cli/commands_cli.py`: `kagura run` CLI command（130行）
- インライン実行: ``!`command` `` 構文でシェルコマンド実行
- Jinja2テンプレートレンダリング
- `tests/commands/test_executor.py`: 19テスト（全パス）

**PR #97** (2025-10-09) - Phase 2: Hooks System
- `src/kagura/commands/hooks.py`: Hook実装（PreToolUse/PostToolUse）
- `src/kagura/commands/registry.py`: HookRegistry
- Validation Hooks
- `tests/commands/test_hooks.py`: Hooksテスト

**成果**: Markdownコマンド、インライン実行、Hooksシステムを実装！

#### RFC-016: Agent Routing System ✅
**PR #98** (2025-10-09) - Phase 1: Basic Routing
- `src/kagura/routing/router.py`: BaseRouter実装
- `src/kagura/routing/keyword.py`: KeywordRouter（キーワードベース）
- `src/kagura/routing/llm.py`: LLMRouter（LLMベース）
- Intent Detection & Agent Selection
- `tests/routing/`: ルーティングテスト

**PR #101** (2025-10-10) - Phase 2: Semantic Routing
- `src/kagura/routing/semantic.py`: SemanticRouter（semantic-router統合）
- ベクトルベースのルーティング
- `pyproject.toml`: routing optional dependency追加
- `tests/routing/test_semantic.py`: セマンティックルーティングテスト

**成果**: Keyword/LLM/Semanticの3種類のルーティング戦略を実装！

#### RFC-006: Chat REPL Phase 1 ✅
**PR #102** (2025-10-10)

- `src/kagura/cli/chat.py`: Chat REPL実装
- `src/kagura/chat/preset.py`: プリセットエージェント（Translate, Summarize, CodeReview）
- 対話型チャットREPL（`kagura chat`）
- セッション管理
- `tests/chat/`: Chat REPLテスト

**成果**: インタラクティブなチャットREPLを実装！

#### Core Decorators ✅
**PR #103** (2025-10-10) - @tool decorator
- `src/kagura/core/decorators.py`: @tool デコレータ実装
- `src/kagura/core/tool_registry.py`: ToolRegistry（117行）
- 型検証、シグネチャ管理
- `tests/core/test_tool_*.py`: テスト（11 registry + 12 decorator）
- `docs/en/tutorials/11-tools.md`: チュートリアル（580行）
- `docs/en/api/tools.md`: APIリファレンス（562行）

**PR #104** (2025-10-10) - @workflow decorator
- `src/kagura/core/decorators.py`: @workflow デコレータ実装
- `src/kagura/core/workflow_registry.py`: WorkflowRegistry（117行）
- マルチエージェントオーケストレーション
- `tests/core/test_workflow_*.py`: テスト（11 registry + 12 decorator）
- `docs/en/tutorials/12-workflows.md`: チュートリアル（580行）
- `docs/en/api/workflows.md`: APIリファレンス（562行）

**成果**: @agent, @tool, @workflow の3つのコアデコレータが完成！

---

### 📊 v2.1.0 完了機能まとめ

| RFC | 機能 | PR | Status |
|-----|------|----|--------|
| RFC-007 | MCP Integration Phase 1 | #89-91 | ✅ |
| RFC-017 | Shell Integration | #92 | ✅ |
| RFC-018 | Memory Management Phase 1 & 2 | #94, #105 | ✅ |
| RFC-012 | Commands & Hooks Phase 1 & 2 | #95-97 | ✅ |
| RFC-016 | Agent Routing Phase 1 & 2 | #98, #101 | ✅ |
| RFC-006 | Chat REPL Phase 1 | #102 | ✅ |
| Core | @tool decorator | #103 | ✅ |
| Core | @workflow decorator | #104 | ✅ |

**合計**: 13個のPR、8個のRFC（Phase含む）完了 🎉

---

## 🎉 v2.2.0 リリース完了！（2025-10-10）

### ✅ 完了済み機能まとめ

| RFC | 機能 | PR | Status |
|-----|------|----|--------|
| RFC-018 | Memory RAG (Phase 2) | #105 | ✅ |
| RFC-019 | Unified Agent Builder | #111-113 | ✅ |
| RFC-022 | Agent Testing Framework | #114 | ✅ |
| RFC-001 | Workflow System - Advanced | #115 | ✅ |
| RFC-020 | Memory-Aware Routing | #116 | ✅ |
| RFC-021 | Agent Observability Dashboard | #117-118 | ✅ |

**合計**: 18個のPR、13個のRFC完了（Phase含む）🎉
**新規テスト**: 246個（全パス、100%カバレッジ）
**総テスト数**: 586+

---

### 📊 v2.2.0 主要機能

#### 1. RFC-018: Memory RAG (Phase 2) ✅
**PR #105**
- ChromaDB統合でベクトル検索
- セマンティックメモリの保存・検索
- エージェントスコープの分離
- 9テスト追加

#### 2. RFC-019: Unified Agent Builder ✅
**PR #111-113**
- Fluent API pattern (method chaining)
- 3つのプリセット（Chatbot, Research, CodeReview）
- Memory/Tools/Hooks統合
- 31テスト追加

#### 3. RFC-022: Agent Testing Framework ✅
**PR #114**
- LLM非決定性対応のアサーション
- モッキング機能（LLMRecorder, LLMMock）
- pytest統合（マーカー、フィクスチャ）
- 34テスト追加

#### 4. RFC-001: Workflow System - Advanced ✅
**PR #115**
- `@workflow.chain` - シーケンシャル実行
- `@workflow.parallel` - 並列実行
- `@workflow.stateful` - Pydanticベースのステートグラフ
- 17テスト追加

#### 5. RFC-020: Memory-Aware Routing ✅
**PR #116**
- ContextAnalyzer（文脈依存検出）
- MemoryAwareRouter（会話履歴考慮）
- 48テスト追加

#### 6. RFC-021: Agent Observability Dashboard ✅
**PR #117-118**
- EventStore + TelemetryCollector
- Rich TUI Dashboard
- `kagura monitor` CLI（live/list/stats/trace/cost）
- 107テスト追加

---

### 🎯 v2.2.0 統計

- **6つのRFC完了**: RFC-001, 018, 019, 020, 021, 022
- **18 PRマージ**: #105, #111-118
- **246 新規テスト**: 全パス（100%カバレッジ）
- **総テスト数**: 586+
- **リリース日**: 2025-10-10
- **GitHub Release**: [v2.2.0](https://github.com/JFK/kagura-ai/releases/tag/v2.2.0)

---

## 🤔 v2.1.0からの気づきと改善点

### 発見された課題

#### 1. **統合性・相互運用性の不足**
現在、各機能（Memory、Routing、Tools、Hooks）が個別に実装されており、統合が煩雑：
```python
# 現状：個別設定が必要
memory = MemoryManager(enable_rag=True)
router = SemanticRouter()
# エージェントとの統合が手動
```

#### 2. **Optional Dependenciesの管理**
4つのoptional groups（memory, routing, mcp, docs）があり、ユーザーが混乱：
```bash
pip install kagura-ai[memory]  # これだけでいい？
pip install kagura-ai[routing] # これも必要？
```

#### 3. **Integration Testsの未実行**
`@pytest.mark.integration`でマークされているが、CIで実行されていない

#### 4. **テスト戦略の不足**
エージェントの振る舞いをテストする標準的な方法がない

#### 5. **可観測性の欠如**
エージェントが何をしているか見えない（デバッグ困難、パフォーマンス不明、コスト不明）

---

## 💡 新規RFC提案（v2.2.0候補）

### 🆕 RFC-019: Unified Agent Builder
**優先度**: High
**見積もり**: 2週間
**Issue**: #107

**概要**: 複数機能を簡単に組み合わせられる統合ビルダーAPI

```python
from kagura import AgentBuilder

agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .with_memory(type="rag", persist=True)
    .with_routing(strategy="semantic", routes={...})
    .with_tools([search_tool, calc_tool])
    .with_hooks(pre=validation_hook)
    .build()
)
```

**解決する課題**:
- 複数機能統合の簡易化
- プリセット提供（Chatbot, Research, CodeReview）
- 一貫性のあるAPI

**実装計画**:
- Phase 1: Core Builder (1週間)
- Phase 2: Presets & Advanced Features (1週間)

---

### 🆕 RFC-020: Memory-Aware Routing
**優先度**: Medium
**見積もり**: 1.5週間
**Issue**: #108

**概要**: 過去の会話履歴を考慮したルーティング

```python
# 会話継続を理解
User: "Translate 'Hello' to Japanese"
→ translation_agent

User: "What about French?"
→ 会話履歴から「translation」と認識 → translation_agent
```

**解決する課題**:
- 代名詞・省略表現の理解
- コンテキストの継続性
- より自然な会話フロー

**実装計画**:
- Phase 1: Core Implementation (1週間)
- Phase 2: Advanced NLP (3日)

---

### 🆕 RFC-021: Agent Observability Dashboard
**優先度**: Medium-High
**見積もり**: 2週間
**Issue**: #109

**概要**: エージェント動作のリアルタイム可視化・監視

```bash
kagura monitor --agent my_agent

[my_agent] Execution Timeline:
├─ LLM Call (gpt-4o) .......... 2.3s  [$0.0023]
├─ Tool: search_tool .......... 1.5s
├─ LLM Call (gpt-4o) .......... 2.1s  [$0.0021]
└─ Total ...................... 5.9s  [$0.0044]

⚠️ LLM calls taking 75% of time
💡 Consider caching or using faster model
```

**解決する課題**:
- パフォーマンスボトルネックの特定
- コスト管理
- デバッグの簡易化

**実装計画**:
- Phase 1: Telemetry Collection (1週間)
- Phase 2: CLI Dashboard (1週間)
- Phase 3: Web UI (optional, v2.3.0)

---

### 🆕 RFC-022: Agent Testing Framework
**優先度**: High
**見積もり**: 2週間
**Issue**: #110

**概要**: AIエージェント専用のテストフレームワーク

```python
from kagura.testing import AgentTestCase

class TestTranslator(AgentTestCase):
    agent = translator

    async def test_japanese_translation(self):
        result = await self.agent("Hello", "ja")

        # Flexible assertions for LLM outputs
        self.assert_contains_any(result, ["こんにちは", "ハロー", "やあ"])
        self.assert_language(result, "ja")
        self.assert_no_english(result)
```

**解決する課題**:
- LLMの非決定性への対応
- 振る舞い駆動テスト (BDD)
- 回帰テストの自動化

**実装計画**:
- Phase 1: Core Framework (1週間)
- Phase 2: Advanced Assertions & Mocking (1週間)

---

## 📝 v2.2.0 優先順位（改訂版）

### 🥇 Tier 1: 統合性とユーザビリティ（必須）
**期間**: 2-3週間

1. **RFC-019: Unified Agent Builder** (High, 2週間)
   - 複数機能の統合を簡単に
   - プリセット提供
   - 学習曲線の改善

2. **RFC-022: Agent Testing Framework** (High, 2週間)
   - 品質保証の標準化
   - TDDの推進
   - エンタープライズ対応

**並行実装可能** → 合計2週間で完了可能

---

### 🥈 Tier 2: 可観測性と品質（重要）
**期間**: 2-3週間

3. **RFC-021: Agent Observability Dashboard** (Medium-High, 2週間)
   - パフォーマンス最適化
   - コスト管理
   - デバッグ支援

4. **RFC-020: Memory-Aware Routing** (Medium, 1.5週間)
   - より自然な会話
   - RFC-016とRFC-018の統合

**並行実装可能** → 合計2週間で完了可能

---

### 🥉 Tier 3: 既存RFC実装（拡張）
**期間**: 2-4週間

5. **RFC-007 Phase 2: MCP Memory Protocol** (Medium, 1週間)
   - Claude Codeとの記憶共有
   - Phase 1完了済みで継続性高い

6. **RFC-014: Web Integration** (Medium, 1.5週間)
   - 実用性が高い
   - Web Scraping, API統合

---

### 改善タスク（小規模、随時対応）

- **Integration Tests CI** (1日)
  - GitHub Actions workflowで`pytest -m integration`実行

- **Preset Dependencies** (半日)
  ```toml
  [project.optional-dependencies]
  full = ["chromadb>=0.4.0", "semantic-router>=0.1.11", "mcp>=1.0.0"]
  ai = ["chromadb>=0.4.0", "semantic-router>=0.1.11"]
  ```

- **examples/ Update** (2-3日)
  - v2.1.0新機能のサンプル追加
  - Memory RAG + Routingの組み合わせ例

---

## 🚀 v2.2.0 推奨実装プラン

### プラン A: 統合性重視（推奨）
**期間**: 4週間
**内容**:
1. Week 1-2: RFC-019 (Unified Builder) + RFC-022 (Testing) 並行
2. Week 3-4: RFC-021 (Observability) + RFC-020 (Memory-Aware Routing) 並行

**利点**: ユーザビリティと品質が大幅向上、v2.3.0以降の基盤

---

### プラン B: 機能拡張重視
**期間**: 4週間
**内容**:
1. Week 1-2: RFC-019 (Unified Builder)
2. Week 3: RFC-007 Phase 2 (MCP Memory)
3. Week 4: RFC-014 (Web Integration)

**利点**: 新機能追加、エコシステム拡大

---

### プラン C: ドキュメント優先
**期間**: 1週間 + 2-3週間
**内容**:
1. Week 1: ドキュメント整理・チュートリアル追加
2. Week 2-4: プランAまたはB実行

**利点**: v2.1.0の完全なドキュメント化 → 新機能実装

---

## 🌐 中長期ロードマップ（v2.3.0以降）

### v2.3.0: Web & Multimodal (2-3ヶ月後)
- RFC-002: Multimodal RAG
- RFC-014: Web Integration (未完の場合)
- RFC-013: OAuth2 Auth

### v2.4.0: Meta Agent & Ecosystem (4-5ヶ月後)
- RFC-005: Meta Agent
- RFC-008: Plugin Marketplace
- RFC-009: Multi-Agent Orchestration

### v2.5.0+: Advanced Features (6ヶ月以降)
- RFC-003: Personal Assistant
- RFC-004: Voice Interface
- RFC-010: Observability (未完の場合)
- RFC-011: Scheduled Automation

**詳細**: `ai_docs/UNIFIED_ROADMAP.md` 参照

---

## 🔧 技術的な準備事項

### 開発環境
```bash
# Python 3.11+
python --version

# 依存関係インストール
uv sync

# オプショナル依存関係
uv sync --extra memory  # Memory RAG (ChromaDB)
uv sync --extra routing # Semantic Routing
uv sync --extra mcp     # MCP Integration

# 全てインストール（開発用）
uv sync --all-extras

# テスト実行
pytest

# Integration testsも含める
pytest -m integration

# 型チェック
pyright src/kagura/

# リンター
ruff check src/
```

### CI/CD
- GitHub Actions設定済み
- PyPI自動デプロイ設定済み
- Codecov統合済み
- **TODO**: Integration tests CI追加

---

## 📊 進捗管理

### GitHub Projects
- Milestoneで管理: v2.0.0, v2.1.0, v2.2.0...
- Issueラベル: `enhancement`, `rfc`, `bug`, `documentation`

### 週次レビュー
- 毎週金曜: 進捗確認
- 月次: ロードマップ見直し

---

## ❓ よくある質問

### Q1: どのRFCが完了している？
A: 以下のRFCが完了しています（2025-10-10 21:00現在）：
- ✅ RFC-007 Phase 1: MCP Integration（Claude Desktop統合）
- ✅ RFC-017: Shell Integration（シェル実行、Git自動化）
- ✅ RFC-018 Phase 1 & 2: Memory Management（3層メモリ + RAG検索）
- ✅ RFC-012 Phase 1 & 2: Commands & Hooks（コマンド + Hooks）
- ✅ RFC-016 Phase 1 & 2: Agent Routing（3種類のルーティング）
- ✅ RFC-006 Phase 1: Chat REPL（対話型チャット）
- ✅ **RFC-019: Unified Agent Builder**（統合ビルダー + Presets）⭐️ NEW

### Q2: 新規RFC（019-022）はどこで確認できる？
A: `ai_docs/rfcs/` ディレクトリ：
- RFC-019: Unified Agent Builder
- RFC-020: Memory-Aware Routing
- RFC-021: Agent Observability Dashboard
- RFC-022: Agent Testing Framework

各RFCには詳細な設計、API例、実装計画が含まれています。

### Q3: v2.2.0で何を実装すべき？
A: **プランA（推奨）**:
1. RFC-019: Unified Agent Builder（統合性）
2. RFC-022: Agent Testing Framework（品質保証）
3. RFC-021: Agent Observability Dashboard（可観測性）
4. RFC-020: Memory-Aware Routing（高度化）

これらは相互に依存しないため、並行実装可能。

### Q4: v2.1.0でどの機能が使える？
A:
- ✅ `@agent` デコレータ
- ✅ `@tool` デコレータ ⭐️ NEW
- ✅ `@workflow` デコレータ ⭐️ NEW
- ✅ Jinja2プロンプトテンプレート
- ✅ 型ベースパース（Pydantic対応）
- ✅ 安全なコード実行（CodeExecutor）
- ✅ CLI & REPL
- ✅ **MCP Integration** (Claude Desktop対応)
- ✅ **Shell Integration** (シェル実行、Git自動化)
- ✅ **Memory Management** (Working/Context/Persistent/RAG) ⭐️ NEW
- ✅ **Custom Commands** (Markdown定義、インライン実行、Hooks) ⭐️ NEW
- ✅ **Agent Routing** (Keyword/LLM/Semantic) ⭐️ NEW
- ✅ **Chat REPL** (対話型チャット、プリセット) ⭐️ NEW

### Q5: なぜUnified Agent Builderが重要？
A: v2.1.0で多数の機能（Memory、Routing、Tools、Hooks）が追加されましたが、統合が手動で煩雑です。Builderパターンにより：
- 初心者でも簡単に複数機能を組み合わせられる
- プリセットで一般的な構成をすぐ使える
- 一貫性のあるAPI
- 学習曲線が改善される

---

## 🎬 次のステップ（v2.3.0に向けて）

### ✅ v2.2.0 完了タスク
1. ✅ 新規RFC作成（019-022）
2. ✅ 各RFCのGitHub Issue作成（#107-110）
3. ✅ RFC-019: Unified Agent Builder完了（PR #111-113）
4. ✅ RFC-022: Agent Testing Framework完了（PR #114）
5. ✅ RFC-001: Advanced Workflows完了（PR #115）
6. ✅ RFC-020: Memory-Aware Routing完了（PR #116）
7. ✅ RFC-021: Observability Dashboard完了（PR #117-118）
8. ✅ v2.2.0リリース（2025-10-10）

---

## 🚀 v2.3.0 候補機能

### 🥇 優先度: High

#### RFC-002: Multimodal RAG
**期間**: 3週間
**Issue**: [#62](https://github.com/JFK/kagura-ai/issues/62)

**概要**: 画像・音声・動画・PDFの処理とRAG統合

**実装内容**:
- 画像処理（Gemini Vision API統合）
- 音声・動画処理（Whisper統合）
- PDF処理（PyPDF2統合）
- マルチモーダルベクトル検索

**使用例**:
```python
@agent(enable_multimodal=True)
async def visual_agent(image_path: str) -> str:
    """Analyze image: {{ image_path }}"""
    pass

result = await visual_agent("diagram.png")
```

---

#### RFC-014: Web Integration
**期間**: 2週間
**Issue**: [#75](https://github.com/JFK/kagura-ai/issues/75)

**概要**: Web検索・スクレイピング機能

**実装内容**:
- Brave Search API統合（無料枠2000クエリ/月）
- DuckDuckGo フォールバック
- BeautifulSoup スクレイピング
- robots.txt 遵守

**使用例**:
```python
@agent
@web.enable
async def research_agent(topic: str) -> str:
    """Research {{ topic }} using web search"""
    pass
```

---

### 🥈 優先度: Medium

#### RFC-007 Phase 2: MCP Memory Protocol
**期間**: 1週間
**Issue**: [#67](https://github.com/JFK/kagura-ai/issues/67)

**概要**: Claude DesktopとKaguraエージェント間でメモリ共有

**実装内容**:
- MCP Memory Protocol実装
- 双方向メモリ同期
- セッション復元

---

#### RFC-013: OAuth2 Authentication
**期間**: 1.5週間
**Issue**: [#74](https://github.com/JFK/kagura-ai/issues/74)

**概要**: Google OAuth2認証でAPIキー不要に

**実装内容**:
- Google OAuth2フロー
- トークン管理（Fernet暗号化）
- 自動リフレッシュ

---

### 📅 v2.3.0 推奨プラン

**プラン A: マルチモーダル重視（推奨）**
- Week 1-3: RFC-002 (Multimodal RAG)
- Week 4-5: RFC-014 (Web Integration)
- **期間**: 5週間
- **利点**: 実用性が大幅向上

**プラン B: エコシステム拡張**
- Week 1-2: RFC-014 (Web Integration)
- Week 3: RFC-007 Phase 2 (MCP Memory)
- Week 4-5: RFC-013 (OAuth2)
- **期間**: 5週間
- **利点**: Claude Desktop統合強化、認証改善

---

## 🔧 改善タスク（v2.2.0リリース後）

### 完了済み ✅
- [x] v2.2.0リリース（2025-10-10）
- [x] CHANGELOG.md更新
- [x] GitHub Release作成

### 進行中 🚧
- [ ] ai_docs/NEXT_STEPS.md更新（このファイル）
- [ ] ai_docs/UNIFIED_ROADMAP.md更新
- [ ] コードコメント追加（複雑な関数）
- [ ] リファクタリング候補の洗い出し

### 今後の計画 📋
- [ ] ユーザードキュメント追加検討（docs/）
- [ ] examples/ 更新（v2.2.0新機能）
- [ ] Integration tests CI追加

---

## 📚 参考リンク

- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - v2.0.0詳細
- [coding_standards.md](./coding_standards.md) - コーディング規約
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - 全Issue一覧
- [RFC Documents](./rfcs/RFC_*.md) - 各RFC詳細仕様
  - [RFC-019](./rfcs/RFC_019_UNIFIED_AGENT_BUILDER.md) - Unified Agent Builder
  - [RFC-020](./rfcs/RFC_020_MEMORY_AWARE_ROUTING.md) - Memory-Aware Routing
  - [RFC-021](./rfcs/RFC_021_AGENT_OBSERVABILITY_DASHBOARD.md) - Observability Dashboard
  - [RFC-022](./rfcs/RFC_022_AGENT_TESTING_FRAMEWORK.md) - Testing Framework

---

**v2.1.0完了おめでとうございます！次はv2.2.0で統合性と品質の向上を目指しましょう 🚀**
