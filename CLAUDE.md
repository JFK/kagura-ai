# Claude Code Instructions - Kagura AI 2.0

このファイルは、Claude Codeが常に参照する開発ガイドです。

---

## 📋 1. プロジェクト概要

### プロジェクトの目的

**Kagura AI 2.0** は、Python関数を1行のデコレータでAIエージェントに変換するフレームワークです。

**主要機能**:
- `@agent` デコレータによる1行AI変換
- Jinja2テンプレートによる強力なプロンプト生成
- 型ヒントベースの自動レスポンスパース（Pydantic対応）
- 安全なPythonコード実行エンジン（AST検証）
- インタラクティブREPL（`kagura repl`）
- マルチLLMサポート（OpenAI、Anthropic、Google等）

### 技術スタック

**言語**: Python 3.11+

**コアフレームワーク**:
- **Pydantic v2**: データ検証、型パーサー
- **LiteLLM**: マルチLLM統合
- **Jinja2**: プロンプトテンプレート
- **Click**: CLIフレームワーク
- **Rich**: ターミナルUI

**開発ツール**:
- **pytest**: テストフレームワーク
- **pyright**: 型チェッカー（strict mode）
- **ruff**: リンター・フォーマッター
- **uv**: パッケージマネージャー

**CI/CD**:
- GitHub Actions
- Codecov
- PyPI自動デプロイ

---

## 🎯 2. 開発ルール

### コーディング規約

#### 命名規則
- **モジュール/パッケージ**: `snake_case` （例: `kagura.core.agent`）
- **クラス名**: `PascalCase` （例: `AtomicAgent`, `LLMConfig`）
- **関数/変数**: `snake_case` （例: `create_agent`, `agent_instance`）
- **定数**: `UPPER_SNAKE_CASE` （例: `DEFAULT_MODEL`, `MAX_RETRIES`）
- **プライベート**: `_leading_underscore` （例: `_internal_state`）

#### 型ヒント（必須）
```python
# ✅ 正しい
def process_data(
    input_data: dict[str, Any],
    max_items: int = 10
) -> list[dict[str, str]]:
    """データを処理"""
    pass

# ❌ 型ヒントなしは禁止
def process_data(input_data, max_items=10):
    pass
```

**型チェック**: `pyright --strict` に準拠すること

#### ドキュメンテーション
```python
def create_agent(name: str, model: str = "gpt-4o-mini") -> Agent:
    """エージェントを作成する

    Args:
        name: エージェント名
        model: 使用するLLMモデル（デフォルト: gpt-4o-mini）

    Returns:
        作成されたAgentインスタンス

    Raises:
        ValueError: nameが空の場合
    """
    pass
```

### コミットメッセージ規約（Conventional Commits）

