---
name: Claude Code - Migration Task
about: コード移行・バージョンアップグレードタスク (Claude Code用)
title: '[MIGRATE] '
labels: migration, claude-code
assignees: ''
---

## 🎯 目的


## 📂 対象
**ディレクトリ/ファイル**:


**移行元→移行先**:


**対象ファイル拡張子**:


## 📑 出力契約(Claude必読)
- すべてMarkdownで出力
- 各ステップ終了時に「作業ログ」節を追記(差分要約・ファイル数・既知リスク)
- エラー/不明点は「質問」節で列挙し停止(自己判断で進めない)

## 📂 スコープ境界
**許可パス**:


**禁止パス**:
- `src/kagura/core/**` (コア機能は慎重に)
- `pyproject.toml` (依存関係変更は要承認)
- `.github/workflows/**` (CI設定は要承認)

※ 上記以外に変更が必要な場合はこのIssueで要承認

## 🛡️ 安全弁
- すべて**Draft PR**で作成すること
- 10ファイル/500行を超える変更は分割コミット(理由をログに記載)
- 重大変更はまず`--dry-run`レポートを提出 → 承認後に実施

## 📋 Claude Code用タスク定義

### 環境準備
1. このイシューからリモートブランチを作成
2. ブランチ名: `migrate/[issue-number]-[directory-name]`
3. このイシューとブランチを紐づけ
4. イシューステータスを「In Progress」に変更

### 実装タスク
5. 対象ディレクトリ配下のコード移行を実施
6. 上記で指定した拡張子のファイルを対象とする
7. 潜在的なバグ・非推奨機能の検出と修正
8. 変更は段階的にコミット(コミット規約に従う)

### 完了処理
9. 移行に関する技術的な推奨事項があれば`ai_docs/suggestions/[issue-number]-*.md`に記録
10. 作業ログをこのイシューに記録(変更ファイル数、主な変更内容、発見した問題点)
11. **Draft** プルリクエストを作成

## 🧾 コミット規約

```
<type>(<scope>): <subject> (#issue-number)
```

**type**: `refactor`, `fix`, `chore`, `docs`, `test`
**scope**: 変更モジュール名 (例: `core`, `cli`, `agents`)
**subject**: 変更内容を簡潔に (50文字以内)

例:
```
refactor(agents): migrate to pydantic v2 models (#123)
fix(core): handle deprecated yaml.load warning (#123)
test(agents): update tests for new agent structure (#123)
```

## ⚠️ 制約・注意事項
- [ ] 移行が主目的。過度なリファクタリングは避ける
- [ ] 既存の動作を壊さない
- [ ] `ai_docs/coding_standards.md`のルールに従う
- [ ] `ai_docs/migration_guide.md`を参照
- [ ] `ai_docs/architecture.md`の設計原則を遵守
- [ ] 不明点は作業前にコメントで確認

## 📚 参考資料


## ✅ 完了条件
- [ ] **CI(lint/test/build)が全てグリーン**
- [ ] 対象ディレクトリのコードが移行完了
- [ ] 既存機能が正常動作 (`make test`が成功)
- [ ] 型チェックがパス (`make right`が成功)
- [ ] 主要リスク・除外項目をPR説明に明記
- [ ] 作業ログ記録済み
- [ ] Draft PRレビュー依頼済み
