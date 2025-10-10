# Kagura AI 統合開発ロードマップ (v2.0.0 〜 v2.5.0+)

**最終更新**: 2025-10-10
**策定方針**: RFC駆動開発 - 全18個のRFC（002-018）を優先度・依存関係に基づいて統合

**現在地**: ✅ v2.1.0 リリース完了！

---

## 📊 全体スケジュール概要

```
2025 Q4        │ v2.0.0 Core Foundation (Week 1-12)
2026 Q1        │ v2.1.0 MCP & Live Coding (Week 13-18)
2026 Q2        │ v2.2.0 Multimodal & Web (Week 19-26)
2026 Q3        │ v2.3.0 Personal AI & Auth (Week 27-34)
2026 Q4        │ v2.4.0 Meta Agent & Ecosystem (Week 35-42)
2027 Q1+       │ v2.5.0+ Advanced Features (Week 43+)
```

---

## 🎯 Version 2.0.0: Core Foundation (Week 1-12)

**リリース目標**: Kagura AIの基盤機能を確立し、PyPIパッケージとして公開

### Phase 0: 準備・環境整備 (Week 1)
- [x] **Issue #1**: プロジェクトクリーンアップ（完了）
- [x] **Issue #2**: プロジェクト構造作成（完了）

### Phase 1: Core Engine (Week 2-4)
- **Issue #20**: `@agent` デコレータ実装
- **Issue #22**: Jinja2プロンプトテンプレートエンジン
- **Issue #23**: 型ベースレスポンスパーサー（Pydantic対応）

### Phase 2: Code Execution (Week 5-6)
- **Issue #21**: CodeExecutor（AST検証、Import制限）
- **Issue #24**: Code実行エージェント

### Phase 3: CLI & REPL (Week 7-8)
- **Issue #25**: CLIフレームワーク（Click）
- **Issue #27, #72**: REPL実装（prompt_toolkit、履歴、補完）

### Phase 4: 統合・テスト (Week 9-10)
- **Issue #26**: 統合テスト
- **Issue #28**: ドキュメント
- **Issue #29**: サンプルコード

### Phase 5: リリース (Week 11-12)
- **Issue #30, #31**: PyPIリリース

**成功指標**:
- ✅ テストカバレッジ 90%+
- ✅ `pip install kagura-ai` で動作
- ✅ 5行でエージェント作成可能

**ブロッカー**: なし

---

## ✅ Version 2.1.0: MCP & Live Coding (Completed - 2025-10-10)

**リリース目標**: Claude Codeとの相互運用、対話型チャット機能 ✅ 達成

### ✅ RFC-007: MCP Integration Phase 1 (Completed - PR #89-91)
**関連Issue**: #67

