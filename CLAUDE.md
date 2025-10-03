# Claude Code Instructions

このファイルは、Claude Codeが常に参照する指示書です。

## 開始前の必須確認

1. **ai_docs/README.md**を読む
2. **対象Issueの内容**を完全に理解する
3. **ai_docs/DEVELOPMENT_ROADMAP.md**で現在のPhaseを確認
4. **ai_docs/coding_standards.md**でコーディング規約を確認

## 作業の基本方針

- **安全第一**: 不明点は推測せず質問
- **段階的**: 大きな変更は分割
- **可視化**: 作業ログを必ず記録
- **Draft PR**: 全ての変更はDraft PRで作成
- **テスト駆動**: 実装前にテストを書く（TDD）

## Kagura AI 2.0 固有のルール

### 技術スタック
- **Python**: 3.11以上を使用
- **型ヒント**: 必須 (pyright strict mode)
- **テスト**: pytest で実装
- **テストカバレッジ**: 90%+ 維持
- **データ検証**: Pydantic v2を使用
- **LLM統合**: LiteLLM
- **テンプレート**: Jinja2
- **CLI**: Click
- **UI**: Rich

### ディレクトリ構造
```
src/kagura/          # 2.0実装 (変更可能)
├── core/            # コアエンジン
├── agents/          # エージェント
└── cli/             # CLI

src/kagura_legacy/   # レガシーコード (参照のみ、変更禁止)
tests/               # 2.0テスト (変更可能)
tests/*_legacy/      # レガシーテスト (参照のみ、変更禁止)
ai_docs/             # 開発ドキュメント (更新可能)
examples/            # サンプル (Phase 4で更新)
docs/                # ユーザードキュメント (Phase 4で更新)
```

## 変更禁止パス

以下のパスは**絶対に変更しない**こと:

- `src/kagura_legacy/` - レガシーコード (参照のみ)
- `tests/*_legacy/` - レガシーテスト (参照のみ)
- `examples/` - サンプルコード (Phase 4で更新予定)
- `docs/` - ユーザードキュメント (Phase 4で更新予定)
- `LICENSE` - ライセンスファイル
- `CODE_OF_CONDUCT.md` - 行動規範
- `.env*` - 環境変数ファイル

## コミットメッセージ形式

Conventional Commitsに従う:

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

### Scope
- `core`: コアエンジン
- `executor`: コード実行
- `cli`: CLI
- `agents`: エージェント
- `setup`: プロジェクト設定

### 例
```
feat(core): implement @agent decorator (#20)
fix(executor): prevent import bypass (#21)
test(cli): add REPL command tests (#27)
refactor(core): simplify prompt template engine (#22)
docs(api): update agent decorator documentation (#30)
```

## Issue-Driven開発フロー

### 1. Issue作成
- GitHub Issueテンプレートを使用
- `[PHASE-XXX]` プレフィックス付与
- スコープ境界を明確化
- 完了条件を明記

### 2. 実装
1. Feature branchを作成: `feature/PHASE-XXX-description`
2. ai_docs/配下のドキュメントを参照
3. テストを先に書く (TDD)
4. 実装
5. 型チェック (pyright)
6. テスト実行 (pytest)

### 3. Draft PR作成
- タイトル: `<type>(<scope>): <subject> - PHASE-XXX`
- 必ず**Draft**で作成
- Summary、Changes、Test Resultsを記載
- Issueリンク: `Closes #XXX`

### 4. CI確認
- 全てのテストがパス
- Pyright型チェックがパス
- Codecov警告がないこと

### 5. レビュー・マージ
- Draft → Ready for review
- レビュー後にマージ
- Squash mergeを使用

## テスト要件

### 必須テスト
- **ユニットテスト**: 各関数・クラスごと
- **統合テスト**: モジュール間の連携
- **エッジケース**: 境界値テスト
- **エラーハンドリング**: 例外処理テスト

### カバレッジ目標
- **全体**: 90%+
- **コアモジュール**: 95%+
- **新規実装**: 100%

### テスト実行
```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src/kagura --cov-report=html

# 特定モジュール
pytest tests/core/

# 型チェック
pyright src/kagura/
```

## エラー発生時の対応

1. **エラー内容を正確に記録**
   - エラーメッセージ全文
   - スタックトレース
   - 再現手順

2. **Issueにコメントで報告**
   - エラー内容を貼り付け
   - 試した対処法を記載
   - 原因の仮説を記載

3. **人間の指示を待つ**
   - 推測で進めない
   - 複数の選択肢がある場合は提示して質問

4. **解決後にドキュメント更新**
   - ai_docs/fixes/ に記録
   - 同じエラーの再発防止

## よくある質問

### Q: レガシーコードを参考にしたい
A: `src/kagura_legacy/` は参照可能ですが、変更は禁止です。新規実装では2.0の設計に従ってください。

### Q: 大きな変更をどう分割する？
A: 機能単位でIssueとPRを分割。例: デコレータ実装 → テンプレートエンジン → 型パーサー

### Q: テストが書けない機能がある
A: モック、フィクスチャを活用。外部API呼び出しは必ずモック化。

### Q: ドキュメントはいつ書く？
A: Phase 4で一括更新。今は ai_docs/ のみ更新。

## 参考ドキュメント

- `ai_docs/README.md` - AI開発ガイド
- `ai_docs/DEVELOPMENT_ROADMAP.md` - 開発ロードマップ
- `ai_docs/coding_standards.md` - コーディング規約
- `ai_docs/architecture.md` - システムアーキテクチャ
- `ai_docs/glossary.md` - 用語集

---

**このドキュメントに従って、安全で高品質なコードを生成してください。不明点があれば必ず質問してください！**
