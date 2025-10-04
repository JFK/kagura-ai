# Kagura AI 統合開発ロードマップ (v2.0.0 〜 v2.5.0+)

**最終更新**: 2025-10-04
**策定方針**: RFC駆動開発 - 全13個のRFC（002-014）を優先度・依存関係に基づいて統合

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

## 🚀 Version 2.1.0: MCP & Live Coding (Week 13-18)

**リリース目標**: Claude Codeとの相互運用、対話型チャット機能

### RFC-007: MCP Integration ⭐️ Very High Priority
**関連Issue**: #67

#### 実装内容
1. **MCPサーバー実装** (Week 13-14)
   - Kaguraエージェント → MCPツール変換
   - `mcp install kagura-ai` 対応
   - Claude Code、Clineから呼び出し可能に

2. **MCPクライアント実装** (Week 15-16)
   - Kagura → 既存MCPツール呼び出し
   - `@mcp.use("fetch", "filesystem")` デコレータ

3. **双方向統合** (Week 17-18)
   - Kagura ⇄ Claude Code完全統合
   - ドキュメント・サンプル作成

#### 依存関係
- `mcp>=1.0.0`（Anthropic公式SDK）
- v2.0.0のCore機能完了

#### 成功指標
- ✅ Claude Code内で `mcp install kagura-ai` 成功
- ✅ Kaguraから `@mcp.use("fetch")` で外部ツール呼び出し可能

---

### RFC-006: Live Coding - Chat REPL (Week 15-17)
**関連Issue**: #66

#### 実装内容
1. **対話型Chat REPL**
   ```bash
   $ kagura chat
   You: 今日の天気は？
   AI: （Web検索して）東京は晴れ...
   ```

2. **プリセットコマンド**
   - `/translate <text>` - 翻訳
   - `/summarize <text>` - 要約
   - `/review <code>` - コードレビュー

3. **セッション管理**
   - 会話履歴の自動保存
   - `kagura chat --session <name>` で再開

#### 成功指標
- ✅ エージェント定義不要で即座に対話可能
- ✅ プリセットコマンドが動作

**Note**: RFC-006のLSP統合部分はv2.5.0+に延期

---

### RFC-012: Commands & Hooks System (Week 16-18)
**関連Issue**: #73

#### 実装内容
1. **Markdownコマンド定義**
   ```markdown
   ---
   name: commit-pr
   allowed_tools: [git, gh]
   ---
   ## Task
   Create commit, push, and PR
   ```

2. **Hooks System**
   - PreToolUse / PostToolUse
   - セキュリティバリデーション

3. **インライン実行**
   - ``!`git status` `` 構文

#### 成功指標
- ✅ `.kagura/commands/` でカスタムコマンド定義可能
- ✅ Hooksでツール実行を制御可能

---

## 🌐 Version 2.2.0: Multimodal & Web (Week 19-26)

**リリース目標**: マルチモーダルRAG、Web検索・スクレイピング

### RFC-002: Multimodal RAG (Week 19-23)
**関連Issue**: #62

#### 実装内容
1. **マルチモーダル対応** (Week 19-20)
   - 画像・音声・動画・PDF処理
   - Gemini Vision API統合

2. **RAG Chat** (Week 21-22)
   ```bash
   $ kagura chat --dir ./project
   You: この図の意味は？
   AI: （画像を解析）このアーキテクチャ図は...
   ```

3. **Google Workspace連携** (Week 23)
   - Drive / Calendar / Gmail統合
   - `@workspace.enable` デコレータ

#### 成功指標
- ✅ `kagura chat --dir <path>` でディレクトリ全体を理解
- ✅ 画像・PDF・音声ファイルの内容を質問可能

---

### RFC-014: Web Integration (Week 24-26)
**関連Issue**: #75

#### 実装内容
1. **Web Search** (Week 24)
   - Brave Search API（無料枠2000クエリ/月）
   - DuckDuckGoフォールバック

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

## 📈 マイルストーン一覧

| Version | リリース時期 | 主要機能 | 関連RFC |
|---------|-------------|---------|---------|
| v2.0.0 | 2025 Q4 | Core、Executor、CLI、REPL | - |
| v2.1.0 | 2026 Q1 | MCP統合、Chat REPL、Commands & Hooks | RFC-007, 006, 012 |
| v2.2.0 | 2026 Q2 | Multimodal RAG、Web統合 | RFC-002, 014 |
| v2.3.0 | 2026 Q3 | Personal Assistant、OAuth2 | RFC-003, 013 |
| v2.4.0 | 2026 Q4 | Meta Agent、Marketplace、Orchestration | RFC-005, 008, 009 |
| v2.5.0+ | 2027 Q1+ | Voice、LSP、Observability、Automation | RFC-004, 006, 010, 011 |

---

## 🎯 次のアクション

### 現在地（2025-10-04）
- ✅ v2.0.0 Phase 1-2 完了（Core Engine、Executor）
- 🚧 v2.0.0 Phase 3 進行中（REPL改善 #72）
- 📝 RFC-013/014 作成完了、Issue #74/#75 作成済み

### 即座に着手
1. **Issue #72**: REPL改善（prompt_toolkit統合）
2. **v2.0.0 Phase 4-5**: 統合テスト、ドキュメント、PyPIリリース

### Week 13以降
3. **RFC-007実装開始**: MCP Integration (#67)
4. **RFC-006 Chat REPL**: 対話型AI (#66)

---

## 📚 参考ドキュメント

- `ai_docs/DEVELOPMENT_ROADMAP.md` - v2.0.0詳細ロードマップ
- `ai_docs/rfcs/RFC_*.md` - 各RFC詳細仕様
- `ai_docs/coding_standards.md` - コーディング規約
- `.github/ISSUE_TEMPLATE/` - Issueテンプレート

---

**このロードマップはRFC駆動で進化します。新しいRFCが追加されたら、優先度に応じてバージョンにマッピングします。**
