# Kagura AI v2.5.0 開発計画（改訂版）

**作成日**: 2025-10-13
**最終更新**: 2025-10-14
**現在地**: ✅ v2.4.0 リリース完了 + RFC-005 Phase 2 完了！
**次の目標**: v2.5.0 - Context Compression（最優先） + Meta Agent

---

## 🚨 重要な方針変更（2025-10-14）

**LangChain Context Engineering分析の結果、RFC-024 Context Compression Systemが最優先課題であることが判明しました。**

### 問題の深刻度

現在のKagura AIには**Context Compression機能が完全に欠如**しており：
- ❌ 長時間会話でコンテキストリミットに必ず達する
- ❌ トークン管理機能がない（使用量不明、コスト予測不可）
- ❌ Personal Assistant（RFC-003）実装が不可能
- ❌ **Production環境で使用不可能**

### 新しい優先順位

1. **🔥🔥🔥 RFC-024: Context Compression**（Week 1-5）← **最優先**
2. **⭐️ RFC-005 Phase 3: Self-Improving Agent**（Week 6-8）
3. **⭐️ RFC-010拡張: Deep Observability**（Week 9-11）

**参照**:
- [Context Engineering分析レポート](./CONTEXT_ENGINEERING_ANALYSIS.md)
- [RFC-024仕様書](./rfcs/RFC_024_CONTEXT_COMPRESSION.md)

---

## 📍 現在の状況サマリー

### ✅ 直近の達成（2025-10-13 - 2025-10-14）

**v2.4.0 リリース完了**:
- ✅ RFC-013: OAuth2 Authentication（Google OAuth2統合）
- ✅ 65+ tests、全パス
- ✅ 包括的ドキュメント（1772行）

**RFC-005 Phase 1 & 2 完了**:
- ✅ Phase 1: Meta Agent Core（自然言語→コード生成）
- ✅ Phase 2: Code-Aware Agent（コード実行自動検出）
- ✅ PR #156, #158 マージ済み
- ✅ 52テスト（全パス）、CI通過

**Context Engineering分析完了**（2025-10-14）:
- ✅ LangChainベストプラクティス調査
- ✅ Kagura AI現状評価（3/5）
- ✅ Critical Gaps特定
- ✅ RFC-024作成（Context Compression）
- ✅ Issue #159作成

### 📊 完了したRFC（16個）

1. ✅ RFC-001: Workflow System（Advanced patterns）
2. ✅ RFC-002: Multimodal RAG（Gemini統合）
3. ✅ RFC-006: Chat REPL（Phase 1）
4. ✅ RFC-007: MCP Integration（Phase 1）
5. ✅ RFC-012: Commands & Hooks
6. ✅ RFC-013: OAuth2 Authentication
7. ✅ RFC-014: Web Integration
8. ✅ RFC-016: Agent Routing（Keyword/LLM/Semantic）
9. ✅ RFC-017: Shell Integration
10. ✅ RFC-018: Memory Management（3層 + RAG）
11. ✅ RFC-019: Unified Agent Builder
12. ✅ RFC-020: Memory-Aware Routing
13. ✅ RFC-021: Agent Observability Dashboard
14. ✅ RFC-022: Agent Testing Framework
15. ✅ **RFC-005 Phase 1**: Meta Agent Core
16. ✅ **RFC-005 Phase 2**: Code-Aware Agent

---

## 🎯 v2.5.0 開発目標

**リリース目標**: Meta Agent の完成 + エコシステム構築の基盤
**期間**: 3-4週間
**優先度**: High

### 🚀 v2.5.0 の価値提案

1. **Meta Agent Phase 3**: Self-Improving Agent（エラー自動修正）
2. **エコシステム拡大**: Plugin基盤、コミュニティ統合準備
3. **実用性向上**: エンドツーエンドの開発体験完成

---

## 📋 v2.5.0 実装計画（改訂版）

### 🔥 プラン A': Context Compression優先（最新推奨）⭐️⭐️⭐️

**期間**: 5-6週間
**優先度**: 🔥🔥🔥 **Critical**

**理由**: Context Compression なしでは Production 環境で使用不可能

#### Week 1: RFC-024 Phase 1 - Token Management

