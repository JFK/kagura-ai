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
  - Phase A-E（8-12ヶ月計画）
  - 各フェーズの実装内容
  - タスク分解・スケジュール

### 2. アーキテクチャ
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - システムアーキテクチャ
  - 3-tier memory system
  - GraphMemory（NetworkX）
  - MCP Server & REST API
  - データフロー

- **[MEMORY_STRATEGY.md](./MEMORY_STRATEGY.md)** - メモリー戦略
  - 3-tier memory詳細
  - RAG統合
  - GraphMemory統合
  - Memory Management Agent構想

### 3. 開発ガイドライン
- **[CODING_STANDARDS.md](./CODING_STANDARDS.md)** - コーディング規約
  - 命名規則
  - 型ヒント
  - Docstring形式
  - テスト要件

- **[DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)** - ドキュメント管理
  - ドキュメント構造
  - 更新ルール

### 4. 市場分析
- **[V4.0_COMPETITIVE_ANALYSIS.md](./V4.0_COMPETITIVE_ANALYSIS.md)** - 競合分析
  - vs Mem0, Rewind AI, ChatGPT Memory
  - 差別化ポイント

### 5. その他
- **[VISION.md](./VISION.md)** - プロジェクトビジョン
- **[GLOSSARY.md](./GLOSSARY.md)** - 用語集
- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** - CI/CD設定
- **[OPENAI_PRICING.md](./OPENAI_PRICING.md)** - LLM価格情報

---

## 📂 ディレクトリ構造

```
ai_docs/
├── README.md                          # このファイル（ナビゲーション）
│
├── V4.0_STRATEGIC_PIVOT.md            # v4.0戦略（最重要）
├── V4.0_IMPLEMENTATION_ROADMAP.md     # 実装ロードマップ
├── V4.0_COMPETITIVE_ANALYSIS.md       # 競合分析
├── V4.0_README_DRAFT.md               # 新README案
├── V4.0_GITHUB_ISSUE_TEMPLATE.md      # Issue template
│
├── ARCHITECTURE.md                    # システム設計
├── MEMORY_STRATEGY.md                 # メモリー戦略
├── CODING_STANDARDS.md                # コーディング規約
├── DOCUMENTATION_GUIDE.md             # ドキュメント管理
├── VISION.md                          # ビジョン
├── GLOSSARY.md                        # 用語集
├── GITHUB_ACTIONS_SETUP.md            # CI/CD
├── OPENAI_PRICING.md                  # 価格情報
│
├── rfcs/                              # RFC（設計提案）
│   ├── README.md                      # RFC一覧
│   ├── RFC_005_META_AGENT.md          # Active RFC
│   ├── RFC_033_CHAT_ENHANCEMENT.md    # Active RFC
│   └── future/                        # Future RFCs
│
└── archive/                           # 古いドキュメント
    ├── v3/                            # v3.0時代のドキュメント
    │   ├── V3.0_DEVELOPMENT.md
    │   ├── V3.0_PIVOT.md
    │   ├── V3.0_WORK_LOG.md
    │   └── ROADMAP_v3.md
    ├── work_logs/                     # 古い作業ログ
    ├── guides/                        # 古いガイド
    ├── rfcs/                          # 完了したRFC
    └── old_versions/                  # 古いバージョン
```

---

## 🎯 開発時の参照順序

### 新規機能開発時

1. **Issue内容** を確認
2. **V4.0_IMPLEMENTATION_ROADMAP.md** でフェーズ確認
3. **ARCHITECTURE.md** で実装場所確認
4. **CODING_STANDARDS.md** で規約確認
5. **実装**
6. **DOCUMENTATION_GUIDE.md** に従ってドキュメント更新

### バグ修正時

1. **Issue内容** を確認
2. **ARCHITECTURE.md** で該当モジュール確認
3. **修正**
4. **テスト追加**（回帰防止）
5. **CHANGELOG.md** 更新

### ドキュメント更新時

1. **DOCUMENTATION_GUIDE.md** の規則確認
2. **更新**
3. **ai_docs/README.md** に反映（必要に応じて）

---

## 📝 ドキュメント更新方針

### 更新頻度

- **V4.0_IMPLEMENTATION_ROADMAP.md**: 各Phase完了時
- **CHANGELOG.md**: リリース時
- **ARCHITECTURE.md**: 大きな設計変更時
- **MEMORY_STRATEGY.md**: メモリーシステム変更時

### アーカイブ方針

以下をarchiveに移動：
- ✅ v3.0関連ドキュメント → `archive/v3/`
- ✅ 古い作業ログ（1ヶ月以上前） → `archive/work_logs/`
- ✅ 完了したRFC → `archive/rfcs/completed/`
- ✅ 廃止された機能 → `archive/old_versions/`

---

## 🔍 よくある質問

### Q: v3.0とv4.0の違いは？
A: **V4.0_STRATEGIC_PIVOT.md** 参照

**v3.0**: Python SDK + Chat
**v4.0**: Universal AI Memory Platform (MCP-native + REST API)

### Q: 現在のフェーズは？
A: **V4.0_IMPLEMENTATION_ROADMAP.md** 参照

現在: **Phase B完了**（GraphMemory統合 #345）
次: Phase C（Self-hosted API）

### Q: ドキュメント構造がわからない
A: このREADMEの「ディレクトリ構造」セクション参照

### Q: 古いドキュメント（v3.0等）は？
A: `archive/v3/`ディレクトリ参照

---

**Last Updated**: 2025-10-26（v4.0 Phase B完了時）
**Maintained By**: Claude Code + Human developers
