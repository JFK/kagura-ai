# リファクタリング候補分析（v2.2.0）

## 📊 コード規模分析

### Top 10 最大ファイル
1. `observability/dashboard.py` - 469行
2. `routing/router.py` - 410行
3. `core/decorators.py` - 396行
4. `cli/repl.py` - 343行
5. `chat/session.py` - 339行
6. `observability/store.py` - 334行
7. `testing/testcase.py` - 324行
8. `core/memory/manager.py` - 321行
9. `commands/hooks.py` - 276行
10. `builder/agent_builder.py` - 265行

## 🔍 リファクタリング推奨度

### ✅ 現状維持（問題なし）
以下のファイルは適切な規模で、明確な責務分離されている：
- `dashboard.py` (469行) - 複数の表示メソッド、役割明確
- `testcase.py` (324行) - 多数のアサーションメソッド、適切
- `decorators.py` (396行) - 3つのデコレータ、適切分離
- `agent_builder.py` (265行) - Builderパターン、適切

### ⚠️ 要注意（将来的に分割検討）
- `router.py` (410行) - 複数のルーティング戦略
  - 提案: Intent/Semantic/Keywordを別ファイルに分離
- `session.py` (339行) - チャットセッション管理
  - 提案: MessageHandler/SessionStorage分離
- `executor.py` (260行) - コード実行エンジン
  - 現状OK、将来的に拡張されたら分割

### 🔥 優先改善候補

#### 1. **router.py の分離**
**現状**: 1ファイルに3つのルーティング戦略
**推奨**:
```
routing/
  ├── router.py (Base)
  ├── intent_router.py
  ├── semantic_router.py
  └── keyword_router.py
```
**理由**: 各戦略が独立しており、テスト・保守が容易に

#### 2. **monitor.py CLI コマンド分離**
**現状**: 238行に5つのCLIコマンド
**推奨**:
```
cli/monitor/
  ├── __init__.py
  ├── live.py
  ├── list.py
  ├── stats.py
  ├── trace.py
  └── cost.py
```
**理由**: 各コマンドが独立、保守性向上

## 📝 コーディング標準改善案

### 1. 型ヒント一貫性
現状: ほぼ全てに型ヒントあり ✅
改善: `Optional[X]` vs `X | None` の統一（現在は混在）

### 2. Docstring一貫性
現状: ほぼ全てにdocstringあり ✅
改善: Examples追加（特に新機能）

### 3. エラーメッセージの一貫性
現状: 統一されている ✅
改善: 特になし

## 🎯 次回リリース（v2.3.0）での改善提案

1. **router.py分離** - 優先度: Medium
   - 期間: 半日
   - 利点: テスト容易性、保守性向上

2. **統合テストのCI追加** - 優先度: High
   - 期間: 1日
   - 利点: エンドツーエンド品質保証

3. **examples/更新** - 優先度: High
   - 期間: 1日
   - 利点: ユーザー体験向上

## ✅ 結論

**v2.2.0のコード品質**: 良好 ✅

- 適切な規模のファイル分割
- 一貫した命名規則
- 包括的なテストカバレッジ（586+ tests）
- 型ヒント完備

**即座にリファクタリングが必要な箇所**: なし

**将来的な改善**: router.py分離、monitor CLI分離（v2.3.0以降で検討）

---

**生成日**: 2025-10-10
**分析対象**: Kagura AI v2.2.0