**Issue**: #159（作成済み）
**RFC**: [RFC-024](./rfcs/RFC_024_CONTEXT_COMPRESSION.md)
**Phase 1 Plan**: [RFC_024_PHASE1_PLAN.md](./rfcs/RFC_024_PHASE1_PLAN.md)

**実装内容**:

1. **TokenCounter実装**（Day 1-2）
   ```python
   # src/kagura/core/compression/token_counter.py
   class TokenCounter:
       def count_tokens(self, text: str) -> int:
           """Count tokens using tiktoken"""
           pass

       def count_tokens_messages(self, messages: list[dict]) -> int:
           """Count tokens in message history"""
           pass

       def should_compress(self, current: int, max: int) -> bool:
           """Decide if compression needed"""
           pass
   ```

   - tiktoken統合
   - 全モデル対応（OpenAI, Claude, Gemini）
   - トークンカウント正確性（誤差±5%）

2. **ContextMonitor実装**（Day 3-4）
   ```python
   # src/kagura/core/compression/monitor.py
   class ContextMonitor:
       def check_usage(self, messages: list[dict]) -> ContextUsage:
           """Monitor context window usage"""
           pass
   ```

   - リアルタイム使用量監視
   - 自動圧縮トリガー判定
   - モデル別リミット対応

3. **依存関係追加 & テスト**（Day 5-7）
   - `pyproject.toml` 更新（tiktoken追加）
   - 27+ tests実装（TokenCounter 17, Monitor 8, Integration 2）
   - ドキュメント作成
   - PR作成

**成功指標**:
- ✅ 全モデルのトークンカウント正確（誤差±5%以内）
- ✅ コンテキスト使用量をリアルタイム監視可能
- ✅ 27+ tests全パス
- ✅ Pyright 0 errors

#### Week 2: RFC-024 Phase 2 - Message Trimming

**実装内容**:

1. **MessageTrimmer実装**（Day 1-4）
   ```python
   # src/kagura/core/compression/trimmer.py
   class MessageTrimmer:
       def trim(
           self, messages: list[dict], max_tokens: int,
           strategy: "last" | "first" | "middle" | "smart"
       ) -> list[dict]:
           """Trim messages to fit token limit"""
           pass
   ```

   - 4つの戦略実装（last/first/middle/smart）
   - Smart trimming（重要メッセージ保持）
   - システムメッセージ保護

2. **テスト & PR**（Day 5-7）
   - 20+ tests実装
   - ドキュメント作成
   - PR作成

**成功指標**:
- ✅ 4戦略全て動作
- ✅ トークン削減率50%+
- ✅ 重要メッセージ保持率90%+
- ✅ 20+ tests全パス

#### Week 3-4: RFC-024 Phase 3 - Context Summarization

**実装内容**:

1. **ContextSummarizer実装**（Week 3）
   ```python
   # src/kagura/core/compression/summarizer.py
   class ContextSummarizer:
       async def summarize_recursive(...) -> str:
           """Recursively summarize conversation"""
           pass

       async def compress_preserve_events(...) -> list[dict]:
           """Preserve key events, summarize routine"""
           pass
   ```

   - LLMベース要約（recursive/hierarchical）
   - キーイベント保持型圧縮
   - 25+ tests実装

2. **テスト & 品質検証**（Week 4）
   - 要約品質検証（人間評価）
   - PR作成

**成功指標**:
- ✅ 10,000メッセージ→500トークン圧縮
- ✅ キーイベント保持率95%+
- ✅ 要約品質4/5以上
- ✅ 25+ tests全パス

#### Week 5: RFC-024 Phase 4 - Integration

**実装内容**:

1. **ContextManager & Policy**（Day 1-3）
   ```python
   # Unified interface
   class ContextManager:
       async def compress(self, messages: list[dict]) -> list[dict]:
           """Auto compression with policy"""
           pass
   ```

   - CompressionPolicy実装
   - 統合インターフェース
   - 自動圧縮トリガー

2. **MemoryManager統合**（Day 4-5）
   - `@agent`デコレータ統合
   - 既存テスト全パス確認

3. **最終テスト & ドキュメント**（Day 6-7）
   - 30+ integration tests
   - ユーザーガイド完成
   - PR作成・マージ

