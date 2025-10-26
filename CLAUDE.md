# Claude Code Instructions - Kagura AI v4.0

AI開発者向けの開発ガイド。v4.0: Universal AI Memory Platform

---

## 📋 プロジェクト概要

### v4.0の位置づけ

**Kagura AI v4.0** = **Universal AI Memory & Context Platform**

- **目標**: すべてのAIプラットフォーム（Claude, ChatGPT, Gemini等）で共有できるメモリー・コンテキスト管理
- **アプローチ**: MCP-native + REST API
- **特徴**: ローカル/セルフホスト/クラウド対応

### 技術スタック

- **言語**: Python 3.11+
- **主要依存**: Pydantic v2, LiteLLM, FastAPI, NetworkX, ChromaDB
- **開発ツール**: pytest, pyright, ruff, uv

---

## 🎯 開発ルール

### コーディング規約

- **命名**: `snake_case` (モジュール/関数), `PascalCase` (クラス)
- **型ヒント**: 必須（`pyright --strict`準拠）
- **Docstring**: Google形式、必須
- **テスト**: カバレッジ90%+

### コミットメッセージ（Conventional Commits）

```
<type>(<scope>): <subject> (#issue-number)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
**Scope**: `core`, `api`, `mcp`, `graph`, `cli`, `docs`

### ブランチ戦略

**必須**: GitHub IssueからBranch作成

```bash
# 1. Issue作成
gh issue create --title "..." --body "..."

# 2. Issueからブランチ作成
gh issue develop [Issue番号] --checkout

# 3. 実装・テスト・コミット

# 4. Draft PR作成
gh pr create --draft --title "..." --body "..."

# 5. Ready & Merge
gh pr ready [PR番号]
gh pr merge [PR番号] --squash
```

**⛔️ mainへの直接コミット禁止**

---

## 🔄 作業フロー

```
1. Issue作成（必須）
   ↓
2. ブランチ作成（GitHub Issue経由）
   ↓
3. 実装（TDD推奨）
   ↓
4. テスト（pytest, pyright, ruff）
   ↓
5. Draft PR作成
   ↓
6. CI通過 → Ready → Merge
```

---

## 📁 重要なドキュメント

### 開発前に確認

1. **Issue内容**（必読）
2. `ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md` - v4.0ロードマップ
3. `ai_docs/V4.0_STRATEGIC_PIVOT.md` - v4.0戦略方針
4. `ai_docs/CODING_STANDARDS.md` - コーディング規約
5. `ai_docs/ARCHITECTURE.md` - アーキテクチャ
6. `ai_docs/MEMORY_STRATEGY.md` - メモリー戦略

### ディレクトリ構造

```
kagura-ai/
├── src/kagura/
│   ├── core/              # Memory, Graph, LLM
│   ├── api/               # REST API (FastAPI)
│   ├── mcp/               # MCP Server & Tools
│   ├── cli/               # CLI commands
│   └── tools/             # Built-in tools
│
├── tests/                 # テスト
├── docs/                  # ユーザードキュメント
├── ai_docs/               # 開発ドキュメント
├── examples/              # 使用例
│
├── pyproject.toml
├── CLAUDE.md              # このファイル
└── README.md
```

---

## 🧪 テスト・品質チェック

### コマンド

```bash
# セットアップ
uv sync --all-extras

# テスト（並列）
pytest -n auto

# カバレッジ
pytest --cov=src/kagura --cov-report=html

# 型チェック
pyright src/kagura/

# リント
ruff check src/
ruff format src/
```

### 必須テスト

- ユニットテスト: 各関数・クラス
- 統合テスト: モジュール間連携
- エッジケース: 境界値
- エラーハンドリング: 例外処理

---

## ⚙️ Git操作

```bash
# ブランチ作成（GitHub Issueから）
gh issue develop [Issue番号] --checkout

# コミット
git add .
git commit -m "feat(scope): description (#XX)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# プッシュ & PR
git push
gh pr create --draft --title "..." --body "..."

# Merge
gh pr ready [PR番号]
gh pr merge [PR番号] --squash
```

---

## 🚨 エラー発生時

1. **エラー内容を記録**（全文・スタックトレース）
2. **Issueにコメント**
3. **人間の指示を待つ**（推測で進めない）
4. **解決後にドキュメント更新**

---

## 📚 参考

- **ロードマップ**: `ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md`
- **戦略方針**: `ai_docs/V4.0_STRATEGIC_PIVOT.md`
- **コーディング規約**: `ai_docs/CODING_STANDARDS.md`
- **API仕様**: `docs/api-reference.md`, `docs/api/reference.yaml`
- **CHANGELOG**: `CHANGELOG.md`

---

**このガイドに従って、高品質なコードを生成してください。不明点は必ず質問してください！**
