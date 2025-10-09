# Kagura AI - Next Steps（次のアクション）

**最終更新**: 2025-10-09 (21:00)
**現在地**: v2.0.2 リリース済み、RFC-007 Phase 1 完了、RFC-017 完了 🎉

---

## 📍 現在の状況

### ✅ 完了済み（v2.0.0〜v2.0.2）
- **v2.0.2**: PyPI公開完了、安定版リリース
- **Core Engine**: @agent, Prompt Template, Type Parser（#14, #15, #16）
- **Code Executor**: AST検証、安全実行（#20, #21）
- **CLI & REPL**: Click CLI、prompt_toolkit REPL（#24, #25, #27, #56, #72）
- **テスト**: 統合テスト、カバレッジ79%（202 passed）
- **ドキュメント**: README、チュートリアル、サンプル（#32, #33, #34, #45, #54）
- **RFC作成**: 全18個のRFC（002-018）作成完了、Issue作成済み
- **統合ロードマップ**: `UNIFIED_ROADMAP.md`作成完了

### ✅ **NEW: RFC-007 MCP Integration Phase 1 完了（2025-10-09）**
- **PR #89**: MCP Server実装（Agent Registry, JSON Schema, MCP Server, CLI）
  - `src/kagura/core/registry.py`: Agent Registry（117行）
  - `src/kagura/mcp/schema.py`: JSON Schema生成（146行）
  - `src/kagura/mcp/server.py`: MCP Server（130行）
  - `src/kagura/cli/mcp.py`: CLI commands（121行）
  - `tests/mcp/`: 21テスト（100%パス）
- **PR #90**: MCP統合ドキュメント（1,172行）
  - `docs/en/tutorials/06-mcp-integration.md`: チュートリアル（400行）
  - `docs/en/api/mcp.md`: APIリファレンス（350行）
  - Claude Desktop設定方法（macOS/Windows/Linux対応）
- **PR #91**: ナビゲーションメニュー追加

**成果**: Kaguraエージェントを**Claude Desktop**で即座に利用可能に！

### ✅ **NEW: RFC-017 Shell Integration 完了（2025-10-09）**
- **PR #92**: Shell Integration & Built-in Agents実装（1,402行）
  - `src/kagura/core/shell.py`: ShellExecutor（261行）
  - `src/kagura/builtin/shell.py`: shell() 関数
  - `src/kagura/builtin/git.py`: Git操作（commit, push, status, PR）
  - `src/kagura/builtin/file.py`: File操作（search, grep）
  - `tests/builtin/`: 26テスト（全パス）
  - `docs/en/tutorials/07-shell-integration.md`: チュートリアル（216行）
  - `docs/en/api/shell.md`: APIリファレンス（289行）

**成果**: セキュアなシェルコマンド実行、Git自動化、ファイル操作が可能に！

### 🚧 進行中
- なし（RFC-017完了）

### 📝 次の優先タスク
- **RFC-018 (High)**: Memory Management System (#85)
- **RFC-006 (High)**: Live Coding - Chat REPL (#66)
- **RFC-012 (High)**: Commands & Hooks (#73)
- **RFC-016 (High)**: Agent Routing System (#83)
- **RFC-002〜005, 008〜015**: 詳細は `UNIFIED_ROADMAP.md` 参照

---

## 🎯 優先アクション（1-2週間）

### 1. 次の開発候補を選択

以下から選択してください：

#### Option A: RFC-018 - Memory Management（Week 1-2）
**Issue #85**

**実装内容**:
- [ ] Core Memory Types（Working/Context/Persistent）
- [ ] MemoryRAG（ChromaDB/Qdrant統合）
- [ ] Agent統合（`@agent(enable_memory=True)`）
- [ ] テスト・ドキュメント

**見積もり**: 2週間
**優先度**: High

---

#### Option B: RFC-006 - Chat REPL（Week 1-2）
**Issue #66**

**実装内容**:
- [ ] 対話型Chat REPL（`kagura chat`）
- [ ] プリセットコマンド（/translate, /summarize, /review）
- [ ] セッション管理
- [ ] テスト・ドキュメント

**見積もり**: 1.5週間
**優先度**: High

---

#### Option C: RFC-012 - Commands & Hooks（Week 1-2）
**Issue #73**

**実装内容**:
- [ ] Markdownコマンド定義
- [ ] PreToolUse / PostToolUse Hooks
- [ ] インライン実行 ``!`command` ``
- [ ] テスト・ドキュメント

**見積もり**: 2週間
**優先度**: High

---

#### Option D: RFC-016 - Agent Routing System（Week 1-2）
**Issue #83**

**実装内容**:
- [ ] Router実装（Intent Detection）
- [ ] Agent Selection Logic
- [ ] Fallback Handling
- [ ] テスト・ドキュメント

**見積もり**: 2週間
**優先度**: High

---

## 🚀 中期目標（v2.1.0〜v2.2.0）

### v2.1.0 候補機能
- RFC-018: Memory Management System
- RFC-006: Chat REPL
- RFC-012: Commands & Hooks
- RFC-016: Agent Routing System

### v2.2.0 候補機能
- RFC-002: Multimodal RAG
- RFC-014: Web Integration
- RFC-003: Personal Assistant

---

## 🌐 長期目標（v2.3.0以降）

### v2.3.0: Authentication & Security
- RFC-013: OAuth2 Auth (#74)

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

### Q1: RFC-007とRFC-017は完了？
A: はい！両方とも2025-10-09に完了しました。
- RFC-007 Phase 1: Claude DesktopでKaguraエージェント利用可能
- RFC-017: セキュアなシェル実行、Git自動化、ファイル操作

### Q2: RFC実装の優先順位は？
A:
1. ✅ RFC-007 (Very High) - MCP Integration Phase 1 **完了**
2. ✅ RFC-017 (High) - Shell Integration **完了**
3. RFC-006, 012, 016, 018 (High) - 次の候補
4. RFC-002, 003, 014 (Medium)
5. その他（Low-Medium）

### Q3: 途中でRFC追加される？
A: はい。`UNIFIED_ROADMAP.md`を随時更新します。

### Q4: v2.0.2でどの機能が使える？
A:
- ✅ `@agent` デコレータ
- ✅ Jinja2プロンプトテンプレート
- ✅ 型ベースパース（Pydantic対応）
- ✅ 安全なコード実行（CodeExecutor）
- ✅ CLI & REPL
- ✅ **MCP Integration** (Claude Desktop対応) ⭐️ NEW
- ✅ **Shell Integration** (シェル実行、Git自動化) ⭐️ NEW

---

## 🎬 今すぐやること

### 次の開発を選択
1. 上記Option A〜Dから選択
2. 対応するIssueを確認
3. 実装開始

---

## 📚 参考リンク

- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - v2.0.0詳細
- [coding_standards.md](./coding_standards.md) - コーディング規約
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - 全Issue一覧
- [RFC Documents](./rfcs/RFC_*.md) - 各RFC詳細仕様

---

**最優先タスク: 次の開発候補（Option A〜D）から選択して実装を開始する！**