**成功指標**:
- ✅ 自動圧縮動作
- ✅ 100+ 新規テスト全パス
- ✅ 全既存テスト（900+）パス
- ✅ ドキュメント完備

---

#### Week 6-8: RFC-005 Phase 3 - Self-Improving Agent（オプション）

RFC-024完了後、余裕があれば実装。詳細は別途計画。

---

### プラン B: エコシステム優先

**期間**: 3週間
**優先度**: Medium-High

#### Week 1-2: RFC-008 Phase 1 - Plugin Marketplace Core

- Plugin登録・検索システム
- `kagura plugin install/search/publish` CLI
- レーティング・レビューシステム基盤

#### Week 3: RFC-009 Phase 1 - Multi-Agent Orchestration

- Team基本実装
- エージェント間通信
- 並列実行基盤

**判断基準**:
- Meta Agentの完成度を優先するか
- エコシステム拡大を優先するか

→ **推奨**: プランA（Meta Agent完成を優先）

---

### プラン C: 小規模改善集中

**期間**: 1-2週間
**優先度**: Medium

1. **ドキュメント整備**（3日）
   - 全機能のチュートリアル更新
   - API reference完成度向上
   - examples/更新

2. **バグ修正・リファクタリング**（3日）
   - 既知のバグ修正
   - コード品質向上
   - テストカバレッジ向上

3. **パフォーマンス最適化**（2日）
   - LLM呼び出し最適化
   - キャッシング改善
   - 並列処理強化

**判断基準**:
- 安定性・品質を優先する場合に選択

---

## 🎯 推奨アクション（次に進むべきこと）

### 🥇 最優先: プランA - Meta Agent Phase 3

**理由**:
1. **完成度**: RFC-005 Phase 1 & 2 が完了済み、Phase 3で完結
2. **価値**: Self-Improving Agentは革新的機能
3. **ユーザー体験**: エラーハンドリングでUXが劇的に向上
4. **エコシステム準備**: Week 3でエコシステム基盤も構築

**次のステップ**:
```bash
# 1. Issue作成
gh issue create --title "RFC-005 Phase 3: Self-Improving Agent" \
  --body "..."

# 2. RFC Plan作成
touch ai_docs/rfcs/RFC_005_PHASE3_PLAN.md

# 3. ブランチ作成
git checkout -b feature/RFC-005-phase3-self-improving-agent

# 4. 実装開始
# src/kagura/meta/error_analyzer.py
# src/kagura/meta/fixer.py
# ...
```

---

## 📊 v2.5.0 成功指標（改訂版）

### 機能

- ✅ RFC-024完了（Context Compression System）
- ✅ 長時間会話対応（10,000メッセージ）
- ✅ トークン削減率: 90%（圧縮時）
- ✅ 自動圧縮（ユーザー介入不要）

### 品質

- ✅ 100+ 新規テスト（全パス）
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ カバレッジ: 90%+
- ✅ 圧縮後も回答精度95%+維持

### ドキュメント

- ✅ 包括的ユーザーガイド
- ✅ APIリファレンス完備
- ✅ Best Practices文書

### ユーザー体験

- ✅ Production環境で使用可能
- ✅ コンテキストリミット到達なし
- ✅ コスト削減（トークン使用量削減）

---

## 🔄 代替プラン（状況次第）

### シナリオ 1: 急ぎでエコシステムが必要

→ **プランB** を選択（Plugin Marketplace + Multi-Agent Orchestration）

### シナリオ 2: 安定性・品質を優先

→ **プランC** を選択（ドキュメント・バグ修正・リファクタリング）

### シナリオ 3: 新機能追加要望

→ **ロードマップ調整**（RFC-003 Personal Assistant等を前倒し）

---

## 📅 スケジュール（プランA' - RFC-024優先）

