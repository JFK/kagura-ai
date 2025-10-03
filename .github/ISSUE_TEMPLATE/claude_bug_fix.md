---
name: Claude Code - Bug Fix Task
about: Claude Codeでバグを修正するタスク
title: '[BUG-FIX] '
labels: bug, claude-code
assignees: ''
---

## 🐛 問題の説明


## 📂 影響範囲
**ファイル/ディレクトリ**:


**再現手順**:
1.
2.
3.

**期待される動作**:


**実際の動作**:


## 📑 出力契約(Claude必読)
- すべてMarkdownで出力
- 修正理由・影響範囲を明記
- テストケース追加の有無を報告
- エラー時は停止して質問

## 📂 スコープ境界
**許可パス**:


**禁止パス**:
- `src/kagura/core/**` (コア機能への変更は要相談)
- `pyproject.toml` (依存関係変更は要承認)

## 🛡️ 安全弁
- **Draft PR**で作成
- 重大なバグの場合は`--dry-run`で影響確認
- 修正がコア機能に及ぶ場合は先に報告

## 📋 Claude Code用タスク定義

### 環境準備
1. このイシューからブランチ`fix/[issue-number]-[bug-name]`を作成
2. イシューステータスを「In Progress」に変更

### 調査・修正
3. 関連コードの分析と根本原因の特定
4. 根本原因を`ai_docs/fixes/[issue-number]-analysis.md`に記録
5. バグ修正の実装
6. 同様の問題が他にないか確認
7. 修正内容を`ai_docs/fixes/[issue-number]-solution.md`に記録

### テスト
8. バグを再現するテストケースを追加 (`tests/`配下)
9. 修正後にテストが成功することを確認
10. 既存テストが全てパスすることを確認 (`make test`)

### 完了処理
11. 作業ログをイシューに記録
12. **Draft** PRを作成

## 🧾 コミット規約

```
fix(<scope>): <subject> (#issue-number)
```

**scope**: 変更モジュール名 (例: `agent`, `config`, `memory`)
**subject**: バグの内容を簡潔に (50文字以内)

例:
```
fix(agent): prevent null pointer in state validation (#456)
test(agent): add test case for null state handling (#456)
docs(fixes): document root cause and solution (#456)
```

## ⚠️ 注意事項
- [ ] 修正により他の機能に影響がないか確認
- [ ] テストケース追加を検討
- [ ] `ai_docs/coding_standards.md`に従う
- [ ] `ai_docs/architecture.md`の設計原則を遵守
- [ ] 不明点があれば作業前に質問

## 📚 参考資料
<!-- エラーログ、スタックトレース、関連ドキュメントなど -->


## ✅ 完了条件
- [ ] **CI(lint/test)がグリーン**
- [ ] バグが修正され動作確認済み
- [ ] テストケース追加済み
- [ ] 根本原因と解決策をドキュメント化
- [ ] 作業ログ記録済み
- [ ] Draft PRレビュー依頼済み