**形式**:
```
<type>(<scope>): <subject> (#issue-number)

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント
- `chore`: ビルド、設定変更

**Scope**:
- `core`: コアエンジン
- `executor`: コード実行
- `cli`: CLI
- `agents`: エージェント
- `ai_docs`: 開発ドキュメント

**例**:
```
feat(core): implement @agent decorator (#20)
fix(executor): prevent import bypass (#21)
test(cli): add REPL command tests (#27)
docs(api): update agent decorator documentation (#30)
```

### ブランチ戦略

**メインブランチ**:
- `main`: 安定版（PyPI公開）

**開発ブランチ**:
- `feature/PHASE-XXX-description`: 機能実装
- `fix/issue-XXX-description`: バグ修正

**マージ戦略**:
- Squash mergeを使用
- Draft PR → Ready for review → Merge

---

## 📁 3. 重要なディレクトリとファイル

### 開始前に必ず参照すべきドキュメント

**必須確認（作業前に読むこと）**:
1. `ai_docs/README.md` - AI開発ガイド
2. `ai_docs/UNIFIED_ROADMAP.md` - 統合開発ロードマップ（v2.0.0〜v2.5.0+）
3. `ai_docs/NEXT_STEPS.md` - 次のアクション
4. `ai_docs/coding_standards.md` - コーディング規約
5. **対象Issueの内容**（完全理解）

**RFC参照**:
- `ai_docs/RFC_*.md` - 各機能の詳細仕様（002-014）

### 絶対に変更してはいけないパス

**⛔️ 変更禁止**:
```
src/kagura_legacy/     # レガシーコード（参照のみ）
tests/*_legacy/        # レガシーテスト（参照のみ）
examples/              # サンプルコード（Phase 4まで変更禁止）
docs/                  # ユーザードキュメント（Phase 4まで変更禁止）
LICENSE                # ライセンスファイル
CODE_OF_CONDUCT.md     # 行動規範
.env*                  # 環境変数ファイル
```

**✅ 変更可能**:
```
src/kagura/            # 2.0実装
tests/                 # 2.0テスト
ai_docs/               # 開発ドキュメント
pyproject.toml         # プロジェクト設定
```

### ディレクトリ構造

```
kagura-ai/
├── src/kagura/              # 2.0実装（変更可能）
│   ├── core/                # コアエンジン
│   │   ├── decorators.py    # @agent
│   │   ├── executor.py      # CodeExecutor
│   │   ├── llm.py           # LLM統合
│   │   └── parser.py        # 型パーサー
│   ├── agents/              # エージェント
│   └── cli/                 # CLI
│
├── src/kagura_legacy/       # レガシー（参照のみ、変更禁止）
│
├── tests/                   # 2.0テスト（変更可能）
├── tests/*_legacy/          # レガシーテスト（参照のみ）
│
├── ai_docs/                 # 開発ドキュメント（更新可能）
│   ├── README.md
│   ├── UNIFIED_ROADMAP.md   # 統合ロードマップ
│   ├── NEXT_STEPS.md        # 次のアクション
│   ├── RFC_*.md             # 各RFC仕様
│   └── coding_standards.md
│
├── examples/                # サンプル（Phase 4で更新）
├── docs/                    # ユーザードキュメント（Phase 4で更新）
│
├── pyproject.toml           # プロジェクト設定
├── CLAUDE.md                # このファイル
└── README.md                # プロジェクト紹介
```

### 設定ファイルの場所

- **pyproject.toml**: プロジェクト設定、依存関係、ビルド設定
- **pytest**: `[tool.pytest.ini_options]` in pyproject.toml
- **pyright**: `[tool.pyright]` in pyproject.toml
- **ruff**: `[tool.ruff]` in pyproject.toml
- **.env**: 環境変数（ローカルのみ、Git管理外）

---

## 🧪 4. テスト要件

### テストカバレッジ目標

- **全体**: 90%以上
- **コアモジュール**: 95%以上
- **新規実装**: 100%

### 必須テスト種別

1. **ユニットテスト**: 各関数・クラスごと
2. **統合テスト**: モジュール間の連携
3. **エッジケース**: 境界値テスト
4. **エラーハンドリング**: 例外処理テスト

### テストコマンド

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src/kagura --cov-report=html

# 特定モジュール
pytest tests/core/

# マーカー指定
pytest -m "not integration"  # 統合テストを除外

# 型チェック
pyright src/kagura/

# リント
ruff check src/
```

### テスト作成の必須条件

```python
# tests/core/test_example.py
import pytest
from kagura.core.example import example_function

def test_example_function_basic():
    """基本動作のテスト"""
    result = example_function("input")
    assert result == "expected"

def test_example_function_edge_case():
    """エッジケースのテスト"""
    result = example_function("")
    assert result == ""

def test_example_function_error():
    """エラーハンドリングのテスト"""
    with pytest.raises(ValueError):
        example_function(None)

@pytest.mark.asyncio
async def test_async_function():
    """非同期関数のテスト"""
    result = await async_example()
    assert result is not None
```

---

## 🔄 5. 作業フロー（Issue駆動開発）

### Phase 0: 準備

1. **ドキュメント確認**（必須）
   ```bash
   # 以下を必ず読む
   cat ai_docs/README.md
   cat ai_docs/UNIFIED_ROADMAP.md
   cat ai_docs/NEXT_STEPS.md
   cat ai_docs/coding_standards.md
   ```

2. **Issue内容の完全理解**
   - 対象Issue番号を確認
   - 完了条件を明確化
   - スコープ境界を確認

3. **現在のPhase確認**
   - `ai_docs/UNIFIED_ROADMAP.md`で現在のPhaseを確認
   - v2.0.0, v2.1.0等、どのバージョンか把握

### Phase 1: 実装

1. **Feature branchを作成**
   ```bash
   git checkout -b feature/PHASE-XXX-description
   ```

2. **TDD（テスト駆動開発）**
   - テストを先に書く
   - 実装
   - テストがパスすることを確認

3. **型チェック・リント**
   ```bash
   pyright src/kagura/
   ruff check src/
   ```

### Phase 2: Draft PR作成

**タイトル形式**:
```
<type>(<scope>): <subject> - PHASE-XXX
```

**PRテンプレート**:
```markdown
## Summary
このPRは...を実装します。

## Changes
- src/kagura/core/example.py: 新機能追加
- tests/core/test_example.py: テスト追加

## Test Results
```bash
pytest --cov
# 結果を貼り付け
```

## Related Issues
Closes #XXX
```

**必ずDraftで作成**:
```bash
gh pr create --draft \
  --title "feat(core): implement @agent decorator - PHASE-1" \
  --body "..."
```

### Phase 3: CI確認

- ✅ 全テストパス
- ✅ Pyright型チェックパス
- ✅ Ruffリントパス
- ✅ Codecov警告なし

### Phase 4: レビュー・マージ

```bash
# Draft → Ready for review
gh pr ready [PR番号]

# レビュー後、Squash merge
gh pr merge [PR番号] --squash
```

---

## ⚙️ 6. よく使うコマンド

### 開発環境セットアップ

```bash
# Python 3.11+ 確認
python --version

# 依存関係インストール
uv sync

# 開発用依存関係も含める
uv sync --all-extras
```

### ビルド

```bash
# パッケージビルド
uv build

# ビルド成果物確認
ls dist/
```

### テスト

```bash
# 全テスト
pytest

# カバレッジ付き
pytest --cov=src/kagura --cov-report=html

# 特定ファイル
pytest tests/core/test_decorators.py

# 特定テスト関数
pytest tests/core/test_decorators.py::test_agent_basic

# 並列実行
pytest -n auto

# 失敗したテストのみ再実行
pytest --lf
```

### 型チェック・リント

```bash
# 型チェック（strict mode）
pyright src/kagura/

# リント
ruff check src/

# 自動修正
ruff check --fix src/

# フォーマット
ruff format src/
```

### REPL

```bash
# インタラクティブREPL起動
kagura repl

# REPL内コマンド
/help     # ヘルプ表示
/agents   # 定義済みエージェント一覧
/exit     # 終了
/clear    # 画面クリア
```

### Git操作

```bash
# ブランチ作成
git checkout -b feature/PHASE-XXX-description

# コミット（Conventional Commits）
git add .
git commit -m "feat(core): implement new feature (#XX)"

# プッシュ
git push -u origin feature/PHASE-XXX-description

# Draft PR作成
gh pr create --draft \
  --title "feat(core): implement new feature - PHASE-XXX" \
  --body "Summary of changes"
```

### PyPI公開（リリース時のみ）

```bash
# バージョン確認
cat pyproject.toml | grep version

# ビルド
uv build

# TestPyPI（テスト環境）
uv publish --repository testpypi

# 本番PyPI
uv publish

# GitHubリリース
gh release create v2.0.0 \
  --title "Kagura AI v2.0.0" \
  --notes "Release notes here"
```

---

## 🚨 エラー発生時の対応

### 手順

1. **エラー内容を正確に記録**
   - エラーメッセージ全文
   - スタックトレース
   - 再現手順

2. **Issueにコメントで報告**
   ```markdown
   ## エラー報告

   ### エラー内容
   ```
   [エラーメッセージ全文]
   ```

   ### 試した対処法
   - XXXを試した → 結果

   ### 原因の仮説
   - YYYが原因と思われる
   ```

3. **人間の指示を待つ**
   - 推測で進めない
   - 複数の選択肢がある場合は提示して質問

4. **解決後にドキュメント更新**
   - `ai_docs/fixes/` に記録（該当する場合）
   - 同じエラーの再発防止

---

## ❓ よくある質問

### Q: レガシーコードを参考にしたい
A: `src/kagura_legacy/` は参照可能ですが、**変更は絶対に禁止**です。新規実装では2.0の設計に従ってください。

### Q: 大きな変更をどう分割する？
A: 機能単位でIssueとPRを分割。例: デコレータ実装 → テンプレートエンジン → 型パーサー

### Q: テストが書けない機能がある
A: モック、フィクスチャを活用。外部API呼び出しは必ずモック化。

### Q: ドキュメントはいつ書く？
A: Phase 4（v2.0.0統合・テスト段階）で一括更新。今は `ai_docs/` のみ更新。

### Q: RFCの優先順位は？
A: `ai_docs/UNIFIED_ROADMAP.md` を参照。
- Very High: RFC-007（MCP Integration）
- High: RFC-006, 012, 014
- その他は Medium

---

## 📚 参考リンク

- [ai_docs/README.md](./ai_docs/README.md) - AI開発ガイド
- [ai_docs/UNIFIED_ROADMAP.md](./ai_docs/UNIFIED_ROADMAP.md) - 統合ロードマップ
- [ai_docs/NEXT_STEPS.md](./ai_docs/NEXT_STEPS.md) - 次のアクション
- [ai_docs/coding_standards.md](./ai_docs/coding_standards.md) - コーディング規約
- [.github/ISSUE_TEMPLATE/](./github/ISSUE_TEMPLATE/) - Issueテンプレート

---

**このドキュメントに従って、安全で高品質なコードを生成してください。不明点があれば必ず質問してください！**
