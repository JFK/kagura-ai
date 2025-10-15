# Kagura AI 統合開発ロードマップ (v2.0.0 〜 v2.5.0+)

**最終更新**: 2025-10-15
**策定方針**: RFC駆動開発 - 全23個のRFC（001-025 + 171）を優先度・依存関係に基づいて統合

**現在地**: ✅ v2.5.0 ほぼ完了！→ リリース準備中（ドキュメント整理・Examples更新）

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

## ✅ Version 2.2.0: Unified Builder & Testing (Completed - 2025-10-10)

**リリース目標**: 統合ビルダー、テストフレームワーク、高度なワークフロー ✅ 達成

**リリース日**: 2025-10-10
**GitHub Release**: [v2.2.0](https://github.com/JFK/kagura-ai/releases/tag/v2.2.0)

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

### ✅ RFC-019: Unified Agent Builder (Completed - PR #111-113)
**関連Issue**: [#87](https://github.com/JFK/kagura-ai/issues/87)

#### 実装完了内容
- ✅ **Phase 1: Core Builder** (PR [#111](https://github.com/JFK/kagura-ai/pull/111))
  - `src/kagura/builder/agent_builder.py`: AgentBuilder（225行）
  - `src/kagura/builder/config.py`: Configuration classes（82行）
  - Fluent API pattern (method chaining)
  - `tests/builder/test_agent_builder.py`: 19テスト（全パス）

- ✅ **Phase 1.5: Memory + Tools Integration** (PR [#112](https://github.com/JFK/kagura-ai/pull/112))
  - `@agent` decorator に `tools` パラメータ追加
  - `_convert_tools_to_llm_format()` helper関数
  - Memory設定を`@agent`に渡す統合
  - 4つの統合テスト追加

- ✅ **Phase 2: Hooks + Presets** (PR [#113](https://github.com/JFK/kagura-ai/pull/113))
  - Hooks wrapper実装（pre/post hooks support）
  - `src/kagura/presets/chatbot.py`: ChatbotPreset
  - `src/kagura/presets/research.py`: ResearchPreset
  - `src/kagura/presets/code_review.py`: CodeReviewPreset
  - 11個のPresetテスト追加

#### 成功指標達成 ✅
- ✅ 複数機能の統合が簡単に
- ✅ 3つのプリセット提供
- ✅ Hooks統合
- ✅ 31個のテスト（全パス）

---

### ✅ RFC-022: Agent Testing Framework Phase 1 (Completed - PR #114)
**関連Issue**: TBD

#### 実装完了内容
- ✅ **Phase 1: Core Testing Framework** (PR #114)
  - `src/kagura/testing/testcase.py`: AgentTestCase（326行）
  - `src/kagura/testing/mocking.py`: Mocking utilities（103行）
  - `src/kagura/testing/utils.py`: Timer utility（28行）
  - `src/kagura/testing/plugin.py`: pytest plugin（42行）
  - `tests/testing/`: 34テスト（32パス、2スキップ）
  - `pyproject.toml`: testing optional dependency追加

#### 成功指標
- ✅ LLM非決定性に対応した柔軟なアサーション
- ✅ pytest統合（マーカー、フィクスチャ）
- ✅ モッキング機能でAPIコスト削減
- ✅ パフォーマンス・コスト検証

---

### ✅ RFC-020: Memory-Aware Routing (Completed - PR #116)
**関連Issue**: TBD

#### 実装完了内容
- ✅ **ContextAnalyzer** (PR #116)
  - `src/kagura/routing/context_analyzer.py`: ContextAnalyzer（214行）
  - 代名詞検出（it, this, that, them, etc.）
  - 暗黙的参照検出（also, too, again, etc.）
  - フォローアップ質問検出（what about, how about, etc.）
  - スマートフィルタリング（誤検知防止）
  - `tests/routing/test_context_analyzer.py`: 28テスト（全パス）

- ✅ **MemoryAwareRouter** (PR #116)
  - `src/kagura/routing/memory_aware_router.py`: MemoryAwareRouter（185行）
  - AgentRouter拡張（会話履歴考慮）
  - 自動文脈検出・クエリ強化
  - MemoryManager統合
  - オプションRAG対応
  - `tests/routing/test_memory_aware_router.py`: 20テスト（全パス）

#### 成功指標
- ✅ 文脈依存クエリの自動検出
- ✅ 会話履歴による自動補完
- ✅ 全83 routingテストがパス
- ✅ Pyright: 0 errors, Ruff: All checks passed

---

### ✅ RFC-001: Workflow System (Completed - PR #115)
**関連Issue**: #61

**ステータス**: ✅ 完了（全Phase実装済み）

#### ✅ 完了済み機能
1. **メモリ機能** → **RFC-018で実装済み** ✅
   - `@memory.session` 相当 → `MemoryManager`
   - `@memory.vector` 相当 → `MemoryRAG`

2. **ツールシステム** → **PR #103で実装済み** ✅
   - `@tool` デコレータ
   - ToolRegistry

3. **基本ワークフロー** → **PR #104で実装済み** ✅
   - `@workflow` デコレータ
   - WorkflowRegistry

4. **高度なワークフロー** → **PR #115で実装済み** ✅
   - `@workflow.chain` - シーケンシャル実行チェーン
   - `@workflow.parallel` - 並列実行ヘルパー（`run_parallel()`含む）
   - `@workflow.stateful` - Pydanticベースのステートグラフ
   - LangGraph互換のステート管理
   - `tests/core/test_workflow_advanced.py`: 17テスト（全パス）

#### ❌ 未実装機能（将来検討）
- `@cache` - キャッシングデコレータ
- `@batch` - バッチング処理
- `stream=True` - ストリーミングサポート

#### 成功指標
- ✅ Chain/Parallel/Statefulの3つの高度なパターン実装
- ✅ マルチエージェントオーケストレーション対応
- ✅ LangGraph互換性確保

---

### 🎯 v2.2.0 完了サマリー

**完了したRFC**: 6個（RFC-001, 018, 019, 020, 021, 022）
**マージしたPR**: 18個（#105, #111-118）
**新規テスト**: 246個（全パス、100%カバレッジ）
**総テスト数**: 586+
**リリース日**: 2025-10-10

---

## ✅ Version 2.3.0: Multimodal & Web (Completed - 2025-10-10)

**リリース目標**: マルチモーダルRAG、Web統合 ✅ 達成

**リリース日**: 2025-10-10
**GitHub Release**: [v2.3.0](https://github.com/JFK/kagura-ai/releases/tag/v2.3.0)

### ✅ RFC-002: Multimodal RAG (Completed - PR #117-131)
**関連Issue**: [#62](https://github.com/JFK/kagura-ai/issues/62)

#### 実装完了内容
- ✅ **マルチモーダルファイル処理** (PR #117-125)
  - 画像処理（PNG, JPG, GIF, WebP）- Gemini Vision API
  - PDF処理（PyPDF2）
  - 音声処理（MP3, WAV, M4A）- Whisper API
  - 動画処理（MP4, MOV, AVI）
  - `src/kagura/multimodal/`: 完全実装
  - `tests/multimodal/`: テスト実装

- ✅ **RAG Chat統合** (PR #136)
  - `kagura chat --enable-multimodal --dir <path>`
  - 全ファイルタイプのインデックス化
  - セマンティック検索による関連ファイル取得
  - ChromaDB統合

#### 成功指標
- ✅ `kagura chat --dir <path>` でディレクトリ全体を理解
- ✅ 画像・PDF・音声ファイルの内容を質問可能
- ✅ マルチモーダルベクトル検索動作

---

### ✅ RFC-014: Web Integration (Completed - PR #133-138)
**関連Issue**: ~~#75~~ (Closed - Completed in v2.3.0)

#### 実装完了内容
- ✅ **Web Search** (PR #133)
  - Brave Search API統合（無料枠2000クエリ/月）
  - DuckDuckGoフォールバック
  - `src/kagura/web/search.py`: 実装完了
  - `tests/web/test_search.py`: テスト完了

- ✅ **Web Scraping** (PR #135)
  - BeautifulSoup統合
  - robots.txt遵守
  - `src/kagura/web/scraper.py`: 実装完了
  - `tests/web/test_scraper.py`: テスト完了

- ✅ **エージェント統合** (PR #134, #137, #138)
  - `@web.enable` デコレータ
  - Chat REPL統合 (`--enable-web`)
  - Full-featured mode統合

#### 成功指標
- ✅ `web.search()` でリアルタイム情報取得
- ✅ `@web.enable` でエージェントに自動統合
- ✅ `kagura chat --enable-web` で即座にWeb検索可能

---

### 🎯 v2.3.0 完了サマリー

**完了したRFC**: 2個（RFC-002, RFC-014）
**マージしたPR**: 22個（#117-138）
**リリース日**: 2025-10-10

**主要機能**:
- ✅ Multimodal RAG（画像・音声・PDF・動画処理）
- ✅ Web Integration（Search + Scraping）
- ✅ Chat REPL統合

---

## ✅ Version 2.4.0: OAuth2 Authentication (Completed - 2025-10-13)

**リリース目標**: OAuth2認証システムの完全実装 ✅ 達成

**リリース日**: 2025-10-13
**GitHub Release**: [v2.4.0](https://github.com/JFK/kagura-ai/releases/tag/v2.4.0)

### ✅ RFC-013: OAuth2 Authentication (Completed - PR #154)
**関連Issue**: [#74](https://github.com/JFK/kagura-ai/issues/74)
**PR**: [#154](https://github.com/JFK/kagura-ai/pull/154) - ✅ Merged (2025-10-13)

#### 実装完了内容（Phase 1 & 2）

**Phase 1: Core OAuth2 Implementation（2025-10-11）**
1. ✅ **OAuth2Manager実装**
   - Google OAuth2認証フロー
   - Fernet暗号化（AES-128）
   - トークン自動リフレッシュ
   - 認証情報の安全な保存（0o600パーミッション）

2. ✅ **AuthConfig実装**
   - 設定管理システム
   - プロバイダー別スコープ管理

3. ✅ **Custom Exceptions実装**
   - NotAuthenticatedError
   - InvalidCredentialsError
   - エラーハンドリング

4. ✅ **CLI Commands実装**
   ```bash
   $ kagura auth login --provider google
   $ kagura auth status
   $ kagura auth logout
   ```

**Phase 2: Integration & Documentation（2025-10-13）**
5. ✅ **LLMConfig統合**
   - `auth_type` パラメータ（"api_key" | "oauth2"）
   - `oauth_provider` パラメータ
   - `get_api_key()` メソッドで OAuth2 トークン取得
   - LiteLLM統合（OAuth2トークンをAPI keyとして使用）

6. ✅ **ユーザードキュメント**
   - `docs/en/guides/oauth2-authentication.md`: ユーザーガイド（466行）
   - `docs/en/api/auth.md`: APIリファレンス（400行）
   - `docs/en/installation.md`: OAuth2セクション追加
   - MkDocsナビゲーション更新
   - **ドキュメント明確化**: API Key推奨、OAuth2は高度な機能

7. ✅ **Integration Tests**
   - `scripts/test_oauth2.py`: 手動テストスクリプト（464行）
   - `tests/integration/test_oauth2_integration.py`: 統合テスト（15テスト）
   - `ai_docs/OAUTH2_TESTING_GUIDE.md`: テストガイド（442行）

#### 成功指標（全Phase達成！）

**Phase 1**:
- ✅ 54+ユニットテスト（100% coverage）
- ✅ ブラウザログイン成功
- ✅ Fernet暗号化・0o600パーミッション

**Phase 2**:
- ✅ LLMConfig OAuth2統合完了
- ✅ 包括的ドキュメント（1772行）
- ✅ 統合テスト実装

**全体**:
- ✅ 65+テスト（95% coverage）
- ✅ Pyright 0 errors（strict mode）
- ✅ Ruff linting全パス
- ✅ CI全テストパス（897 passed）

#### 成果物

**Phase 1 実装ファイル**:
- `src/kagura/auth/oauth2.py`: OAuth2Manager（262行）
- `src/kagura/auth/config.py`: AuthConfig（99行）
- `src/kagura/auth/exceptions.py`: Custom Exceptions（48行）
- `src/kagura/cli/auth_cli.py`: CLI commands（157行）
- `tests/auth/`: 54+ユニットテスト（5ファイル）

**Phase 2 統合・ドキュメント**:
- `src/kagura/core/llm.py`: OAuth2統合
- `tests/core/test_llm_oauth2.py`: LLMConfig統合テスト（11テスト）
- `tests/integration/test_oauth2_integration.py`: 統合テスト（15テスト）
- `docs/en/guides/oauth2-authentication.md`: ユーザーガイド（466行）
- `docs/en/api/auth.md`: APIリファレンス（400行）
- `scripts/test_oauth2.py`: 手動テストスクリプト（464行）
- `ai_docs/OAUTH2_TESTING_GUIDE.md`: テストガイド（442行）

**統計**:
- **新規ファイル**: 14ファイル
- **変更ファイル**: 3ファイル
- **変更行数**: +5054 / -26
- **テスト数**: 65+ tests
- **ドキュメント**: 1772行

---

### RFC-003: Personal Assistant (Week 38-40)
**関連Issue**: [#63](https://github.com/JFK/kagura-ai/issues/63)

#### 実装内容
1. **RAG記憶システム** (Week 38)
   - 会話履歴をベクトルDB保存
   - ChromaDB / Qdrant統合
   - 長期記憶管理

2. **Few-shot Learning** (Week 39)
   - 最近の会話から動的Few-shot例生成
   - コンテキスト適応型プロンプト

3. **Auto Fine-tuning** (Week 40)
   ```python
   @agent(auto_finetune=True)
   async def my_assistant(query: str) -> str:
       """Personal assistant for {{ query }}"""
       pass
   ```

#### 成功指標
- ✅ 使うほど賢くなる体験
- ✅ ユーザー固有の振る舞い学習

---

## 🤖 Version 2.5.0: Meta Agent & Ecosystem (Week 43-50)

**リリース目標**: エージェント生成自動化、エコシステム拡大

### RFC-005: Meta Agent (Week 43-45)
**関連Issue**: #65

#### 実装内容
```bash
$ kagura create "GitHubのPR内容を要約するエージェント"
✓ エージェント生成中...
✓ テスト実行中...
✓ pr_summarizer.py 作成完了！
```

---

### RFC-008: Plugin Marketplace (Week 46-48)
**関連Issue**: #68

#### 実装内容
```bash
$ kagura search translator
$ kagura install @community/universal-translator
$ kagura publish my-agent
```

---

### RFC-009: Multi-Agent Orchestration (Week 49-50)
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

## 🌟 Version 2.6.0+: Advanced Features (Week 51+)

### RFC-004: Voice First Interface (Week 51-54)
**関連Issue**: #64
- 音声入出力（STT/TTS）

### RFC-006: LSP Integration (Week 55-58)
**関連Issue**: #66
- VS Code / Vim拡張

### RFC-010: Observability (Week 59-62)
**関連Issue**: #70
- コスト追跡、パフォーマンス監視

### RFC-011: Scheduled Automation (Week 63-66)
**関連Issue**: #71
- Cron、Webhook、ファイル監視

---

## 🚀 Version 2.7.0: API Server & Web Integration (Week 67+)

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

## 🌐 Version 2.8.0: Web UI & Dashboard (Week 75+)

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

## ☁️ Version 2.9.0+: SaaS化オプション (Week 85+)

### SaaS化機能（オプション）

#### 実装内容
- マルチテナント対応
- 従量課金システム
- エンタープライズ機能（SSO、監査ログ）
- Kubernetes/Docker Compose デプロイ

---

## 📈 マイルストーン一覧

| Version | リリース時期 | 主要機能 | 関連RFC | Status |
|---------|-------------|---------|---------|--------|
| v2.0.0 | 2025 Q4 | Core、Executor、CLI、REPL | - | ✅ |
| v2.1.0 | 2026 Q1 | MCP統合、Chat REPL、Commands & Hooks、Shell統合 | RFC-007, 006, 012, 017 | ✅ |
| v2.2.0 | 2026 Q2 | Unified Builder、Testing、Memory RAG | RFC-001, 018-022 | ✅ |
| v2.3.0 | 2026 Q3 | **Multimodal RAG、Web統合** | **RFC-002, 014** | ✅ |
| v2.4.0 | 2026 Q4 | **OAuth2認証** | **RFC-013** | ✅ |
| v2.5.0 | 2027 Q1 | Meta Agent、Marketplace、Orchestration | RFC-005, 008, 009 | 📋 |
| v2.6.0+ | 2027 Q2+ | Voice、LSP、Observability、Automation | RFC-004, 006, 010, 011 | 📋 |
| v2.7.0 | 2027 Q3 | API Server、REST/WebSocket | RFC-015 | 📋 |
| v2.8.0 | 2027 Q4 | Web UI、Dashboard、Marketplace UI | RFC-015, 005, 008 | 📋 |
| v2.9.0+ | 2028 Q1+ | SaaS化、マルチテナント、従量課金 | RFC-015 | 📋 |

---

## 🎯 次のアクション

### 現在地（2025-10-13）
- ✅ **v2.4.0 リリース完了！** 🎉
- ✅ RFC-013 (OAuth2 Authentication) Phase 1 & 2 実装完了
- ✅ **合計 41個のPR、16個のRFC（Phase含む）完了**
- ✅ **GitHub Release**: [v2.4.0](https://github.com/JFK/kagura-ai/releases/tag/v2.4.0)

### 📊 全RFCステータス（RFC-001〜022）
- **完了**: 16個（RFC-001, 002, 006, 007, 012, 013, 014, 016, 017, 018, 019, 020, 021, 022 + Phase含む）
- **v2.5.0候補**: 4個（RFC-003, 005, 008, 009）
- **未実装**: 2個（RFC-004, 010, 011, 015）
- **詳細**: `ai_docs/RFC_STATUS.md` 参照

### 🎯 v2.4.0 完了サマリー

**完了したRFC**: 1個（RFC-013 - OAuth2 Authentication）
**マージしたPR**: 1個（#154）
**新規テスト**: 65+ tests（65+ unit + 11 LLM integration + 15 integration）
**リリース日**: 2025-10-13

**主要機能**:
- ✅ OAuth2 Authentication（Google/Gemini対応）
- ✅ LLMConfig統合（`auth_type`, `oauth_provider`）
- ✅ 包括的ドキュメント（1772行）
- ✅ 手動テストスクリプト + 統合テスト

**技術的な学び**:
- Fernet暗号化（AES-128）でクレデンシャル保護
- Google auth libraryのtimezone-naive UTC datetime処理
- OAuth2トークンをLiteLLM API keyとして使用
- ドキュメント明確化の重要性（API Key推奨、OAuth2は高度な機能）

### 🚀 v2.5.0 開発候補

#### 🔥 推奨候補

1. **RFC-003: Personal Assistant** (#63) - 3週間
   - RAG記憶システム
   - Few-shot Learning
   - Auto Fine-tuning
   - ユーザー固有の振る舞い学習

2. **RFC-005: Meta Agent** (#65) - 3週間
   - 自然言語からエージェント生成
   - `kagura create` CLI
   - 自動テスト生成
   - コード生成・デプロイ

3. **RFC-008: Plugin Marketplace** (#68) - 3週間
   - コミュニティエージェント共有
   - `kagura search/install/publish` CLI
   - レーティング・レビューシステム

4. **RFC-009: Multi-Agent Orchestration** (#69) - 3週間
   - Team実装
   - エージェント間通信
   - 並列実行・シーケンシャル実行

---

## 📚 参考ドキュメント

- `ai_docs/DEVELOPMENT_ROADMAP.md` - v2.0.0詳細ロードマップ
- `ai_docs/rfcs/RFC_*.md` - 各RFC詳細仕様
- `ai_docs/coding_standards.md` - コーディング規約
- `.github/ISSUE_TEMPLATE/` - Issueテンプレート

---

**このロードマップはRFC駆動で進化します。新しいRFCが追加されたら、優先度に応じてバージョンにマッピングします。**

---

## ✅ Version 2.5.0: Meta Agent & Testing (Completed - 2025-10-15)

**リリース目標**: Meta Agent完成、Testing最適化、Production-ready達成 ✅ ほぼ達成

**リリース予定**: 2025-10-15（ドキュメント整理後）

### ✅ RFC-005: Meta Agent (All Phases Completed)

**Phase 1: Meta Agent Core** - PR #156 ✅
- 自然言語 → AgentSpec → Pythonコード生成
- `kagura build agent` CLI実装
- REPL/Chat統合

**Phase 2: Code-Aware Agent** - PR #158 ✅
- コード実行必要性の自動検出
- `execute_code` ツール自動追加
- Code execution template生成

**Phase 3: Self-Improving Agent** - PR #187 ✅
- ErrorAnalyzer: LLMベースのエラー分析
- CodeFixer: 自動コード修正
- SelfImprovingMetaAgent: リトライロジック

**成功指標**:
- ✅ 自然言語からエージェント生成
- ✅ コード実行自動検出
- ✅ エラー自動修正

---

### ✅ RFC-024: Context Compression (All Phases Completed)

**Phase 1: Token Management** - PR #160 ✅
- TokenCounter: tiktoken統合
- ContextMonitor: リアルタイム監視

**Phase 2: Message Trimming** - PR #161 ✅
- MessageTrimmer: 4戦略（last/first/middle/smart）

**Phase 3: Context Summarization** - PR #165 ✅
- ContextSummarizer: LLMベース要約

**Phase 4: Integration & Policy** - PR #166 ✅
- ContextManager: 統合インターフェース
- MemoryManager統合
- @agentデコレータ統合

**成功指標**:
- ✅ 長時間会話対応（10,000メッセージ）
- ✅ トークン削減90%
- ✅ Production-ready達成

---

### ✅ RFC-171: Testing Optimization (Completed)

**Phase 1: Parallel Execution** - PR #185 ✅
- pytest-xdist導入
- Worker-specific fixtures
- Unit tests: 24.6%高速化

**Phase 2: LLM Mocking** - PR #185 ✅
- Gemini APIモック
- Mock coverage: 55% → 95%
- Integration tests: 85-90%高速化

**Combined Results**:
- Full test suite: 5-10 min → ~2 min (60-80%削減)
- CI/CD: APIキー不要、コスト$0

---

### 📊 v2.5.0 統計

**完了したRFC**: 18個
- Core: 7個
- Memory & Context: 3個
- Multimodal & Web: 2個
- Quality & Tools: 4個
- Performance: 1個
- Authentication: 1個

**総テスト数**: 1,222 tests (99.7%パス)
**Coverage**: 90%+
**完了率**: 18/23 RFCs (78%)

---

### 🚀 v2.5.0 リリース前タスク

**今週中**:
1. Issue #188: ドキュメント整理
2. Issue #189: Examples更新（36サンプル）
3. Issue #190: CLAUDE.md更新
4. PR #187マージ
5. GitHub Release作成

---

**🎊 v2.5.0により、Kagura AIはproduction-readyフレームワークとして完成しました！**

---

## ✅ Version 2.5.1: Refactoring & Bug Fixes (Completed - 2025-10-15)

**リリース目標**: コード品質向上、クリティカルバグ修正 ✅ 達成

**リリース日**: 2025-10-15
**GitHub Release**: [v2.5.1](https://github.com/JFK/kagura-ai/releases/tag/v2.5.1)

### ✅ RFC-027: Bug Fixes - Shell Executor & Parser (Completed - PR #201)
**関連Issue**: [#200](https://github.com/JFK/kagura-ai/issues/200)
**PR**: [#201](https://github.com/JFK/kagura-ai/pull/201) - ✅ Merged (2025-10-15)

#### 実装完了内容

**Bug 1: Shell Executor Security Policy** (Critical)
- **問題**: ブロックコマンドチェックが過剰に厳格
  - パス文字列全体をチェックし、`/tmp/dnddt_test/`の"dd"でブロック
- **解決**: 精密なコマンド名マッチング
  - `blocked_commands`: `list[str]` → `dict[str, str]`（"exact"/"pattern"）
  - "exact": コマンド名のみチェック（第1ワード）
  - "pattern": 危険なパターンをサブストリングチェック
- **影響**: 4テスト失敗 → 修正

**Bug 2: AgentSpec Type Validation** (Medium)
- **問題**: `examples` フィールドが`dict[str, str]`のみ受付
  - LLM出力の数値例（`{"input": 3, "output": 6}`）が失敗
- **解決**: `dict[str, Any]`に変更
- **影響**: 1テスト失敗 → 修正

**Bug 3: TypeVar Usage Warning** (Low)
- **問題**: TypeVar "T"が一度しか使われていない
- **解決**: `parse_response(response: str, target_type: type[T]) -> T`
- **影響**: Pyright警告 → 解消

**Dependencies Upgrade**:
- Pyright: v1.1.390 → v1.1.406
- typing-extensions: 4.12.2 → 4.15.0

#### 成功指標（全達成！）

**テスト**:
- ✅ Pass Rate: 98.4% → 100% (1,213/1,213)
- ✅ 新規テスト: +7 (セキュリティポリシー)
- ✅ Pyright: 0 errors, 0 warnings (was 1 warning)
- ✅ Ruff: All checks passed

**セキュリティ**:
- ✅ 同じセキュリティレベル維持
- ✅ 精密な検出で誤検出を削減
- ✅ ユーザビリティ向上

#### 成果物

**実装ファイル**:
- `src/kagura/core/shell.py`: 精密なコマンドブロッキング（60行変更）
- `src/kagura/meta/spec.py`: 柔軟な型対応（11行変更）
- `src/kagura/core/parser.py`: TypeVar修正（10行変更）
- `tests/core/test_shell.py`: セキュリティテスト追加（66行追加）

**ドキュメント**:
- `ai_docs/rfcs/RFC_027_BUGFIX_SHELL_AND_PARSER.md`: RFC仕様（515行）
- `ai_docs/rfcs/RFC_027_IMPLEMENTATION_PLAN.md`: 実装計画（742行）
- `CHANGELOG.md`: 変更履歴（新規作成）

**統計**:
- **変更ファイル**: 9ファイル
- **変更行数**: +3,296 / -29
- **テスト**: 1,213 passed (100%)
- **ドキュメント**: 1,257行

---

### 🎯 v2.5.1 完了サマリー

**完了したRFC**: 1個（RFC-027 - Bug Fixes）
**マージしたPR**: 1個（#201）
**修正バグ**: 3個（Critical: 1, Medium: 1, Low: 1）
**リリース日**: 2025-10-15

**主要改善**:
- ✅ Shell Executor過剰制限解消
- ✅ AgentSpec型検証柔軟化
- ✅ TypeVar警告解消
- ✅ Pyright 1.1.406アップグレード
- ✅ 100%テスト成功率達成

**技術的な学び**:
- セキュリティポリシーの精密化（exact/pattern戦略）
- Pydantic型柔軟性（dict[str, Any]）
- TypeVar正しい使用法（type[T]パラメータ）
- Issue駆動開発の重要性

---

**🎊 v2.5.1により、Kagura AIのコード品質がさらに向上しました！**

