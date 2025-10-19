# Claude Code Instructions - Kagura AI v3.0

AI開発者向けのシンプルな開発ガイド。v3.0方針に基づく。

---

## 📋 1. プロジェクト概要

### コンセプト: Python-First AI Agent SDK

**v3.0の位置づけ**:
- **SDK軸**: Python開発者が自分のアプリに組み込むSDK
- **Chat**: SDK機能を手軽に試せるボーナス機能

**主要機能**:
- `@agent` デコレータ（1行でAIエージェント化）
- Built-in tools（Web search, File ops, Code exec）
- Memory management（3-tier system）
- Full type safety（pyright strict）
- Interactive Chat（Claude Code-like）

### 技術スタック

**言語**: Python 3.11+

**主要依存**:
- Pydantic v2, LiteLLM, OpenAI SDK
- Jinja2, Click, Rich
- ChromaDB (optional, for Memory)

**開発ツール**:
- pytest, pyright, ruff, uv

---

## 🎯 2. 開発ルール

### コーディング規約

- **命名**: `snake_case` (モジュール/関数), `PascalCase` (クラス)
- **型ヒント**: 必須（`pyright --strict`準拠）
- **Docstring**: Google形式、必須

### コミットメッセージ（Conventional Commits）

```
<type>(<scope>): <subject> (#issue-number)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
**Scope**: `core`, `chat`, `tools`, `cli`, `docs`

### ブランチ戦略

**必須**: GitHub IssueからBranch作成

```bash
# 1. Issue作成
gh issue create --title "..." --body "..."

# 2. Issueからブランチ作成
gh issue develop [Issue番号] --checkout

# 3. 実装・コミット

# 4. Draft PR作成
gh pr create --draft --title "..." --body "..."
```

**⛔️ mainへの直接コミット禁止**

---

## 🔄 3. 作業フロー（Issue駆動）

### 必須手順

```
1. Issue作成（必須）
   ↓
2. GitHub IssueからBranch作成（必須）
   ↓
3. 実装（TDD推奨）
   ↓
4. Draft PR作成
   ↓
5. CI通過 → Ready for review → Merge
```

**参考**: [Issue駆動AI開発](https://qiita.com/kiyotaman/items/70af26501e10036cb117)

---

## 📁 4. 重要なディレクトリ

### 開発前に確認

1. `ai_docs/V3.0_DEVELOPMENT.md` - v3.0開発ガイド（最重要）
2. `ai_docs/ROADMAP_v3.md` - v3.0ロードマップ
3. `ai_docs/V3.0_PIVOT.md` - v3.0方針（SDK-first）
4. `ai_docs/coding_standards.md` - コーディング規約
5. `ai_docs/DOCUMENTATION_GUIDE.md` - ドキュメント管理ルール
6. **対象Issueの内容**（必読）

### ディレクトリ構造

```
kagura-ai/
├── src/kagura/            # v3.0実装
│   ├── core/              # @agent, LLM, Memory
│   ├── chat/              # Interactive chat
│   ├── agents/            # Personal tools
│   ├── tools/             # Built-in tools
│   └── cli/               # CLI commands
│
├── tests/                 # テスト
├── examples/              # SDK使用例
├── docs/                  # ユーザードキュメント
├── ai_docs/               # 開発ドキュメント
│
├── pyproject.toml         # プロジェクト設定
├── CLAUDE.md              # このファイル
└── README.md              # プロジェクト紹介
```

### 変更可能/禁止

**✅ 変更可能**:
- `src/kagura/`
- `tests/`
- `examples/`
- `docs/`
- `ai_docs/`
- `pyproject.toml`

**⛔️ 変更禁止**:
- `LICENSE`
- `CODE_OF_CONDUCT.md`
- `.env*`

---

## 🧪 5. テスト要件

### テストコマンド

```bash
# 並列実行（推奨）
pytest -n auto

# カバレッジ
pytest -n auto --cov=src/kagura --cov-report=html

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

**カバレッジ目標**: 90%+

---

## ⚙️ 6. よく使うコマンド

### 開発環境

```bash
# セットアップ
uv sync --all-extras

# テスト
pytest -n auto

# 型チェック・リント
pyright src/kagura/
ruff check src/
```

### Git操作

```bash
# ブランチ作成（GitHub Issueから）
gh issue develop [Issue番号] --checkout

# コミット
git add .
git commit -m "feat(core): implement feature (#XX)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# プッシュ
git push

# Draft PR作成
gh pr create --draft --title "..." --body "..."

# Ready & Merge
gh pr ready [PR番号]
gh pr merge [PR番号] --squash
```

---

## 📚 7. 参考ドキュメント

### 必須
- `ai_docs/ROADMAP_v3.md` - v3.0ロードマップ
- `ai_docs/V3.0_PIVOT.md` - v3.0方針
- `ai_docs/coding_standards.md` - コーディング規約

### v3.0方針

**SDK軸**:
- Python開発者がアプリに組み込む
- 型安全、テスト可能、Production-ready
- `from kagura import agent` で即座に使える

**Chat（ボーナス）**:
- SDK機能を手軽に試せる
- Claude Code-like UX
- プロトタイピング・実験用

---

## 🚨 エラー発生時

1. **エラー内容を記録**（全文・スタックトレース）
2. **Issueにコメント**
3. **人間の指示を待つ**（推測で進めない）
4. **解決後にドキュメント更新**

---

## ❓ よくある質問

### Q: ブランチ作成方法は？
A: **必ずGitHub Issueから作成**

```bash
gh issue create --title "..." --body "..."
gh issue develop [Issue番号] --checkout
```

### Q: mainへの直接コミットは？
A: **絶対禁止**。すべてPR経由。

### Q: テストが書けない機能は？
A: モック・フィクスチャ活用。外部APIは必ずモック化。

### Q: v3.0の優先度は？
A: `ai_docs/ROADMAP_v3.md` 参照

**現在の最優先**:
- ドキュメント刷新（Issue #315）
- SDK化推進
- Examples更新

---

**このガイドに従って、高品質なコードを生成してください。不明点は必ず質問してください！**
