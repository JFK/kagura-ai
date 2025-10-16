# Kagura AI - RFCs (Request for Comments)

このディレクトリには、Kagura AIの機能追加・変更に関する設計ドキュメント（RFC）が含まれています。

**最終更新**: 2025-10-16

---

## 📂 ディレクトリ構造

```
rfcs/
├── README.md                    # このファイル
├── RFC_XXX_TITLE.md             # 実装中のRFC（root）
├── archive/
│   └── completed/               # 完了済みRFC
└── future/                      # 将来構想のRFC（Draft）
```

---

## 🚧 実装中のRFC（Active）

rootディレクトリに配置されているRFCは、現在実装中または次の実装対象です。

| RFC | タイトル | Status | Priority | Target |
|-----|---------|--------|----------|--------|
| [RFC-005](./RFC_005_META_AGENT.md) | Meta Agent | Phase 1&2完了、Phase 3未実装 | ⭐️⭐️⭐️ High | v2.6.0 |
| [RFC-033](./RFC_033_CHAT_ENHANCEMENT.md) | Chat Enhancement | RFC作成済み | ⭐️⭐️⭐️ High | v2.6.0 |
| [RFC-034](./RFC_034_HIPPOCAMPUS_MEMORY.md) | Hippocampus Memory | RFC作成済み | ⭐️⭐️ Medium | v2.6.0+ |
| [RFC-035](./RFC_035_TOOL_AGENT_BUILDER_IN_CHAT.md) | Tool/Agent Builder | RFC作成済み | ⭐️⭐️ Medium | v2.6.0+ |

### RFC-005: Meta Agent（一部完了）
- ✅ Phase 1: Core Meta Agent（完了 - v2.4.0）
- ✅ Phase 2: Validator & CLI（完了 - v2.4.0）
- ⏳ Phase 3: Self-Improving Agent（未実装 - v2.6.0予定）

### RFC-033: Chat Enhancement
- 6 Phases計画（Auto-Discovery, Meta Agent統合, Agent DB, UX改善等）
- 関連Issue: #221（Phase 1）, #232（YouTube Analysis）

### RFC-034: Hippocampus Memory
- 長期記憶システムの高度化
- Episodic/Semantic/Procedural memory

### RFC-035: Tool/Agent Builder in Chat
- Chat内でのツール・エージェント動的生成
- 関連Issue: #228

---

## ✅ 完了済みRFC（Completed）

**場所**: [archive/completed/](./archive/completed/)

完了済みRFCはarchive/completed/ディレクトリに移動されています。

### v2.0.0-2.1.0
- **RFC-001**: Workflow System
- **RFC-006**: Live Coding / Chat REPL
- **RFC-007**: MCP Integration Phase 1
- **RFC-012**: Commands & Hooks System
- **RFC-016**: Agent Routing System
- **RFC-017**: Shell Integration

### v2.2.0
- **RFC-018**: Memory Management System
- **RFC-019**: Unified Agent Builder
- **RFC-020**: Memory-Aware Routing
- **RFC-021**: Agent Observability Dashboard
- **RFC-022**: Agent Testing Framework Phase 1

### v2.3.0-2.4.0
- **RFC-002**: Multimodal RAG（Phase 1-3）
- **RFC-013**: OAuth2 Authentication
- **RFC-014**: Web Integration（Phase 1-2）

### v2.5.0-2.5.10
- **RFC-024**: Context Compression（All Phases）
- **RFC-027**: Bug Fixes（Shell & Parser）
- **RFC-028**: Pydantic v2 Migration
- **RFC-030**: Telemetry Integration Phase 1
- **RFC-031**: CLI Startup Optimization
- **RFC-032**: MCP Full Feature Integration Phase 1&2

詳細は[archive/completed/README.md](./archive/completed/README.md)を参照。

---

## 🔮 将来構想のRFC（Future）

**場所**: [future/](./future/)

Draft状態、または長期的な構想のRFCです。

