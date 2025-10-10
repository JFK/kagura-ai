# Kagura AI - Next Steps（次のアクション）

**最終更新**: 2025-10-10 (17:30)
**現在地**: v2.1.0 リリース済み 🎉

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
|-----|------|----|----|
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

## 📝 次の優先タスク

### Option A: ドキュメント整理（推奨）
**見積もり**: 1-2時間
**優先度**: High

**実装内容**:
- [ ] ユーザーガイド作成（Chat REPL, Routing, Memory RAG）
- [ ] README.md更新（新機能追加）
- [ ] チュートリアルの整理

---

### Option B: RFC-007 MCP Phase 2 - Memory Protocol
**Issue #67**
**見積もり**: 1週間
**優先度**: Medium

**実装内容**:
- [ ] MCP Memory Protocol実装
- [ ] Claude Codeとの記憶共有
- [ ] Multi-agent memory sharing
- [ ] テスト・ドキュメント

---

### Option C: RFC-002 - Multimodal RAG
**Issue #62**
**見積もり**: 2週間
**優先度**: Medium

**実装内容**:
- [ ] 画像処理（vision models統合）
- [ ] PDFパース
- [ ] Audio/Videoサポート
- [ ] テスト・ドキュメント

---

### Option D: RFC-014 - Web Integration
**Issue #75**
**見積もり**: 1.5週間
**優先度**: Medium

**実装内容**:
- [ ] Web Scraping（BeautifulSoup/Playwright）
- [ ] API Integration（REST/GraphQL）
- [ ] WebSocket support
- [ ] テスト・ドキュメント

---

### Option E: RFC-003 - Personal Assistant
**Issue #63**
**見積もり**: 2週間
**優先度**: Medium

**実装内容**:
- [ ] タスク管理（TODO, Calendar）
- [ ] メール統合
- [ ] ファイル管理
- [ ] テスト・ドキュメント

---

## 🚀 中期目標（v2.2.0〜v2.3.0）

### v2.2.0 候補機能
- RFC-002: Multimodal RAG
- RFC-014: Web Integration
- RFC-003: Personal Assistant
- RFC-007 Phase 2: MCP Memory Protocol

### v2.3.0: Authentication & Security
- RFC-013: OAuth2 Auth (#74)

---

## 🌐 長期目標（v2.4.0以降）

### v2.4.0: Meta Agent & Ecosystem
- RFC-005: Meta Agent (#65)
- RFC-008: Plugin Marketplace (#68)
- RFC-009: Multi-Agent Orchestration (#69)

### v2.5.0+: Advanced Features
- RFC-004: Voice Interface (#64)
- RFC-010: Observability (#70)
- RFC-011: Scheduled Automation (#71)

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

# テスト実行
pytest

# 型チェック
pyright src/kagura/

# リンター
ruff check src/
```

### CI/CD
- GitHub Actions設定済み
- PyPI自動デプロイ設定済み
- Codecov統合済み

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
A: 以下のRFCが完了しています（2025-10-10現在）：
- ✅ RFC-007 Phase 1: MCP Integration（Claude Desktop統合）
- ✅ RFC-017: Shell Integration（シェル実行、Git自動化）
- ✅ RFC-018 Phase 1 & 2: Memory Management（3層メモリ + RAG検索）
- ✅ RFC-012 Phase 1 & 2: Commands & Hooks（コマンド + Hooks）
- ✅ RFC-016 Phase 1 & 2: Agent Routing（3種類のルーティング）
- ✅ RFC-006 Phase 1: Chat REPL（対話型チャット）

### Q2: RFC実装の優先順位は？
A:
1. ✅ RFC-007 Phase 1 (Very High) - MCP Integration **完了**
2. ✅ RFC-017 (High) - Shell Integration **完了**
3. ✅ RFC-018 Phase 1 & 2 (High) - Memory Management **完了**
4. ✅ RFC-012 Phase 1 & 2 (High) - Commands & Hooks **完了**
5. ✅ RFC-016 Phase 1 & 2 (High) - Agent Routing **完了**
6. ✅ RFC-006 Phase 1 (High) - Chat REPL **完了**
7. 🔜 RFC-002, 003, 007 Phase 2, 014 (Medium) - 次の候補
8. その他（Low-Medium）

### Q3: v2.1.0でどの機能が使える？
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

### Q4: Memory RAGの使い方は？
A:
```python
from kagura.core.memory import MemoryManager

# RAG有効化
memory = MemoryManager(agent_name="assistant", enable_rag=True)

# セマンティックメモリ保存
memory.store_semantic("Python is great for AI development")

# 意味検索
results = memory.recall_semantic("AI programming", top_k=5)
```

### Q5: Chat REPLの使い方は？
A:
```bash
# Chat REPL起動
kagura chat

# プリセットエージェント使用
/translate Hello World
/summarize <long text>
/review <code>
```

---

## 🎬 今すぐやること

### 次の開発を選択
1. 上記Option A〜Eから選択
2. 対応するIssueを確認
3. 実装開始

**推奨**: Option A（ドキュメント整理）から始めることをおすすめします！

---

## 📚 参考リンク

- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - v2.0.0詳細
- [coding_standards.md](./coding_standards.md) - コーディング規約
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - 全Issue一覧
- [RFC Documents](./rfcs/RFC_*.md) - 各RFC詳細仕様

---

**v2.1.0完了おめでとうございます！次はドキュメント整理がおすすめです 📚**