```
Week 1 (10/14-10/20): RFC-024 Phase 1 - Token Management
├─ Day 1-2: TokenCounter実装（tiktoken統合）
├─ Day 3-4: ContextMonitor実装
├─ Day 5: 依存関係追加 & 統合
└─ Day 6-7: テスト（27+ tests）& ドキュメント & PR

Week 2 (10/21-10/27): RFC-024 Phase 2 - Message Trimming
├─ Day 1-4: MessageTrimmer実装（4戦略）
└─ Day 5-7: テスト（20+ tests）& ドキュメント & PR

Week 3 (10/28-11/03): RFC-024 Phase 3 - Summarization (Part 1)
├─ Day 1-4: ContextSummarizer実装（recursive/hierarchical）
└─ Day 5-7: Event-preserving compression実装

Week 4 (11/04-11/10): RFC-024 Phase 3 - Summarization (Part 2)
├─ Day 1-3: テスト（25+ tests）
└─ Day 4-7: 品質検証 & ドキュメント & PR

Week 5 (11/11-11/17): RFC-024 Phase 4 - Integration
├─ Day 1-3: ContextManager & CompressionPolicy
├─ Day 4-5: MemoryManager統合 & @agent統合
└─ Day 6-7: 統合テスト（30+ tests）& 最終ドキュメント & PR

Week 6 (11/18-11/24): v2.5.0 リリース準備
└─ 全テスト実行、CI確認、リリースノート作成、デプロイ
```

---

## 🚀 v2.5.0 以降の展望

### v2.6.0: Full Ecosystem（2-3ヶ月後）

- RFC-008 Phase 2: Plugin Marketplace（コミュニティ統合）
- RFC-009 Phase 2: Multi-Agent Teams（高度なオーケストレーション）
- RFC-003: Personal Assistant（学習・適応）

### v2.7.0: API Server & Web UI（4-5ヶ月後）

- RFC-015: Agent API Server（REST/WebSocket）
- Web UI（Agent Builder、Executor、Dashboard）
- JavaScript SDK

### v2.8.0+: Advanced Features（6ヶ月以降）

- RFC-004: Voice Interface
- RFC-006 Phase 2: LSP Integration
- RFC-010: Advanced Observability
- RFC-011: Scheduled Automation

---

## ❓ よくある質問（改訂版）

### Q1: なぜContext Compressionを最優先に？

A: LangChain Context Engineering分析の結果、これがないとProduction環境で使用不可能であることが判明しました。長時間会話で必ずコンテキストリミットに達し、Personal Assistant（RFC-003）実装も不可能です。

### Q2: Meta Agent Phase 3（Self-Improving）はいつ？

A: RFC-024完了後（Week 6以降）に実装予定です。または v2.6.0 に延期する可能性もあります。

### Q3: なぜ5週間もかかる？

A: Context Compressionは4つのフェーズ（Token Management, Trimming, Summarization, Integration）から成り、LLMベースの要約実装と品質検証に時間を要します。

### Q4: エコシステム（RFC-008/009）はいつ？

A: v2.6.0以降で実装予定です。RFC-024が最優先のため、スケジュール調整しました。

### Q5: 他のRFC（RFC-003/010/011）は？

A: v2.6.0以降で順次実装予定です。特にRFC-010（Observability）はRFC-024後に優先度が上がります。

---

## 📚 関連ドキュメント

### 新規作成（2025-10-14）
- [CONTEXT_ENGINEERING_ANALYSIS.md](./CONTEXT_ENGINEERING_ANALYSIS.md) - Context Engineering分析レポート
- [RFC_024_CONTEXT_COMPRESSION.md](./rfcs/RFC_024_CONTEXT_COMPRESSION.md) - RFC-024仕様書
- [RFC_024_PHASE1_PLAN.md](./rfcs/RFC_024_PHASE1_PLAN.md) - Phase 1実装計画

### 既存ドキュメント
- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 全体ロードマップ
- [NEXT_STEPS.md](./NEXT_STEPS.md) - 現在の状況
- [RFC_005_META_AGENT.md](./rfcs/RFC_005_META_AGENT.md) - Meta Agent仕様
- [RFC_005_PHASE1_PLAN.md](./rfcs/RFC_005_PHASE1_PLAN.md) - Meta Agent Phase 1計画
- [RFC_005_PHASE2_PLAN.md](./rfcs/RFC_005_PHASE2_PLAN.md) - Meta Agent Phase 2計画

---

**🚨 重要: v2.5.0はRFC-024 Context Compressionを最優先で実装します！Production-readyなフレームワークを目指しましょう 🚀**