| RFC | タイトル | Priority | 見積もり |
|-----|---------|----------|---------|
| [RFC-003](./future/RFC_003_PERSONAL_ASSISTANT.md) | Personal AI Assistant | ⭐️⭐️ Medium | v2.7.0+ |
| [RFC-004](./future/RFC_004_VOICE_FIRST_INTERFACE.md) | Voice-First Interface | ⭐️⭐️ Medium | v2.7.0+ |
| [RFC-008](./future/RFC_008_PLUGIN_MARKETPLACE.md) | Plugin Marketplace | ⭐️ Low | v3.0.0 |
| [RFC-009](./future/RFC_009_MULTI_AGENT_ORCHESTRATION.md) | Multi-Agent Orchestration | ⭐️⭐️ Medium | v2.8.0+ |
| [RFC-010](./future/RFC_010_OBSERVABILITY.md) | Observability拡張 | ⭐️ Low | v2.7.0+ |
| [RFC-011](./future/RFC_011_SCHEDULED_AUTOMATION.md) | Scheduled Agents | ⭐️⭐️ Medium | v2.7.0+ |
| [RFC-015](./future/RFC_015_AGENT_API_SERVER.md) | Agent API Server | ⭐️⭐️ Medium | v2.8.0+ |
| [RFC-025](./future/RFC_025_BROADLISTENING_EXAMPLE.md) | Broadlistening Example | ⭐️ Low | 未定 |
| [RFC-025](./future/RFC_025_PERFORMANCE_OPTIMIZATION.md) | Performance Optimization | ⭐️⭐️ Medium | v2.7.0+ |
| [RFC-026](./future/RFC_026_PRESET_EXPANSION.md) | Preset Expansion | ⭐️⭐️ Medium | v2.6.0+ |
| [RFC-029](./future/RFC_029_SECRET_CONFIG_MANAGEMENT.md) | Secret Management | ⭐️⭐️⭐️ High | v2.6.0 |

---

## 📊 RFC統計

| Category | Count |
|----------|-------|
| **Active** (実装中) | 4 |
| **Completed** (完了済み) | 16+ |
| **Future** (将来構想) | 11 |
| **Total** | 31+ |

---

## 📝 RFCプロセス

### 1. RFC作成

新しい機能やアーキテクチャ変更を提案する際：

1. **RFCファイル作成**: `ai_docs/rfcs/RFC_XXX_TITLE.md`
2. **GitHub Issue作成**: RFC番号をタイトルに含める
3. **Draft状態で配置**: `future/`ディレクトリ

**テンプレート**:
```markdown
# RFC-XXX: Title

**ステータス**: Draft
**作成日**: YYYY-MM-DD
**優先度**: ⭐️⭐️⭐️ High / ⭐️⭐️ Medium / ⭐️ Low
**対象バージョン**: vX.X.X
**関連Issue**: #XXX

## 📋 概要
（3-5行で要約）

## 🎯 目標
（成功指標）

## 🏗️ アーキテクチャ
（設計図、コード例）

## 📦 実装Phase
（Phase分割、各Phaseの成果物）

## 🧪 テスト計画
（テスト戦略、カバレッジ目標）

## 📅 スケジュール
（見積もり、マイルストーン）

## 🔒 リスクと対策
（予想される問題と解決策）
```

### 2. レビュー & 承認

- コミュニティレビュー期間（最低3日）
- フィードバック対応
- 承認後、`future/` → root に移動

### 3. 実装

- Phaseごとに分割実装
- 各Phase完了時にIssue更新
- GitHub Issue駆動開発（必須）

### 4. 完了 & アーカイブ

- 全Phase完了後、`archive/completed/` に移動
- Issue自動クローズ
- リリースノートに記載

---

## 🎯 現在の優先順位（2025-10-16）

### 最優先（今すぐ）
1. **RFC-033 Phase 1** (#221) - Auto-Discovery
   - Chat UX向上の核心
   - 作業量: 2-3日

### 高優先度（今月）
2. **RFC-029** (#204) - Secret Management
   - Production必須
   - 作業量: 1週間

3. **RFC-005 Phase 3** - Self-Improving Agent
   - Meta Agent完成
   - 作業量: 1週間

### 中優先度（来月以降）
4. **RFC-035** (#228) - Tool Builder in Chat
5. **RFC-034** - Hippocampus Memory
6. **RFC-026** - Preset Expansion

---

## 🔗 関連ドキュメント

- [Unified Roadmap](../UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [Next Steps](../NEXT_STEPS.md) - 次のアクション
- [Next Plan v2.5.0](../NEXT_PLAN_v2.5.0.md) - v2.5.0詳細計画
- [GitHub Issues - RFC Label](https://github.com/JFK/kagura-ai/issues?q=label%3Arfc) - 全RFC Issue一覧
- [Coding Standards](../coding_standards.md) - コーディング規約

---

## 📖 RFC番号ルール

- **RFC-001 ~ RFC-024**: 初期RFC（v2.0.0 ~ v2.5.0）
- **RFC-025 ~ RFC-035**: 追加RFC（v2.5.0+）
- **RFC-036+**: 将来のRFC

番号は連番で付与。欠番なし。

---

**このREADMEは、RFCの現状を一目で把握するための索引です。**
**RFCの詳細は各ファイルを参照してください。**
