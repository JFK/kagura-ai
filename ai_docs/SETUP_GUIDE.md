# Claude Code ワークフロー セットアップガイド

## 概要

このガイドでは、Kagura AIプロジェクトでClaude Codeを使った効率的な開発ワークフローをセットアップする方法を説明します。

---

## 前提条件

- Claude Codeがインストール済み
- GitHubリポジトリへのアクセス権限
- Python 3.11以上の環境

---

## 1. ai_docs/の確認

`ai_docs/`ディレクトリには、Claude Codeが参照する重要なドキュメントが格納されています。

### ディレクトリ構成

```
ai_docs/
├── README.md                 # このディレクトリの説明
├── architecture.md          # システムアーキテクチャ
├── coding_standards.md      # コーディング規約
├── glossary.md             # 用語集
├── migration_guide.md      # 移行ガイド
├── SETUP_GUIDE.md          # このファイル
├── analysis/               # 調査レポート
├── suggestions/            # 技術的提案
└── fixes/                  # バグ修正記録
```

### 初期確認

各ドキュメントを一読し、プロジェクトの理解を深めてください:

```bash
# アーキテクチャの確認
cat ai_docs/architecture.md

# コーディング規約の確認
cat ai_docs/coding_standards.md

# 用語集の確認
cat ai_docs/glossary.md
```

---

## 2. Issue Templatesの確認

`.github/ISSUE_TEMPLATE/`には、Claude Code最適化されたテンプレートが用意されています。

### Claude Code専用テンプレート

| テンプレート | 用途 | ラベル |
|------------|------|--------|
| `claude_migration_task.md` | コード移行・アップグレード | `migration, claude-code` |
| `claude_bug_fix.md` | バグ修正 | `bug, claude-code` |
| `claude_development_task.md` | 汎用開発タスク | `development, claude-code` |
| `claude_investigation_task.md` | 調査・分析 | `investigation, claude-code` |
| `claude_rfc.md` | 技術的意思決定 | `rfc, claude-code` |

### 一般ユーザー向けテンプレート

| テンプレート | 用途 |
|------------|------|
| `bug_report.md` | バグ報告 |
| `feature_request.md` | 機能リクエスト |
| `task.md` | タスク管理 |
| `documentation_improvement.md` | ドキュメント改善 |
| `question.md` | 質問 |

---

## 3. GitHubラベルの作成

以下のラベルを作成することを推奨します:

```bash
# GitHub CLIを使用する場合
gh label create "claude-code" --color "0E8A16" --description "Claude Codeで処理するタスク"
gh label create "migration" --color "FBCA04" --description "コード移行タスク"
gh label create "development" --color "1D76DB" --description "新機能開発"
gh label create "investigation" --color "A2EEEF" --description "調査タスク"
gh label create "rfc" --color "D4C5F9" --description "提案・方式検討"
gh label create "in-progress" --color "C5DEF5" --description "作業中"
gh label create "needs-review" --color "FEF2C0" --description "レビュー待ち"
gh label create "ai-docs" --color "7057FF" --description "AI向けドキュメント関連"
```

手動作成する場合は、GitHubの`Issues` → `Labels` → `New label`から作成してください。

---

## 4. Branch Protection Rulesの設定

Claude Codeが直接mainブランチに変更を加えないよう保護します。

### 設定手順

1. リポジトリの`Settings` → `Branches`
2. `Add branch protection rule`をクリック
3. Branch name pattern: `main`
4. 以下をチェック:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1人以上)
   - ✅ Require status checks to pass before merging

---

## 5. 開発環境のセットアップ

### 仮想環境の作成

```bash
# uvを使用
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係のインストール
uv pip install -e ".[dev]"
```

### pre-commit hooksのインストール

```bash
# フックのインストール
pre-commit install

# 手動実行で確認
pre-commit run --all-files
```

---

## 6. 最初のIssueを作成

Claude Codeの動作確認として、簡単なIssueを作成します。

### 例: 調査タスク

