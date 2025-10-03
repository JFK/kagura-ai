# AI Docs - Claude Codeへの指示

このディレクトリは、Claude Codeがタスクを実行する際に**必ず参照**すべきドキュメントです。

## 🚨 必須ルール(MUST)

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
- テストカバレッジ90%+を維持

### 禁止事項(NEVER)
- ❌ `src/kagura_legacy/`配下の変更
- ❌ `tests/*_legacy/`配下の変更
- ❌ `examples/`の変更 (Phase 4まで待機)
- ❌ `docs/`の変更 (Phase 4まで待機)
- ❌ 推測での実装 (不明点は必ず質問)

## 目的

Claude Codeに対してプロジェクト固有の文脈、設計思想、コーディング規約を提供し、高品質な作業結果を得るためのナレッジベースです。

## ディレクトリ構成

```
ai_docs/
├── README.md                 # このファイル
├── architecture.md          # システムアーキテクチャ概要
├── coding_standards.md      # コーディング規約
├── glossary.md             # 用語集・略語集
├── migration_guide.md      # バージョン移行ガイドライン
├── analysis/               # 調査レポート
├── suggestions/            # Claude Codeからの技術的提案
└── fixes/                  # バグ修正の詳細記録
```

## ファイル命名規則

Issue番号を含むファイル名で管理します:

- `analysis/123-feature-investigation.md`
- `suggestions/456-performance-optimization.md`
- `fixes/789-auth-bug-fix.md`

## 更新ルール

1. **新しい知見は積極的にドキュメント化**
   - Claude Codeが発見した問題点
   - 技術的な推奨事項
   - アーキテクチャ上の決定

2. **定期的なレビュー**
   - 四半期ごとに古い情報を見直し
   - 非推奨となった情報は削除または更新

3. **具体例を含める**
   - 抽象的な説明だけでなく、コード例を含める
   - 良い例・悪い例を明示

## 📋 Issue-Driven開発フロー

### 1. Issue確認
1. Issueの内容を完全に理解
2. スコープ境界を確認
3. 完了条件を確認
4. 関連ドキュメント（ai_docs/）を参照

### 2. 実装
1. Feature branchを作成: `feature/PHASE-XXX-description`
2. テストを先に書く (TDD)
3. 実装
4. 型チェック (pyright)
5. テスト実行 (pytest)

### 3. Draft PR作成
- タイトル: `<type>(<scope>): <subject> - PHASE-XXX`
- 必ず**Draft**で作成
- Summary、Changes、Test Resultsを記載
- Issueリンク: `Closes #XXX`

### 4. CI確認・マージ
- 全テストがパス
- Pyright型チェックがパス
- Codecov警告がないこと
- レビュー後にマージ

## 📝 コミットメッセージ形式

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
- [ ] テストカバレッジ90%+
- [ ] 全テストがパス
- [ ] Draft PR作成
- [ ] Issueにコメントで進捗報告

## Claude Codeへの指示

Issue Templateで以下のように参照させます:

```markdown
## ⚠️ 制約・注意事項
- [ ] `ai_docs/coding_standards.md`のルールに従う
- [ ] `ai_docs/architecture.md`の設計原則を遵守
- [ ] `ai_docs/glossary.md`の用語定義を使用
```

## 機密情報の取り扱い

- APIキーや認証情報は含めない
- 機密性の高いビジネスロジックは抽象化して記載
- 必要に応じて`.gitignore`で除外

## 参考リンク

- [Issue-Driven AI Development実践ガイド](https://qiita.com/kiyotaman/items/87a5a9ddc88db64f78ac)
- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
