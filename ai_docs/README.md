# AI Docs

このディレクトリは、Claude Codeがタスクを実行する際に参照するドキュメントを格納します。

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
