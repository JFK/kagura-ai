# Kagura AI - RFCs (Request for Comments)

このディレクトリには、Kagura AIの機能追加・変更に関する設計ドキュメント（RFC）が含まれています。

---

## 📋 Active RFCs（実装予定・進行中）

以下のRFCは現在実装予定、または一部実装中です。

### 🔥 High Priority

#### RFC-002: Multimodal RAG Chat
- **Status**: 🚧 **一部完了**（Phase 1-3完了、Phase 4未実装）
- **Issue**: [#62](https://github.com/JFK/kagura-ai/issues/62)
- **Target**: v2.3.0（Phase 1-3完了）, v2.4.0（Phase 4: Google Workspace）
- **Summary**:
  - ✅ Phase 1-3: Gemini API、マルチモーダルローダー、ChromaDB統合（v2.3.0完了）
  - ⏭️ Phase 4: Google Workspace連携（Drive/Calendar/Gmail）（v2.4.0延期）

#### RFC-014: Web Integration
- **Status**: 🚧 **一部完了**（Phase 1-2完了）
- **Issue**: [#75](https://github.com/JFK/kagura-ai/issues/75)
- **Target**: v2.3.0（Phase 1-2完了）
- **Summary**:
  - ✅ Phase 1-2: Web Search（Brave/DuckDuckGo）、Web Scraping（v2.3.0完了）

---

### 🥈 Medium Priority

#### RFC-013: OAuth2 Authentication
- **Status**: 📋 **Planning**
- **Issue**: [#74](https://github.com/JFK/kagura-ai/issues/74)
- **Target**: v2.4.0
- **Summary**: Google OAuth2認証でAPIキー不要化

#### RFC-015: Agent API Server
- **Status**: 📋 **Planning**
- **Issue**: [#86](https://github.com/JFK/kagura-ai/issues/86)
- **Target**: v2.6.0
- **Summary**: FastAPI HTTP/WebSocket API Server

---

### 🥉 Future Plans

#### RFC-003: Personal AI Assistant
- **Status**: 📋 **Planning**
- **Issue**: [#63](https://github.com/JFK/kagura-ai/issues/63)
- **Target**: v2.5.0+
- **Summary**: Auto Fine-tuning & Continuous Learning

#### RFC-004: Voice-First Interface
- **Status**: 📋 **Planning**
- **Issue**: [#64](https://github.com/JFK/kagura-ai/issues/64)
- **Target**: v2.5.0+
- **Summary**: 音声入出力機能（STT/TTS）

#### RFC-005: Meta Agent
- **Status**: 📋 **Planning**
- **Issue**: [#65](https://github.com/JFK/kagura-ai/issues/65)
- **Target**: v2.4.0
- **Summary**: AIエージェントを作るAI

#### RFC-008: Plugin Marketplace
- **Status**: 📋 **Planning**
- **Issue**: [#68](https://github.com/JFK/kagura-ai/issues/68)
- **Target**: v2.4.0
- **Summary**: コミュニティエージェント共有プラットフォーム

#### RFC-009: Multi-Agent Orchestration
- **Status**: 📋 **Planning**
- **Issue**: [#69](https://github.com/JFK/kagura-ai/issues/69)
- **Target**: v2.4.0
- **Summary**: 複数エージェント協調システム

#### RFC-010: Observability & Monitoring
- **Status**: 📋 **Planning**
- **Issue**: [#70](https://github.com/JFK/kagura-ai/issues/70)
- **Target**: v2.5.0+
- **Summary**: エージェント可視化・監視システム（RFC-021で一部実装済み）

#### RFC-011: Scheduled Agents & Automation
- **Status**: 📋 **Planning**
- **Issue**: [#71](https://github.com/JFK/kagura-ai/issues/71)
- **Target**: v2.5.0+
- **Summary**: 自動実行システム（Cron、Webhook、ファイル監視）

---

## ✅ Completed RFCs（完了済み）

完了済みのRFCは **[archive/completed/](archive/completed/)** に移動されました。

詳細は [archive/README.md](archive/README.md) を参照してください。

### v2.1.0 (2025-10-09)
- RFC-006: Live Coding
- RFC-007: MCP Integration (Phase 1)
- RFC-012: Commands & Hooks
- RFC-016: Agent Routing
- RFC-017: Shell Integration

### v2.2.0 (2025-10-10)
- RFC-018: Memory Management
- RFC-019: Unified Agent Builder
- RFC-020: Memory-Aware Routing
- RFC-021: Agent Observability Dashboard
- RFC-022: Agent Testing Framework

### v2.3.0 (2025-10-11)
- RFC-002: Multimodal RAG (Phase 1-3)
- RFC-014: Web Integration (Phase 1-2)

---

## 📝 RFCプロセス

### 1. RFC作成
新しい機能やアーキテクチャ変更を提案する際は、以下の手順に従ってください：

1. `ai_docs/rfcs/RFC_XXX_TITLE.md` を作成
2. テンプレート：
   ```markdown
   # RFC-XXX: Title

   **ステータス**: 提案中
   **作成日**: YYYY-MM-DD
   **対象バージョン**: vX.X.X
   **関連Issue**: #XXX

   ## 概要
   （3-5行で要約）

   ## 目標
   （ユーザー視点・開発者視点）

   ## アーキテクチャ
   （設計図、コード例）

   ## 実装スケジュール
   （Phase分割、見積もり）

   ## リスクと対策
   （予想される問題と解決策）
   ```

3. GitHub Issueを作成し、RFC番号をタイトルに含める
4. Pull Requestで提出（レビュー用）

### 2. レビュー & 承認
- コミュニティレビュー期間（最低3日）
- フィードバック対応
- 承認後、実装開始

### 3. 実装 & クローズ
- Phaseごとに分割実装
- 各Phase完了時にIssue更新
- 全Phase完了後、RFCを `archive/completed/` に移動

---

## 🔗 関連リンク

- [Unified Roadmap](../UNIFIED_ROADMAP.md) - 全体ロードマップ（v2.0.0〜v2.5.0+）
- [Next Steps](../NEXT_STEPS.md) - 次のアクション
- [GitHub Issues - RFC Label](https://github.com/JFK/kagura-ai/issues?q=label%3Arfc) - 全RFC Issue一覧
- [Archived RFCs](archive/) - 完了済みRFC

---

**Last Updated**: 2025-10-11
