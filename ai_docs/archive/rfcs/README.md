# Archived RFCs

このディレクトリには**完了済み**のRFC（Request for Comments）が保管されています。

設計思想や実装の背景を理解するためのリファレンスとして残していますが、最新の実装状況は必ず**GitHub Issues**を参照してください。

---

## 📁 Archive Structure

```
archive/
├── completed/     # 実装完了したRFC
└── README.md      # このファイル
```

---

## ✅ Completed RFCs

### v2.1.0 (Released: 2025-10-09)
- **RFC-006**: Live Coding - AI-Powered Pair Programming
  - Issue: [#66](https://github.com/JFK/kagura-ai/issues/66)
  - PR: [#102](https://github.com/JFK/kagura-ai/pull/102)
  - Status: Chat REPL Phase 1 完了（LSP統合はv2.5.0+に延期）

- **RFC-007**: MCP Integration - Model Context Protocol統合
  - Issue: [#67](https://github.com/JFK/kagura-ai/issues/67)
  - PR: [#89-91](https://github.com/JFK/kagura-ai/pull/89)
  - Status: Phase 1 完了（Phase 2はv2.4.0に延期）

- **RFC-012**: Custom Commands & Hooks System
  - Issue: [#73](https://github.com/JFK/kagura-ai/issues/73)
  - PR: [#95-97](https://github.com/JFK/kagura-ai/pull/95)
  - Status: Phase 1 & 2 完了

- **RFC-016**: Agent Routing System
  - Issue: [#80](https://github.com/JFK/kagura-ai/issues/80), [#87](https://github.com/JFK/kagura-ai/issues/87)
  - PR: [#98](https://github.com/JFK/kagura-ai/pull/98), [#101](https://github.com/JFK/kagura-ai/pull/101)
  - Status: Phase 1 & 2 完了（Keyword/LLM/Semantic routing）

- **RFC-017**: Shell Integration & Command Execution
  - Issue: [#84](https://github.com/JFK/kagura-ai/issues/84)
  - PR: [#92](https://github.com/JFK/kagura-ai/pull/92)
  - Status: 完了（ShellExecutor, Built-in Agents）

### v2.2.0 (Released: 2025-10-10)
- **RFC-018**: Memory Management System
  - Issue: [#85](https://github.com/JFK/kagura-ai/issues/85)
  - PR: [#94](https://github.com/JFK/kagura-ai/pull/94), [#105](https://github.com/JFK/kagura-ai/pull/105)
  - Status: Phase 1 & 2 完了（Working/Context/Persistent + RAG）

- **RFC-019**: Unified Agent Builder
  - Issue: [#107](https://github.com/JFK/kagura-ai/issues/107)
  - PR: [#111-113](https://github.com/JFK/kagura-ai/pull/111)
  - Status: 完了（Builder API + Presets）

- **RFC-020**: Memory-Aware Routing
  - Issue: [#108](https://github.com/JFK/kagura-ai/issues/108)
  - PR: [#116](https://github.com/JFK/kagura-ai/pull/116)
  - Status: 完了（ContextAnalyzer + MemoryAwareRouter）

- **RFC-021**: Agent Observability Dashboard
  - Issue: [#109](https://github.com/JFK/kagura-ai/issues/109)
  - PR: [#117-118](https://github.com/JFK/kagura-ai/pull/117)
  - Status: 完了（EventStore + TUI Dashboard）

- **RFC-022**: Agent Testing Framework
  - Issue: [#110](https://github.com/JFK/kagura-ai/issues/110)
  - PR: [#114](https://github.com/JFK/kagura-ai/pull/114)
  - Status: Phase 1 完了（AgentTestCase, Mocking）

---

## 📖 アーカイブされたRFCの使い方

### 参照目的
- ✅ 設計思想を理解する
- ✅ 実装の背景を知る
- ✅ 新規RFC作成時のテンプレートとして使う

### ⚠️ 注意事項
- **実装状況は必ずGitHub Issuesを確認**してください
- アーカイブされたRFCは更新されません（スナップショット）
- 最新のAPIドキュメントは `docs/en/api/` を参照

---

## 🔗 関連リンク

- [Active RFCs](../) - 実装予定・進行中のRFC
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues?q=label%3Arfc) - 全RFC Issue一覧
- [Unified Roadmap](../../UNIFIED_ROADMAP.md) - 全体ロードマップ
- [Next Steps](../../NEXT_STEPS.md) - 次のアクション

---

**Last Updated**: 2025-10-11
