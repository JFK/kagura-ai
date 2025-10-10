# GitHub Actions Setup Guide

このガイドでは、Kagura AIプロジェクトのGitHub Actions workflowsの設定方法を説明します。

## 📋 目次

1. [Workflows概要](#workflows概要)
2. [GitHub Secretsの設定](#github-secretsの設定)
3. [各Workflowの詳細](#各workflowの詳細)
4. [トラブルシューティング](#トラブルシューティング)

---

## Workflows概要

Kagura AIプロジェクトには4つのGitHub Actions workflowsがあります：

| Workflow | ファイル | 実行タイミング | 目的 |
|----------|---------|--------------|------|
| **Tests** | `test.yml` | PR, push to main | ユニット・機能テスト |
| **Integration Tests** | `integration_tests.yml` | 手動, スケジュール, push to main | 統合テスト（API呼び出し） |
| **Deploy PyPI** | `deploy_pypi.yml` | タグpush (v*) | PyPIへのリリース |
| **Deploy Docs** | `deploy_mkdocs.yml` | push to main | ドキュメントデプロイ |

---

## GitHub Secretsの設定

### 必須: OPENAI_API_KEY

Integration testsを実行するには、OpenAI API keyが必要です。

#### 手順

1. **GitHubリポジトリページを開く**
   ```
   https://github.com/<YOUR_USERNAME>/kagura-ai
   ```

2. **Settings > Secrets and variables > Actions に移動**
   - リポジトリのSettings タブをクリック
   - 左サイドバーから "Secrets and variables" > "Actions" を選択

3. **"New repository secret" をクリック**

4. **シークレットを追加**

   **Name**: `OPENAI_API_KEY`

   **Secret**: `sk-...` （あなたのOpenAI API key）

   **Add secret** をクリック

#### OpenAI API Keyの取得方法

1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. ログイン
3. "Create new secret key" をクリック
4. Key nameを入力（例: `kagura-ci`）
5. "Create secret key" をクリック
6. 表示されたkeyをコピー（⚠️ 一度しか表示されません）
7. GitHub Secretsに貼り付け

---

### オプション: その他のAPI Keys

追加のLLMプロバイダーをテストする場合：

#### ANTHROPIC_API_KEY

**Name**: `ANTHROPIC_API_KEY`

**Secret**: `sk-ant-...`

**取得方法**: [Anthropic Console](https://console.anthropic.com/settings/keys)

---

#### GOOGLE_API_KEY

**Name**: `GOOGLE_API_KEY`

**Secret**: `AIza...`

**取得方法**: [Google AI Studio](https://makersuite.google.com/app/apikey)

---

### PyPI Deployment用（メンテナーのみ）

#### PYPI_API_TOKEN

**Name**: `PYPI_API_TOKEN`

**Secret**: `pypi-...`

**取得方法**:
1. [PyPI Account Settings](https://pypi.org/manage/account/) にアクセス
2. "Add API token" をクリック
3. Scope: "Entire account" または "Project: kagura-ai"
4. Token nameを入力
5. "Add token" をクリック
6. 表示されたトークンをコピー

---

## 各Workflowの詳細

### 1. Tests Workflow (`test.yml`)

**目的**: PRとmain branchへのpush時に、ユニット・機能テストを実行

**実行内容**:
- ✅ Pyright型チェック（strict mode）
- ✅ Ruffリント
- ✅ Pytest（統合テスト除外）
- ✅ Codecovカバレッジアップロード

**実行条件**:
```yaml
on:
  push:
    branches: [main]
    paths: ['src/**', 'tests/**', 'pyproject.toml']
  pull_request:
    paths: ['src/**', 'tests/**', 'pyproject.toml']
```

**特徴**:
- API key不要（モック使用）
- 実行時間: 約5-10分
- コスト: $0

**手動実行**:
```bash
# GitHub UI: Actions > Run tests > Run workflow
# または
gh workflow run test.yml
```

---

### 2. Integration Tests Workflow (`integration_tests.yml`) 🆕

**目的**: 実際のAPI呼び出しを伴う統合テストを実行

**実行内容**:
- ✅ `@pytest.mark.integration` テストのみ実行
- ✅ OpenAI/Anthropic/Google APIと実際に通信
- ⚠️ API使用料が発生

**実行条件**:
```yaml
on:
  workflow_dispatch:  # 手動実行
  schedule:
    - cron: '0 2 * * *'  # 毎日午前2時（UTC）
  push:
    branches: [main]
    paths: ['src/**', 'tests/**', 'pyproject.toml']
```

**特徴**:
- API key必須（`OPENAI_API_KEY`）
- 実行時間: 約10-30分
- コスト: 約$0.10-1.00/回（実装による）
- PRでは実行されない（コスト削減）

**手動実行**:
```bash
# 全統合テスト
gh workflow run integration_tests.yml

# 特定のテストパターンのみ
gh workflow run integration_tests.yml \
  -f test_pattern="test_mcp"
```

**GitHub UI**:
1. Actions > Integration Tests を選択
2. "Run workflow" をクリック
3. Test pattern（オプション）を入力
4. "Run workflow" をクリック

---

### 3. Deploy PyPI Workflow (`deploy_pypi.yml`)

**目的**: 新しいバージョンをPyPIにリリース

**実行条件**:
```yaml
on:
  push:
    tags:
      - 'v*'  # v2.2.0, v2.3.0 等
```

**リリース手順**:
```bash
# 1. バージョン更新
# pyproject.toml の version を更新

# 2. Git tag作成
git tag v2.3.0
git push origin v2.3.0

# 3. GitHub Actionsが自動実行
# PyPIへのデプロイ、GitHub Releaseの作成
```

**必要なSecret**: `PYPI_API_TOKEN`

---

### 4. Deploy Docs Workflow (`deploy_mkdocs.yml`)

**目的**: MkDocsドキュメントをGitHub Pagesにデプロイ

**実行条件**:
```yaml
on:
  push:
    branches: [main]
    paths: ['docs/**', 'mkdocs.yml']
```

**アクセス**: https://<USERNAME>.github.io/kagura-ai/

---

## コスト見積もり

### Integration Tests

各実行あたりの推定コスト：

| テスト種別 | API呼び出し数 | 推定コスト |
|-----------|-------------|----------|
| MCP Integration | 5-10 | $0.01-0.05 |
| Memory RAG | 10-20 | $0.02-0.10 |
| Routing | 10-15 | $0.02-0.08 |
| Full Suite | 50-100 | $0.10-0.50 |

**月間推定**:
- 毎日1回（スケジュール）: $3-15/月
- 手動実行: $0.10-0.50/回
- Main pushでの自動実行: 変動

**コスト削減策**:
1. PRでは統合テストを実行しない（実装済み）
2. スケジュール頻度を調整（毎日 → 週1回）
3. 特定のテストのみ手動実行

---

## トラブルシューティング

### ❌ "OPENAI_API_KEY is not set"

**原因**: GitHub Secretsが設定されていない

**解決策**:
1. [GitHub Secretsの設定](#github-secretsの設定) を確認
2. Secret名が正確に `OPENAI_API_KEY` であることを確認（大文字小文字区別）
3. リポジトリの権限を確認（Settings > Actions > General > Workflow permissions）

---

### ❌ Integration tests fail with "Rate limit exceeded"

**原因**: OpenAI API rate limitに達した

**解決策**:
1. OpenAI Platformで使用状況を確認
2. Usage limitsを増やす
3. テスト頻度を減らす（スケジュールを週1回に変更）

---

### ❌ Type checking fails on PR

**原因**: v2.2.0から型チェックが厳格化（`|| true` 削除）

**解決策**:
1. ローカルで型チェックを実行:
   ```bash
   uv run pyright src/kagura/
   ```
2. エラーを修正
3. 再度pushして確認

---

### ❌ Linting fails on PR

**原因**: Ruffリンターが厳格化

**解決策**:
1. ローカルでリントを実行:
   ```bash
   uv run ruff check src/kagura/
   ```
2. 自動修正:
   ```bash
   uv run ruff check --fix src/kagura/
   ```
3. 手動でエラーを修正
4. 再度pushして確認

---

## ベストプラクティス

### 1. PRを出す前に

ローカルでテストを実行してCIの失敗を防ぐ：

```bash
# 型チェック
uv run pyright src/kagura/

# リント
uv run ruff check src/kagura/

# テスト
pytest -m "not integration"
```

---

### 2. Integration testsの実行タイミング

- ✅ **重要な変更後**: 手動で実行
- ✅ **毎日のスケジュール**: 回帰検出
- ❌ **PRごと**: コスト高、不要

---

### 3. API Keyのセキュリティ

- ✅ GitHub Secretsに保存（暗号化）
- ✅ コードに直接書かない
- ✅ `.env` ファイルはgitignore
- ✅ 定期的にrotate（更新）

---

## 参考リンク

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Anthropic Console](https://console.anthropic.com/)
- [PyPI Account Settings](https://pypi.org/manage/account/)

---

## 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2025-10-10 | Integration tests workflow追加、test.yml厳格化 |
| 2024-10-09 | 初版作成 |

---

**問題が解決しない場合は、GitHub Issuesで報告してください。**
