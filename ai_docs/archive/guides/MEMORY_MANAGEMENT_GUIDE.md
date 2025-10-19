# Memory Management Guide - MCP メモリー管理ガイド

**最終更新**: 2025-10-04
**対象**: Kagura AI 開発プロジェクト
**関連**: MCP_SETUP_GUIDE.md

---

## 📖 目次

1. [メモリーサーバーの仕組み](#メモリーサーバーの仕組み)
2. [ai_docsで保存すべき重要な内容](#ai_docsで保存すべき重要な内容)
3. [メモリーの確認方法](#メモリーの確認方法)
4. [開発中のメモリー活用](#開発中のメモリー活用)
5. [実践例](#実践例)

---

## メモリーサーバーの仕組み

### データベース実装

**ストレージ**: JSON ファイルベース

- **デフォルトパス**: `memory.json` (カレントディレクトリ)
- **設定**: 環境変数 `MEMORY_FILE_PATH` で変更可能
- **形式**: ナレッジグラフ（Knowledge Graph）

### データ構造

メモリーは3つの要素で構成されます：

```json
{
  "entities": [
    {
      "name": "Kagura_AI_Project",
      "entityType": "project",
      "observations": [
        "Current version: v2.0.0-beta.1",
        "Main branch: main",
        "Python version: 3.11+"
      ]
    }
  ],
  "relations": [
    {
      "from": "Kagura_AI_Project",
      "to": "MCP_Integration",
      "relationType": "implements"
    }
  ]
}
```

#### 1. **Entities** (エンティティ)
- **name**: 一意の名前
- **entityType**: タイプ（project, feature, issue, rfc, etc.）
- **observations**: 観察・事実のリスト

#### 2. **Relations** (関係)
- **from**: 開始エンティティ
- **to**: 終了エンティティ
- **relationType**: 関係のタイプ

#### 3. **Observations** (観察)
- エンティティに紐づく個別の事実

### ストレージパスの設定

```json
// ~/.claude.json の設定
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/home/jfk/.claude/memory/kagura-ai-memory.json"
      }
    }
  }
}
```

---

## ai_docsで保存すべき重要な内容

### 1. プロジェクト基本情報

**保存内容**:
```
Entity: Kagura_AI_Project
Type: project
Observations:
- プロジェクト名: Kagura AI 2.0
- 目的: Python関数を1行のデコレータでAIエージェントに変換
- リポジトリ: /home/jfk/works/kagura-ai
- 現在バージョン: v2.0.0-beta.1
- メインブランチ: main
- Python要件: 3.11+
```

**Claude での保存方法**:
```
User: 以下をメモリーに保存して：
- プロジェクト名: Kagura AI 2.0
- 目的: Python関数を1行のデコレータでAIエージェントに変換
- 現在バージョン: v2.0.0-beta.1
- メインブランチ: main
- Python要件: 3.11+

Claude: [memory_create_entities を実行]
保存しました！
```

### 2. 開発フェーズと優先度

**保存内容**:
```
Entity: Current_Development_Phase
Type: phase
Observations:
- 現在のフェーズ: v2.0.0 正式版リリース準備
- 進行中Issue: #72 (REPL改善)
- 次のフェーズ: v2.1.0 (MCP Integration)

Entity: RFC_Priorities
Type: roadmap
Observations:
- Very High: RFC-007 (MCP Integration) - Issue #67
- High: RFC-006 (Live Coding Chat REPL) - Issue #66
- High: RFC-012 (Commands & Hooks) - Issue #73
- High: RFC-014 (Web Integration) - Issue #75
```

### 3. コーディング規約

**保存内容**:
```
Entity: Coding_Standards
Type: standards
Observations:
- 命名規則: snake_case (モジュール/関数), PascalCase (クラス)
- 型ヒント: 必須（pyright --strict 準拠）
- テストカバレッジ: 全体90%+, コア95%+
- コミット形式: Conventional Commits
- ブランチ形式: feature/PHASE-XXX-description
```

### 4. 重要なディレクトリ構造

**保存内容**:
```
Entity: Directory_Structure
Type: structure
Observations:
- 変更可能: src/kagura/, tests/, ai_docs/
- 変更禁止: src/kagura_legacy/, examples/, docs/, LICENSE
- 開発ドキュメント: ai_docs/ (README, UNIFIED_ROADMAP, NEXT_STEPS, coding_standards)
- RFC: ai_docs/rfcs/RFC_*.md
- 設定: pyproject.toml
```

### 5. よく使うコマンド

**保存内容**:
```
Entity: Common_Commands
Type: commands
Observations:
- テスト実行: pytest --cov=src/kagura --cov-report=html
- 型チェック: pyright src/kagura/
- リント: ruff check src/
- フォーマット: ruff format src/
- REPL起動: kagura repl
- ビルド: uv build
- 並列テスト: pytest -n auto
```

### 6. 開発ワークフロー

**保存内容**:
```
Entity: Development_Workflow
Type: workflow
Observations:
- Phase 0: ai_docs 確認 (README, UNIFIED_ROADMAP, NEXT_STEPS, coding_standards)
- Phase 1: feature/PHASE-XXX-description ブランチ作成
- Phase 2: TDD (テスト → 実装 → パス確認)
- Phase 3: Draft PR作成 (gh pr create --draft)
- Phase 4: CI確認 (テスト, pyright, ruff, codecov)
- Phase 5: Ready for review → Squash merge
```

### 7. 禁止事項

**保存内容**:
```
Entity: Development_Restrictions
Type: restrictions
Observations:
- レガシーコード変更禁止: src/kagura_legacy/, tests/*_legacy/
- Phase 4まで変更禁止: examples/, docs/
- 変更厳禁: LICENSE, CODE_OF_CONDUCT.md, .env*
- 推測での進行禁止: エラー時は Issue にコメント報告
```

---

## メモリーの確認方法

### 方法1: Claude Code で直接確認

```
User: メモリーに保存されている情報を全て表示して

Claude: [read_graph を実行]

保存されている情報:

【エンティティ】
1. Kagura_AI_Project (project)
   - 現在バージョン: v2.0.0-beta.1
   - メインブランチ: main
   - Python要件: 3.11+

2. Current_Development_Phase (phase)
   - 現在のフェーズ: v2.0.0 正式版リリース準備
   - 進行中Issue: #72
   ...
```

### 方法2: 特定の情報を検索

```
User: RFCの優先度について教えて

Claude: [search_nodes でクエリ: "RFC priority"]

RFC優先度:
- Very High: RFC-007 (MCP Integration)
- High: RFC-006, RFC-012, RFC-014
```

### 方法3: JSON ファイルを直接確認

```bash
# デフォルトの場合（カレントディレクトリ）
cat memory.json | jq .

# カスタムパスの場合
cat ~/.claude/memory/kagura-ai-memory.json | jq .

# エンティティのみ表示
cat memory.json | jq '.entities'

# 特定エンティティの検索
cat memory.json | jq '.entities[] | select(.name == "Kagura_AI_Project")'
```

### 方法4: 開発中にメモリー内容を定期確認

```
User: 現在のプロジェクト状況をメモリーから確認して

Claude: [open_nodes で "Kagura_AI_Project", "Current_Development_Phase" を取得]

現在の状況:
- バージョン: v2.0.0-beta.1
- 進行中: Issue #72 (REPL改善)
- 次のフェーズ: v2.1.0 MCP Integration
```

---

## 開発中のメモリー活用

### ユースケース1: 新しいIssue着手時

**開始時**:
```
User: Issue #72 の作業を開始します。関連する情報をメモリーから教えて

Claude: [search_nodes でクエリ: "Issue #72 REPL"]

Issue #72: REPL改善
- タスク: prompt_toolkit統合
- 完了条件:
  1. >>> プロンプトがバックスペースで削除不可
  2. 複数行コード貼り付けが正常動作
  3. 履歴が Ctrl+R で検索可能
- 見積もり: 2-3日
```

**完了時**:
```
User: Issue #72 を完了しました。メモリーを更新して

Claude: [create_entities と add_observations を実行]

メモリーを更新しました：
- Current_Development_Phase → "v2.0.0 リリース準備完了"
- Issue #72 → "completed"
- Next Action → "v2.0.0 正式版リリース"
```

### ユースケース2: コーディング規約の確認

```
User: コミットメッセージの形式は？

Claude: [open_nodes で "Coding_Standards"]

コミットメッセージ形式（Conventional Commits）:
<type>(<scope>): <subject> (#issue-number)

例:
- feat(core): implement @agent decorator (#20)
- fix(executor): prevent import bypass (#21)
- test(cli): add REPL command tests (#27)
```

### ユースケース3: エラー対応時

```
User: テストが失敗しました。対応フローを教えて

Claude: [search_nodes でクエリ: "error handling workflow"]

エラー発生時の対応フロー:
1. エラー内容を正確に記録
2. Issue にコメントで報告
3. 人間の指示を待つ（推測で進めない）
4. 解決後に ai_docs/fixes/ に記録
```

### ユースケース4: RFC実装の優先順位確認

```
User: 次に実装すべきRFCは？

Claude: [open_nodes で "RFC_Priorities"]

次の実装優先順位:
1. RFC-007 (Very High): MCP Integration - Issue #67
   - v2.1.0 でリリース予定
   - 見積もり: 6週間

2. RFC-006 (High): Live Coding Chat REPL - Issue #66
   - v2.1.0 で並行実装可能
```

---

## 実践例

### 例1: プロジェクト情報の初期セットアップ

```
User: Kagura AI プロジェクトの基本情報をメモリーに保存してください：
- プロジェクト名: Kagura AI 2.0
- 目的: Python関数を@agentデコレータでAIエージェント化
- リポジトリパス: /home/jfk/works/kagura-ai
- 現在バージョン: v2.0.0-beta.1
- メインブランチ: main
- Python要件: 3.11+
- テストカバレッジ目標: 90%+
- 型チェッカー: pyright --strict

Claude: [create_entities を実行]

✓ メモリーに保存しました！

Entity created: Kagura_AI_Project
- Type: project
- Observations: 8件

これで今後の会話で、プロジェクト情報を参照できます。
```

### 例2: 開発フェーズの更新

```
User: Issue #72 が完了しました。次は v2.0.0 正式版リリースです。メモリーを更新して

Claude: [create_entities と create_relations を実行]

✓ メモリーを更新しました！

【更新内容】
- Entity "Issue_72" を作成
  - Status: completed
  - Completion date: 2025-10-04

- Entity "Current_Development_Phase" を更新
  - Phase: v2.0.0 正式版リリース準備
  - Tasks:
    1. 最終テスト実行
    2. CHANGELOG更新
    3. PyPI公開
    4. GitHub Release作成

- Relation 追加: Issue_72 → v2.0.0 (blocks)
```

### 例3: コーディング規約の確認

```
User: 新しいファイルを作成します。命名規則を教えて

Claude: [search_nodes でクエリ: "naming convention"]

命名規則（ai_docs/coding_standards.md より）:
- モジュール/パッケージ: snake_case (例: kagura.core.agent)
- クラス名: PascalCase (例: AtomicAgent, LLMConfig)
- 関数/変数: snake_case (例: create_agent)
- 定数: UPPER_SNAKE_CASE (例: DEFAULT_MODEL)
- プライベート: _leading_underscore (例: _internal_state)

型ヒントは必須です（pyright --strict 準拠）。
```

### 例4: 禁止事項の確認

```
User: src/kagura_legacy/agent.py を修正してもいいですか？

Claude: [open_nodes で "Development_Restrictions"]

❌ 禁止です！

src/kagura_legacy/ は変更禁止ディレクトリです。
- 理由: レガシーコード（参照のみ）
- 許可: 参照・コピーは可能
- 実装: src/kagura/ に新規実装してください

変更可能なディレクトリ:
- src/kagura/
- tests/
- ai_docs/
```

### 例5: よく使うコマンドの確認

```
User: テストを実行したいです

Claude: [open_nodes で "Common_Commands"]

テスト関連コマンド:

【全テスト実行】
pytest

【カバレッジ付き】
pytest --cov=src/kagura --cov-report=html

【並列実行】
pytest -n auto

【特定モジュール】
pytest tests/core/

【型チェック】
pyright src/kagura/

【リント】
ruff check src/
```

---

## メモリーのバックアップと管理

### バックアップ

```bash
# メモリーファイルのバックアップ
cp memory.json memory.backup.$(date +%Y%m%d).json

# または指定パスの場合
cp ~/.claude/memory/kagura-ai-memory.json \
   ~/.claude/memory/backups/kagura-ai-memory-$(date +%Y%m%d).json
```

### リセット

```bash
# メモリーを完全にリセット
rm memory.json

# または
rm ~/.claude/memory/kagura-ai-memory.json

# Claude を再起動すると、新しいメモリーファイルが作成されます
```

### 複数プロジェクト管理

```json
// プロジェクトごとにメモリーファイルを分ける
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": "/home/jfk/.claude/memory/${PROJECT_NAME}-memory.json"
      }
    }
  }
}
```

---

## トラブルシューティング

### 問題1: メモリーが保存されない

**症状**: 保存したはずの情報が次回の会話で参照できない

**解決方法**:
```bash
# 1. メモリーファイルの存在確認
ls -la memory.json

# 2. ファイルの権限確認
chmod 644 memory.json

# 3. 内容確認
cat memory.json | jq .

# 4. Claude Code を再起動
```

### 問題2: メモリーファイルが見つからない

**症状**: `memory.json` がどこにあるか分からない

**解決方法**:
```bash
# 1. プロジェクトディレクトリを確認
pwd

# 2. カレントディレクトリにあるか確認
ls memory.json

# 3. 環境変数で指定されているか確認
grep MEMORY_FILE_PATH ~/.claude.json

# 4. システム全体を検索
find ~ -name "memory.json" -type f 2>/dev/null
```

### 問題3: メモリーが肥大化

**症状**: `memory.json` が数MBになってパフォーマンスが低下

**解決方法**:
```bash
# 1. ファイルサイズ確認
ls -lh memory.json

# 2. 古い情報を削除（Claude経由で）
User: 30日以上前の古い情報を削除して

# 3. または手動で編集
jq 'del(.entities[] | select(.name | startswith("old_")))' memory.json > memory.tmp.json
mv memory.tmp.json memory.json
```

---

## ベストプラクティス

### 1. プロジェクト開始時に基本情報を保存

```
User: 以下をメモリーに保存：
- プロジェクト名
- 目的
- 重要なパス
- コーディング規約
- 禁止事項
```

### 2. Issue 着手時に関連情報を確認

```
User: Issue #XX について、メモリーから関連情報を教えて
```

### 3. 定期的にメモリーを更新

```
User: 現在のフェーズが完了しました。メモリーを更新して次のフェーズ情報を追加して
```

### 4. エラー対応履歴を蓄積

```
User: 今回のエラーと解決方法をメモリーに保存して
```

### 5. メモリーのレビュー

```
User: 保存されている情報を確認して、不要な情報を削除して
```

---

## まとめ

### メモリーに保存すべき ai_docs の内容

1. ✅ **プロジェクト基本情報** (名前, 目的, バージョン, パス)
2. ✅ **開発フェーズと優先度** (現在地, RFC優先順位)
3. ✅ **コーディング規約** (命名規則, 型ヒント, テスト要件)
4. ✅ **ディレクトリ構造** (変更可能/禁止ディレクトリ)
5. ✅ **よく使うコマンド** (テスト, 型チェック, リント)
6. ✅ **開発ワークフロー** (Phase 0-5)
7. ✅ **禁止事項** (レガシーコード変更禁止等)

### メモリーの確認方法

1. **Claude 経由**: "メモリーから〜を教えて"
2. **直接確認**: `cat memory.json | jq .`
3. **検索**: Claude の `search_nodes` ツール
4. **特定情報**: Claude の `open_nodes` ツール

### DBの実装

- **形式**: JSON ファイル
- **デフォルトパス**: `memory.json`
- **カスタム設定**: 環境変数 `MEMORY_FILE_PATH`
- **構造**: Knowledge Graph (Entities + Relations + Observations)

---

## 参考リンク

- [MCP_SETUP_GUIDE.md](./MCP_SETUP_GUIDE.md) - MCP設定ガイド
- [UNIFIED_ROADMAP.md](./UNIFIED_ROADMAP.md) - 開発ロードマップ
- [NEXT_STEPS.md](./NEXT_STEPS.md) - 次のアクション
- [coding_standards.md](./coding_standards.md) - コーディング規約
- [MCP Memory Server GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/memory)

---

## 改訂履歴

- **2025-10-04**: 初版作成
  - メモリーサーバーの仕組み解説
  - ai_docs保存推奨項目リストアップ
  - メモリー確認方法の説明
  - 開発中の活用方法
  - 実践例の追加
