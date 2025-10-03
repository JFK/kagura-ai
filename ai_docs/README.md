# AI Docs

このディレクトリは、Claude Codeがタスクを実行する際に参照するドキュメントを格納します。

## 📂 ディレクトリ構成

```
ai_docs/
├── README.md                # このファイル
├── architecture.md         # システムアーキテクチャ概要
├── coding_standards.md     # コーディング規約
├── glossary.md            # 用語集・略語集
├── DEVELOPMENT_ROADMAP.md # 開発ロードマップ
├── NEXT_STEPS.md          # 次の開発ステップ
├── analysis/              # 調査レポート
├── suggestions/           # Claudeからの技術的提案
└── fixes/                 # バグ修正の詳細記録
```

## 🚨 Claude Code必読ルール

### 作業前の確認
- [ ] このREADME.mdを読む
- [ ] `DEVELOPMENT_ROADMAP.md`で現在のPhaseを確認
- [ ] `architecture.md`でシステム構造を把握
- [ ] `coding_standards.md`のルールを確認
- [ ] `glossary.md`で用語を確認

### 作業中の原則
- すべての変更は**Draft PR**で作成
- 不明点があれば**必ず質問**して停止(推測で進めない)
- コミットは**Conventional Commits**形式
- 10ファイル/500行超える場合は分割コミット

### 禁止事項(NEVER)
- ❌ 推測での実装 (不明点は必ず質問)
- ❌ mainブランチへの直接コミット
- ❌ テストなしでのコード変更

## 📋 コミットメッセージ形式

```
<type>(<scope>): <subject> (#issue-number)

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `chore`: ビルド、設定変更

### 例
```
feat(core): implement @agent decorator (#20)
fix(executor): prevent import bypass (#21)
test(cli): add REPL command tests (#27)
```

## 🎯 作業完了時のチェックリスト
- [ ] 型チェック (pyright) がパス
- [ ] 全テストがパス
- [ ] Draft PR作成
- [ ] Issueにコメントで進捗報告

## 📝 ファイル命名規則

Issue番号を含むファイル名で管理:

- `analysis/123-feature-investigation.md`
- `suggestions/456-performance-optimization.md`
- `fixes/789-auth-bug-fix.md`

## 🔄 更新ルール

1. **新しい知見は積極的にドキュメント化**
   - Claude Codeが発見した問題点
   - 技術的な推奨事項
   - アーキテクチャ上の決定

2. **定期的なレビュー**
   - 古い情報を見直し
   - 非推奨となった情報は削除または更新

3. **具体例を含める**
   - 抽象的な説明だけでなく、コード例を含める
   - 良い例・悪い例を明示

## 参考リンク

- [Issue-Driven AI Development実践ガイド](https://qiita.com/kiyotaman/items/87a5a9ddc88db64f78ac)
- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
