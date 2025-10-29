# AI Developer Documentation

Kagura AI v4.0の開発ドキュメント。AI開発者向け。

---

## 📚 必読ドキュメント（優先順）

### 1. 戦略・ロードマップ
- **[V4.0_STRATEGIC_PIVOT.md](./V4.0_STRATEGIC_PIVOT.md)** - v4.0戦略方針（最重要）
  - なぜv4.0に移行したか
  - Universal AI Memory Platformのビジョン
  - MCP-first approach
  - Multimodal戦略

- **[V4.0_IMPLEMENTATION_ROADMAP.md](./V4.0_IMPLEMENTATION_ROADMAP.md)** - 実装ロードマップ
  - Phase A-F（8-12ヶ月計画）
  - ✅ Phase A: MCP-First Foundation (Complete)
  - ✅ Phase B: GraphMemory (Complete)
  - ✅ Phase C: Remote MCP + Export/Import (Complete)
  - 各フェーズの実装内容とタスク分解

### 2. アーキテクチャ
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - システムアーキテクチャ（v4.0更新済み）
  - MCP Server (stdio & HTTP/SSE)
  - Memory Manager (4-tier system)
  - Graph Memory (NetworkX)
  - REST API & Authentication
  - Remote MCP Server architecture
  - Security layers

- **[MEMORY_STRATEGY.md](./MEMORY_STRATEGY.md)** - メモリー戦略（v4.0 Phase C完了）
  - Multi-tier memory system (4-tier + Graph)
  - RAG統合 (ChromaDB/Qdrant)
  - GraphMemory統合 (NetworkX)
  - Export/Import strategy (JSONL)

- **[../src/kagura/core/memory/README.md](../src/kagura/core/memory/README.md)** - Temperature-based Hierarchy設計
  - 🔥 Hot/Warm/Cool/Cold階層
  - Important Memory Protection
  - Hebbian学習アルゴリズム
  - Memory Curator設計
  - High Context実現方法
  - **実装ガイド** (Phase 1-3)
  - [Issue #453](https://github.com/JFK/kagura-ai/issues/453)

### 3. 開発ガイドライン
- **[CODING_STANDARDS.md](./CODING_STANDARDS.md)** - コーディング規約
  - 命名規則（snake_case, PascalCase）
  - 型ヒント必須（pyright strict）
  - Docstring形式（Google style）
  - テスト要件（90%+ coverage）

- **[GLOSSARY.md](./GLOSSARY.md)** - 用語集（v4.0更新済み）
  - v4.0コア概念
  - Phase C用語
  - CLI commands
  - 略語一覧

### 4. 市場分析
- **[V4.0_COMPETITIVE_ANALYSIS.md](./V4.0_COMPETITIVE_ANALYSIS.md)** - 競合分析
  - vs Mem0, Rewind AI, ChatGPT Memory
  - 差別化ポイント
  - 市場機会

### 5. その他
- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** - CI/CD設定

---

## 📂 ディレクトリ構造

```
ai_docs/
├── README.md                          # このファイル（ナビゲーション）
│
├── V4.0_STRATEGIC_PIVOT.md            # v4.0戦略（最重要）
├── V4.0_IMPLEMENTATION_ROADMAP.md     # 実装ロードマップ
├── V4.0_COMPETITIVE_ANALYSIS.md       # 競合分析
│
├── ARCHITECTURE.md                    # システム設計（v4.0）
├── MEMORY_STRATEGY.md                 # メモリー戦略
├── CODING_STANDARDS.md                # コーディング規約
├── GLOSSARY.md                        # 用語集（v4.0）
├── GITHUB_ACTIONS_SETUP.md            # CI/CD
│
└── archive/                           # 古いドキュメント
    └── v3/                            # v3.0時代のドキュメント
```

**削除済み** (Phase C完了時):
- ❌ `VISION.md` - V4.0_STRATEGIC_PIVOT.mdに統合
- ❌ `DOCUMENTATION_GUIDE.md` - 古いv3.0管理ルール
- ❌ `OPENAI_PRICING.md` - 古い料金情報
- ❌ `V4.0_README_DRAFT.md` - ドラフト（README完成）
- ❌ `V4.0_GITHUB_ISSUE_TEMPLATE.md` - 使用済み

---

## 🎯 開発時の参照順序

### 新規機能開発時

1. **GitHub Issue内容** を確認
2. **V4.0_IMPLEMENTATION_ROADMAP.md** でフェーズ・タスク確認
3. **ARCHITECTURE.md** で実装場所確認
4. **CODING_STANDARDS.md** で規約確認
5. **実装** (TDD推奨)
6. **テスト** (pytest, カバレッジ90%+)
7. **ドキュメント更新** (user docs in `docs/`)

### バグ修正時

1. **Issue内容** を確認
2. **ARCHITECTURE.md** で該当モジュール確認
3. **修正**
4. **テスト追加**（回帰防止）
5. **CHANGELOG.md** 更新

---

## 📝 ドキュメント更新方針

### 更新タイミング

- **V4.0_IMPLEMENTATION_ROADMAP.md**: 各Phase完了時にステータス更新
- **CHANGELOG.md**: PR merge時、リリース時
- **ARCHITECTURE.md**: 大きな設計変更時（Phase完了時等）
- **MEMORY_STRATEGY.md**: メモリーシステム変更時
- **GLOSSARY.md**: 新用語追加時、Phase完了時

### Phase C完了時の更新（2025-10-27完了）

- ✅ `ARCHITECTURE.md` - Remote MCP architecture追加
- ✅ `GLOSSARY.md` - Phase C用語追加
- ✅ `V4.0_IMPLEMENTATION_ROADMAP.md` - Phase C完了マーク
- ✅ `README.md` (this file) - ディレクトリ構造更新

---

## 🔍 よくある質問

### Q: v3.0とv4.0の違いは？
A: **V4.0_STRATEGIC_PIVOT.md** 参照

**v3.0**: Python SDK-First + Chat
**v4.0**: Universal AI Memory Platform (MCP-native)

### Q: 現在のフェーズは？
A: **V4.0_IMPLEMENTATION_ROADMAP.md** 参照

**現在**: Phase C完了 (2025-10-27)
- ✅ Phase A: MCP-First Foundation
- ✅ Phase B: GraphMemory
- ✅ Phase C: Remote MCP Server + Export/Import

**次**: v4.0.0 stable release → Phase D (Multimodal MVP)

### Q: Phase Cで何が実装された？
A: Issue #378 参照

**Week 1-2**: Remote MCP Server (HTTP/SSE, API Auth, Tool Filtering)
**Week 3**: Memory Export/Import (JSONL)
**Week 4**: Production Deployment (Docker, Caddy)

### Q: Claude Desktop統合は引き続き動く？
A: **完全後方互換** ✅

`kagura mcp serve` は全31ツールにアクセス可能（変更なし）

---

## 🔗 関連リソース

### GitHub
- [Issues](https://github.com/JFK/kagura-ai/issues)
- [Pull Requests](https://github.com/JFK/kagura-ai/pulls)
- [Discussions](https://github.com/JFK/kagura-ai/discussions)

### User Documentation
- [docs/](../docs/) - ユーザー向けドキュメント
- [examples/](../examples/) - 使用例

---

**Last Updated**: 2025-10-29（Temperature-based Hierarchy設計追加）
**Maintained By**: Claude Code + Human developers
**Status**: Phase C Complete, v4.0.0 stable準備中、Phase 1実装開始予定（Issue #453）
