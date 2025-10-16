# RFC-036: Codebase Redundancy Review & Consolidation

**ステータス**: Draft
**作成日**: 2025-10-16
**優先度**: ⭐️⭐️ Medium
**対象バージョン**: v2.6.0+
**関連Issue**: [#227](https://github.com/JFK/kagura-ai/issues/227)

---

## 📋 概要

Kagura AIコードベース全体を調査し、冗長な仕組み、重複実装、統合可能な機能を特定して整理します。

---

## 🎯 目標

### 問題

v2.5.10に到達し、多くの機能が追加されたが、以下の懸念：

1. **重複実装**: 似た機能が複数箇所に存在
2. **冗長な抽象化**: 不要なラッパーやレイヤー
3. **未使用コード**: 削除可能な機能
4. **一貫性の欠如**: 似た処理の実装方法がバラバラ

### ゴール

- ✅ コードベース簡素化
- ✅ メンテナンス性向上
- ✅ パフォーマンス改善
- ✅ 一貫性確保

---

## 🔍 調査対象領域

### 1. メモリ・RAGシステム

**現在の実装**:
```
src/kagura/core/memory/
├── manager.py          # MemoryManager
├── rag.py              # MemoryRAG (ChromaDB)
├── multimodal_rag.py   # MultimodalRAG
├── persistent.py       # PersistentMemory
└── context.py          # ContextManager
```

**調査ポイント**:
- MemoryRAG vs MultimodalRAG: 統合可能？
- PersistentMemory: 必要性は？
- ContextManager: MemoryManagerと重複？

### 2. ルーティングシステム

**現在の実装**:
```
src/kagura/routing/
├── router.py               # AgentRouter
├── memory_aware_router.py  # MemoryAwareRouter
└── context_analyzer.py     # ContextAnalyzer
```

**調査ポイント**:
- AgentRouter vs MemoryAwareRouter: 統合可能？
- ContextAnalyzer: 必要性は？

### 3. ツールシステム

**現在の実装**:
```
src/kagura/tools/        # YouTube等
src/kagura/builtin/      # File operations
src/kagura/web/          # Web search/scraper
```

**調査ポイント**:
- tools/ vs builtin/: 統合可能？
- 一貫性は？

### 4. プリセット vs テンプレート

**現在の実装**:
```
src/kagura/presets/        # Pre-built agents
src/kagura/chat/preset.py  # Chat presets
src/kagura/meta/templates/ # Meta agent templates
```

**調査ポイント**:
- 重複？統合可能？

---

## 📦 調査Phase

### Phase 1: 使用状況分析（1週間）

**方法**:
```bash
# Import分析
rg "^from kagura\." --type py | cut -d: -f2 | sort | uniq -c | sort -rn

# 未使用コード検出
vulture src/kagura/

# Git log分析
git log --all --pretty=format:'%h' --name-only |   grep "src/kagura/" | sort | uniq -c | sort -rn
```

**成果物**:
- 使用頻度レポート
- 未使用コードリスト
- 削除候補リスト

### Phase 2: 依存関係分析（3日）

**方法**:
```bash
# モジュール依存グラフ
pydeps src/kagura/ --max-bacon 3

# Circular dependencies検出
pydeps src/kagura/ --show-cycles
```

**成果物**:
- 依存関係図
- Circular dependency報告
- 統合候補リスト

### Phase 3: リファクタリング計画（2日）

**成果物**:
- 統合計画ドキュメント
- 優先順位付け
- 実装ロードマップ

### Phase 4: 実装（2-4週間）

- Phaseごとに分割実装
- 後方互換性維持
- 段階的移行

---

## 📊 期待される成果

### 短期効果
- ✅ 削除可能コード特定
- ✅ 統合候補リスト
- ✅ リファクタリング計画

### 中期効果
- ✅ コードベース10-20%削減
- ✅ Import時間短縮
- ✅ メンテナンス性向上

### 長期効果
- ✅ 新機能追加が容易に
- ✅ バグ発生率低下
- ✅ ドキュメント整理

---

## 🔒 制約

### 変更禁止
- ❌ 公開API（Breaking change禁止）
- ❌ 既存のagent定義
- ❌ examples/（Phase 4まで）

### 慎重に扱うべき
- ⚠️ Memory system（多くの機能が依存）
- ⚠️ LLM integration（コア機能）
- ⚠️ Tool system（拡張性重要）

---

## 📅 スケジュール

**Duration**: 4-6週間

- Week 1: Phase 1（使用状況分析）
- Week 2: Phase 2（依存関係分析）
- Week 3: Phase 3（計画策定）
- Week 4-6: Phase 4（実装）

**Target**: v2.6.0+

---

## ✅ 成功指標

- ✅ 冗長性レポート作成
- ✅ 統合計画作成
- ✅ 優先順位付け
- ✅ 実装ロードマップ
- ✅ コードベース10-20%削減
- ✅ 後方互換性維持

---

## 🔗 関連

- **Issue #227**: このRFC
- **Issue #249**: CLI簡素化（完了 - 11,000行削減の実績）

---

**Status**: Draft - 調査フェーズ
**このRFCは品質向上とメンテナンス性改善のための重要な取り組みです。**