#### 実装完了内容
- ✅ **MCPサーバー実装** (PR #89)
  - `src/kagura/core/registry.py`: Agent Registry（117行）
  - `src/kagura/mcp/schema.py`: JSON Schema生成（146行）
  - `src/kagura/mcp/server.py`: MCP Server（130行）
  - `src/kagura/cli/mcp.py`: CLI commands（121行）
  - `tests/mcp/`: 21テスト（100%パス）

- ✅ **ドキュメント** (PR #90-91)
  - `docs/en/tutorials/06-mcp-integration.md`: チュートリアル（400行）
  - `docs/en/api/mcp.md`: APIリファレンス（350行）

#### 成功指標
- ✅ `kagura mcp start` でMCPサーバー起動成功
- ✅ Claude Desktopから Kaguraエージェント呼び出し可能

---

### ✅ RFC-006: Chat REPL Phase 1 (Completed - PR #102)
**関連Issue**: #66

#### 実装完了内容
- ✅ **対話型Chat REPL** (PR #102)
  - `src/kagura/cli/chat.py`: Chat REPL実装
  - `src/kagura/chat/preset.py`: プリセットエージェント
  - `kagura chat` コマンド
  - セッション管理
  - `tests/chat/`: Chat REPLテスト

- ✅ **プリセットコマンド**
  - `/translate <text>` - 翻訳
  - `/summarize <text>` - 要約
  - `/review <code>` - コードレビュー

#### 成功指標
- ✅ `kagura chat` で即座に対話可能
- ✅ プリセットコマンドが動作

**Note**: RFC-006のLSP統合部分はv2.5.0+に延期

---

### ✅ RFC-012: Commands & Hooks System (Completed - PR #95-97)
**関連Issue**: #73

#### 実装完了内容
- ✅ **Phase 1-A: Command Loader** (PR #95)
  - `src/kagura/commands/command.py`: Command dataclass（66行）
  - `src/kagura/commands/loader.py`: CommandLoader（104行）
  - Markdownファイルから YAML frontmatter + template 読み込み
  - `tests/commands/`: 23テスト（100%カバレッジ）

- ✅ **Phase 1-B: Inline Execution** (PR #96)
  - `src/kagura/commands/executor.py`: InlineCommandExecutor（157行）
  - `src/kagura/cli/commands_cli.py`: `kagura run` CLI（130行）
  - インライン実行: ``!`command` `` 構文
  - Jinja2テンプレートレンダリング

- ✅ **Phase 2: Hooks System** (PR #97)
  - `src/kagura/commands/hooks.py`: Hook実装
  - PreToolUse / PostToolUse hooks
  - Validation hooks

#### 成功指標
- ✅ `.kagura/commands/` でカスタムコマンド定義可能
- ✅ `kagura run` CLI実行可能
- ✅ Hooksでツール実行を制御可能

---

### ✅ RFC-017: Shell Integration (Completed - PR #92)
**関連Issue**: #84

#### 実装完了内容
- ✅ **ShellExecutor** (PR #92)
  - `src/kagura/core/shell.py`: ShellExecutor（261行）
  - セキュアなコマンド実行エンジン
  - Whitelist/Blacklist検証

- ✅ **Built-in Agents**
  - `src/kagura/builtin/shell.py`: shell() 関数
  - `src/kagura/builtin/git.py`: Git操作（commit, push, status, PR）
  - `src/kagura/builtin/file.py`: File操作（search, grep）
  - `tests/builtin/`: 26テスト（全パス）

- ✅ **ドキュメント**
  - `docs/en/tutorials/07-shell-integration.md`: チュートリアル（216行）
  - `docs/en/api/shell.md`: APIリファレンス（289行）

#### 成功指標
- ✅ `await shell.exec("git status")` で安全にコマンド実行
- ✅ ビルトインエージェントが動作
- ✅ セキュリティポリシー有効

---

### ✅ RFC-016: Agent Routing System (Completed - PR #98, #101)
**関連Issue**: #83

#### 実装完了内容
- ✅ **Phase 1: Basic Routing** (PR #98)
  - `src/kagura/routing/router.py`: BaseRouter実装
  - `src/kagura/routing/keyword.py`: KeywordRouter（キーワードベース）
  - `src/kagura/routing/llm.py`: LLMRouter（LLMベース）
  - Intent Detection & Agent Selection
  - `tests/routing/`: ルーティングテスト

- ✅ **Phase 2: Semantic Routing** (PR #101)
  - `src/kagura/routing/semantic.py`: SemanticRouter（semantic-router統合）
  - ベクトルベースのルーティング
  - `pyproject.toml`: routing optional dependency追加
  - `tests/routing/test_semantic.py`: セマンティックルーティングテスト

#### 成功指標
- ✅ Keyword/LLM/Semanticの3種類のルーティング戦略実装
- ✅ `router.route()` で自動エージェント選択
- ✅ Semantic matching動作

---

### ✅ Core Decorators (Completed - PR #103, #104)

#### @tool Decorator (PR #103)
- `src/kagura/core/decorators.py`: @tool デコレータ実装
- `src/kagura/core/tool_registry.py`: ToolRegistry（117行）
- 型検証、シグネチャ管理
- `tests/core/test_tool_*.py`: テスト（11 registry + 12 decorator）
- `docs/en/tutorials/11-tools.md`: チュートリアル（580行）
- `docs/en/api/tools.md`: APIリファレンス（562行）

#### @workflow Decorator (PR #104)
- `src/kagura/core/decorators.py`: @workflow デコレータ実装
- `src/kagura/core/workflow_registry.py`: WorkflowRegistry（117行）
- マルチエージェントオーケストレーション
- `tests/core/test_workflow_*.py`: テスト（11 registry + 12 decorator）
- `docs/en/tutorials/12-workflows.md`: チュートリアル（580行）
- `docs/en/api/workflows.md`: APIリファレンス（562行）

#### 成功指標
- ✅ @agent, @tool, @workflow の3つのコアデコレータが完成
- ✅ 各デコレータのレジストリシステム実装
- ✅ 完全なドキュメント整備

---

## 🌐 Version 2.2.0: Multimodal & Web (Week 19-26)

**リリース目標**: マルチモーダルRAG、Web検索・スクレイピング、メモリー管理

### ✅ RFC-018: Memory Management System (Completed - PR #94, #105)
**関連Issue**: #85

#### 実装完了内容
- ✅ **Phase 1: Core Memory Types** (PR #94)
  - `src/kagura/core/memory/working.py`: WorkingMemory（99行）
  - `src/kagura/core/memory/context.py`: ContextMemory（166行）
  - `src/kagura/core/memory/persistent.py`: PersistentMemory（249行）
  - `src/kagura/core/memory/manager.py`: MemoryManager（263行）
  - `@agent` デコレータにメモリ統合
  - `tests/core/memory/`: 66テスト（100%カバレッジ）

- ✅ **Phase 2: Memory RAG** (PR #105)
  - `src/kagura/core/memory/rag.py`: MemoryRAG（167行）
  - ChromaDB統合でベクトル検索
  - `store_semantic()` / `recall_semantic()` メソッド
  - エージェントスコープのセマンティック検索
  - `tests/core/test_memory_rag.py`: 9テスト（全パス）
  - `pyproject.toml`: memory optional dependency追加

- ✅ **ドキュメント**
  - `docs/en/tutorials/08-memory-management.md`: チュートリアル（429行）
  - `docs/en/api/memory.md`: APIリファレンス（479行）

#### 成功指標
- ✅ エージェントが記憶を保持（Working/Context/Persistent）
- ✅ セマンティック検索動作（ChromaDB RAG）
- ✅ セッション保存・復元可能

---

### RFC-002: Multimodal RAG (Week 22-24)
**関連Issue**: #62

#### 実装内容
1. **マルチモーダル対応** (Week 22)
   - 画像・音声・動画・PDF処理
   - Gemini Vision API統合
   - RFC-018 Memory統合

2. **RAG Chat** (Week 23)
   ```bash
   $ kagura chat --dir ./project
   You: この図の意味は？
   AI: （画像を解析）このアーキテクチャ図は...
   ```

3. **Google Workspace連携** (Week 24)
   - Drive / Calendar / Gmail統合
   - `@workspace.enable` デコレータ

#### 成功指標
- ✅ `kagura chat --dir <path>` でディレクトリ全体を理解
- ✅ 画像・PDF・音声ファイルの内容を質問可能

---

### RFC-014: Web Integration (Week 25-26)
**関連Issue**: #75

#### 実装内容
1. **Web Search** (Week 25)
   - Brave Search API（無料枠2000クエリ/月）
   - DuckDuckGoフォールバック
   - RFC-018 Memory統合（検索履歴）

2. **Web Scraping** (Week 25)
   - BeautifulSoup統合
   - robots.txt遵守

3. **エージェント統合** (Week 26)
   ```python
   @agent
   @web.enable
   async def research(topic: str) -> str:
       """Research {{ topic }} using web search"""
       pass
   ```

#### 成功指標
- ✅ `web.search()` でリアルタイム情報取得
- ✅ `@web.enable` でエージェントに自動統合

---

## 🤖 Version 2.3.0: Personal AI & Auth (Week 27-34)

**リリース目標**: パーソナライズされたAIアシスタント

### RFC-003: Personal Assistant (Week 27-32)
**関連Issue**: #63

#### 実装内容
1. **RAG記憶システム** (Week 27-28)
   - 会話履歴をベクトルDB保存
   - ChromaDB / Qdrant統合

2. **Few-shot Learning** (Week 29-30)
   - 最近の会話から動的Few-shot例生成

3. **Auto Fine-tuning** (Week 31-32)
   ```python
   @agent(auto_finetune=True)
   async def my_assistant(query: str) -> str:
       """Personal assistant for {{ query }}"""
       pass
   ```

#### 成功指標
- ✅ 使うほど賢くなる体験
- ✅ 月次自動ファインチューニング

---

### RFC-013: OAuth2 Authentication (Week 32-34)
**関連Issue**: #74

#### 実装内容
1. **Google OAuth2** (Week 32-33)
   ```bash
   $ kagura auth login --provider google
   → ブラウザでログイン → 完了
   ```

2. **認証情報管理** (Week 34)
   - Fernet暗号化保存
   - 自動トークンリフレッシュ

#### 成功指標
- ✅ APIキー不要でGemini使用可能

---

## 🛠️ Version 2.4.0: Meta Agent & Ecosystem (Week 35-42)

**リリース目標**: エージェント生成自動化、エコシステム拡大

### RFC-005: Meta Agent (Week 35-37)
**関連Issue**: #65

#### 実装内容
```bash
$ kagura create "GitHubのPR内容を要約するエージェント"
✓ エージェント生成中...
✓ テスト実行中...
✓ pr_summarizer.py 作成完了！
```

---

### RFC-008: Plugin Marketplace (Week 38-40)
**関連Issue**: #68

#### 実装内容
```bash
$ kagura search translator
$ kagura install @community/universal-translator
$ kagura publish my-agent
```

---

### RFC-009: Multi-Agent Orchestration (Week 41-42)
**関連Issue**: #69

#### 実装内容
```python
team = Team("data-pipeline")
team.add_agent(collector)
team.add_agent(analyzer)

await team.parallel([
    team.collector(source=s) for s in sources
])
```

---

### RFC-016: Agent Routing - Phase 3 (Future)

**Note**: Phase 1 & 2 は v2.1.0 で完了済み (PR #98, #101)

#### 将来の拡張内容
1. **Chain & RFC-009統合**
   - AgentChain実装
   - Team内自動ルーティング
   - 動的チーム構成

#### 統合例（将来）
```python
from kagura import Team

# Team統合
team = Team("support")
team_router = AgentRouter()
team_router.register(billing_agent, intents=["billing"])
team_router.register(tech_agent, intents=["technical"])

@team.workflow
async def support(query: str):
    return await team_router.route(query)
```

#### 将来の成功指標
- [ ] RFC-009 Team統合
- [ ] 動的チーム構成

---

## 🌟 Version 2.5.0+: Advanced Features (Week 43+)

### RFC-004: Voice First Interface (Week 43-46)
**関連Issue**: #64
- 音声入出力（STT/TTS）

### RFC-006: LSP Integration (Week 47-50)
**関連Issue**: #66
- VS Code / Vim拡張

### RFC-010: Observability (Week 51-54)
**関連Issue**: #70
- コスト追跡、パフォーマンス監視

### RFC-011: Scheduled Automation (Week 55-58)
**関連Issue**: #71
- Cron、Webhook、ファイル監視

---

## 🚀 Version 2.6.0: API Server & Web Integration (Week 59+)

### RFC-015: Agent API Server ⭐️ NEW
**関連Issue**: TBD

#### 実装内容
1. **FastAPI Server** (Week 59-62)
   - REST API (register, execute, list, delete)
   - WebSocket (ストリーミング実行)
   - JWT/API Key認証

2. **セキュリティ** (Week 63-64)
   - サンドボックス強化（Docker）
   - レート制限
   - 監査ログ

3. **CLI** (Week 65-66)
   ```bash
   $ kagura api start --port 8000
   $ kagura api register --file my_agent.py
   ```

4. **クライアントSDK** (Week 67-68)
   ```javascript
   // JavaScript SDK
   const kagura = new KaguraClient('http://localhost:8000');
   const result = await kagura.execute('translate', { text: 'Hello' });
   ```

#### 成功指標
- ✅ REST API完全実装
- ✅ WebSocket ストリーミング動作
- ✅ Python以外のクライアント（JS、Go）から実行可能
- ✅ ドキュメント完備（OpenAPI/Swagger）

---

## 🌐 Version 2.7.0: Web UI & Dashboard (Week 69+)

### Web UI実装（RFC-015統合）

#### 実装内容
1. **Agent Builder UI** (Week 69-72)
   - 自然言語 → Meta Agent → コード生成 → 登録
   - RFC-005統合

2. **Agent Executor UI** (Week 73-74)
   - エージェント選択
   - パラメータ入力フォーム
   - 実行 → リアルタイム結果表示

3. **Dashboard** (Week 75-76)
   - 実行履歴
   - コスト分析
   - パフォーマンス統計

4. **Marketplace UI** (Week 77-78)
   - RFC-008統合
   - コミュニティエージェント検索
   - ワンクリックインストール

---

## ☁️ Version 2.8.0+: SaaS化オプション (Week 79+)

### SaaS化機能（オプション）

#### 実装内容
- マルチテナント対応
- 従量課金システム
- エンタープライズ機能（SSO、監査ログ）
- Kubernetes/Docker Compose デプロイ

---

## 📈 マイルストーン一覧

| Version | リリース時期 | 主要機能 | 関連RFC |
|---------|-------------|---------|---------|
| v2.0.0 | 2025 Q4 | Core、Executor、CLI、REPL | - |
| v2.1.0 | 2026 Q1 | MCP統合、Chat REPL、Commands & Hooks、**Shell統合** | RFC-007, 006, 012, **017** |
| v2.2.0 | 2026 Q2 | **Memory管理**、Multimodal RAG、Web統合 | **RFC-018**, 002, 014 |
| v2.3.0 | 2026 Q3 | Personal Assistant、OAuth2 | RFC-003, 013 |
| v2.4.0 | 2026 Q4 | Meta Agent、Marketplace、Orchestration、Agent Routing | RFC-005, 008, 009, 016 |
| v2.5.0+ | 2027 Q1+ | Voice、LSP、Observability、Automation | RFC-004, 006, 010, 011 |
| v2.6.0 | 2027 Q2 | API Server、REST/WebSocket、認証 | RFC-015 |
| v2.7.0 | 2027 Q3 | Web UI、Dashboard、Marketplace UI | RFC-015, 005, 008 |
| v2.8.0+ | 2027 Q4+ | SaaS化、マルチテナント、従量課金 | RFC-015 |

---

## 🎯 次のアクション

### 現在地（2025-10-10）
- ✅ **v2.1.0 リリース完了！**
- ✅ RFC-007, 006, 012, 017, 018, 016 実装完了
- ✅ @agent, @tool, @workflow の3つのコアデコレータ完成
- ✅ 合計 13個のPR、8個のRFC（Phase含む）完了

### 次の候補（v2.2.0に向けて）
1. **RFC-002**: Multimodal RAG (#62)
2. **RFC-014**: Web Integration (#75)
3. **RFC-003**: Personal Assistant (#63)
4. **RFC-007 Phase 2**: MCP Memory Protocol (#67)

---

## 📚 参考ドキュメント

- `ai_docs/DEVELOPMENT_ROADMAP.md` - v2.0.0詳細ロードマップ
- `ai_docs/rfcs/RFC_*.md` - 各RFC詳細仕様
- `ai_docs/coding_standards.md` - コーディング規約
- `.github/ISSUE_TEMPLATE/` - Issueテンプレート

---

**このロードマップはRFC駆動で進化します。新しいRFCが追加されたら、優先度に応じてバージョンにマッピングします。**
