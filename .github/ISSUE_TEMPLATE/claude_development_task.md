---
name: Claude Code - Development Task
about: Claude Codeで実装する汎用的な開発タスク
title: '[DEV] '
labels: development, claude-code
assignees: ''
---

## 🎯 目的・背景


## 📑 出力契約(Claude必読)
- 実装の設計判断を記録
- 未解決の技術的負債を明示
- エラー/不明点は質問節で停止

## 📂 スコープ境界
**許可パス**:


**禁止パス**:
- `src/kagura/core/**` (コア機能への変更は要相談)
- `pyproject.toml` (依存関係追加は要承認)
- `.github/workflows/**` (CI変更は要承認)

## 🛡️ 安全弁
- **Draft PR**で作成
- 10ファイル/500行超える場合は分割コミット
- 新しい依存関係追加は事前報告

## 📋 Claude Code用タスク定義

### 準備
1. ブランチ`feature/[issue-number]-[feature-name]`を作成
2. イシューステータスを「In Progress」に変更

### 実装
3. [具体的なタスクを記載]


### テスト
4. ユニットテスト作成 (`tests/`配下)
5. テストカバレッジ80%以上を確保
6. 既存テストが全てパス (`make test`)

### ドキュメント・完了処理
7. 必要に応じて`ai_docs/`にドキュメント作成
8. 実装の設計判断を`ai_docs/suggestions/[issue-number]-design.md`に記録
9. 作業ログをイシューに記録
10. **Draft** PRを作成

## 🧾 コミット規約

```
<type>(<scope>): <subject> (#issue-number)
```

**type**: `feat` (新機能), `refactor` (リファクタリング), `test` (テスト), `docs` (ドキュメント)
**scope**: 変更モジュール名
**subject**: 変更内容を簡潔に (50文字以内)

例:
```
feat(cli): add new command for agent generation (#789)
test(cli): add tests for agent generation command (#789)
docs(cli): update CLI documentation (#789)
```

## ⚠️ 制約・注意事項
- [ ] `ai_docs/coding_standards.md`のルールに従う
- [ ] `ai_docs/architecture.md`の設計原則を遵守
- [ ] `ai_docs/glossary.md`の用語定義を使用
- [ ] 型ヒントを必ず付ける (`Any`型の乱用禁止)
- [ ] Pydanticモデルで型安全性を確保
- [ ] ロギングに`logging`を使用 (`print()`禁止)
- [ ] 不明点は作業前に質問

## 📚 参考資料
<!-- 関連Issue、設計ドキュメント、外部リンクなど -->


## ✅ 完了条件
- [ ] **CI(lint/test/build)がグリーン**
- [ ] 実装完了
- [ ] 動作確認済み
- [ ] テストカバレッジ80%以上
- [ ] 型チェックがパス (`make right`)
- [ ] ドキュメント更新済み
- [ ] 作業ログ記録済み
- [ ] Draft PRレビュー依頼済み