1. GitHubで`New Issue`をクリック
2. `Claude Code - Investigation Task`テンプレートを選択
3. 以下の内容で作成:

```markdown
## 🔍 調査目的
プロジェクトのテストカバレッジを確認し、改善点を特定する

## 📂 調査対象
**ディレクトリ/ファイル**:
- tests/

**技術/ライブラリ**:
- pytest
- pytest-cov

## 📋 Claude Code用タスク定義
(テンプレートのまま)
```

---

## 7. Claude Codeでタスクを実行

### 基本的なワークフロー

```bash
# 1. Issueを読み込む
claude code

# プロンプト:
# "GitHub Issue #XX を読み込んで、タスクを実行してください"
```

Claude Codeが以下を自動実行:
1. ブランチ作成
2. コード調査・実装
3. コミット
4. Draft PR作成

### 作業確認

```bash
# ブランチ確認
git branch

# 変更確認
git status
git diff

# Draft PR確認
gh pr list --state open
```

---

## 8. レビューとマージ

### レビューのポイント

1. **CIのステータス確認**
   - lint, test, buildが全てグリーンか

2. **コード品質確認**
   - `ai_docs/coding_standards.md`に準拠しているか
   - 型ヒントが適切か
   - テストカバレッジが十分か

3. **作業ログ確認**
   - Issueに作業内容が記録されているか
   - 未解決の問題が明示されているか

### マージ手順

```bash
# Draft PRをReady for reviewに変更
gh pr ready <PR番号>

# レビュー後、マージ
gh pr merge <PR番号> --squash
```

---

## 9. トラブルシューティング

### Claude Codeがエラーを起こす

1. **ai_docs/の内容を確認**
   - 情報が不足していないか
   - 矛盾する情報がないか

2. **Issueの指示を明確にする**
   - スコープ境界を明示
   - 禁止パスを指定

3. **段階的に進める**
   - 大きなタスクは分割
   - 調査→実装の順で進める

### CIが失敗する

```bash
# ローカルでチェック
make ruff    # lint
make right   # 型チェック
make test    # テスト

# 個別に修正
ruff check --fix src/
pyright src/
pytest tests/
```

### マージコンフリクト

```bash
# mainから最新を取得
git checkout main
git pull origin main

# 作業ブランチをリベース
git checkout feature/xxx
git rebase main

# コンフリクト解決後
git push --force-with-lease
```

---

## 10. ベストプラクティス

### Issue作成時

- [ ] タイトルは簡潔に (50文字以内)
- [ ] スコープ境界を明確に
- [ ] 参考資料のリンクを含める
- [ ] 完了条件をチェックリストで明示

### Claude Code実行時

- [ ] 最初は小さなタスクで試す
- [ ] 作業中は定期的にステータス確認
- [ ] 不明点があれば人間に質問させる

### レビュー時

- [ ] CIステータスを確認
- [ ] コーディング規約準拠を確認
- [ ] テストカバレッジを確認
- [ ] セキュリティリスクを確認

---

## 11. 参考資料

### プロジェクト内
- [ai_docs/README.md](./README.md) - AI Docsの使い方
- [ai_docs/architecture.md](./architecture.md) - アーキテクチャ
- [ai_docs/coding_standards.md](./coding_standards.md) - コーディング規約
- [ai_docs/glossary.md](./glossary.md) - 用語集

### 外部リンク
- [Claude Code公式ドキュメント](https://docs.claude.com/en/docs/claude-code)
- [Issue-Driven AI Development実践ガイド](https://qiita.com/kiyotaman/items/87a5a9ddc88db64f78ac)
- [GitHub Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## 次のステップ

1. **最初のIssueを作成**
   - 調査タスクから始める

2. **Claude Codeで実行**
   - 動作を確認しながら進める

3. **フィードバックループ**
   - ai_docs/を改善
   - Issue Templateを調整
   - ワークフローを最適化

---

このセットアップガイドは、チームの成長に合わせて更新してください。
