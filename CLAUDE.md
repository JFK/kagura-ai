# Claude Code Instructions - Kagura AI v4.0.9

AI開発者向けの開発ガイド。v4.0.9: CLI Inspection, Source Code RAG, Claude Code Integration

**v4.0.9 Complete** (Nov 2025) - Session Auto-save, Code RAG, MCP Monitor ✅

---

## 🤖 For AI Assistants (Claude Code, Cursor, etc.)

### Kagura Coding Session Auto-Management Protocol

**IMPORTANT**: すべての開発作業でKagura Coding Sessionを使用してください。

#### 🚀 Auto-start Criteria (自動でセッション開始)

以下の場合、**必ず**セッションを開始:
- ユーザーが機能実装を依頼
- バグ修正を依頼
- コード変更を伴うタスク
- Issue番号が含まれる依頼

**開始方法:**
\`\`\`python
coding_start_session(
    user_id="kiyota",
    project_id="kagura-ai",
    description="[User's task description]",
    tags='["feature", "bug-fix", etc.]'
)
\`\`\`

#### 📝 Auto-track Criteria (自動で記録)

作業中、以下を**必ず**記録:
- ファイル編集/作成 → `coding_track_file_change()`
- エラー修正 → `coding_record_error()`
- 設計決定 → `coding_record_decision()`

**注意**: v4.0.9以降、これらはactive session必須です。

#### ✅ Auto-checkpoint (自動保存)

- ファイル変更ごとに自動保存される（v4.0.9）
- 手動チェックポイント: `coding_get_current_session_status()`

#### 🏁 Auto-end Criteria (自動で終了)

以下の場合、セッションを終了:
- タスク完了
- ユーザーが満足
- 次の変更予定なし

**終了方法:**
\`\`\`python
# ユーザーに確認してから:
coding_end_session(
    user_id="kiyota",
    project_id="kagura-ai",
    success='true',
    save_to_github='true'  # GitHub Issueに記録
)
\`\`\`

#### 💡 Example Auto-flow

\`\`\`
User: "Issue #510のバグを修正して"

Claude (自動実行):
1. 🤖 coding_start_session(description="Fix Issue #510 bug", tags=["bug-fix", "issue-510"])
2. [コード調査・修正]
3. 🤖 coding_track_file_change(file="src/memory.py", action="edit", reason="Fix #510")
4. 🤖 coding_record_error(error_type="AttributeError", solution="Added None check")
5. [テスト確認]
6. User: "動いた！"
7. 🤖 "セッションを終了しますか？" (確認)
8. User: "はい"
9. 🤖 coding_end_session(success='true', save_to_github='true')

Result: Issue #510に包括的なサマリーが自動投稿される
\`\`\`

#### ⚠️ Important Notes

- **Session必須**: track/record toolsはactive session必須（v4.0.9+）
- **確認必須**: end_session前にユーザー確認を取る
- **Auto-save**: ファイル変更ごとに進捗が自動保存される
- **検索可能**: 過去のセッションは`claude_code_search_past_work()`で検索可能

---

## 📋 プロジェクト概要

### v4.0の位置づけ

**Kagura AI v4.0** = **Universal AI Memory & Context Platform**

- **目標**: すべてのAIプラットフォーム（Claude, ChatGPT, Gemini等）で共有できるメモリー・コンテキスト管理
- **アプローチ**: MCP-native + REST API
- **特徴**: ローカル/セルフホスト/クラウド対応
- **現状**: Phase A/B/C完了、v4.0.0 stable準備中

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

## 🔄 作業フロー（Kagura Coding Session推奨）

```
1. Issue作成（必須）
   ↓
2. ブランチ作成（GitHub Issue経由）
   ↓
3. 🆕 Coding Session開始（Kagura MCP）
   coding_start_session(
       user_id="kiyota",
       project_id="kagura-ai",
       description="Implement Issue #XXX: ..."
   )
   ↓
4. 実装（TDD推奨）
   ├─ 重要な会話を記録: coding_track_interaction()
   ├─ ファイル変更を記録: coding_track_file_change()
   ├─ 設計決定を記録: coding_record_decision()
   └─ エラーを記録: coding_record_error()
   ↓
5. テスト（pytest, pyright, ruff）
   ↓
6. 🆕 Session終了 & GitHub記録
   coding_end_session(
       success=True,
       save_to_github=True  # GitHub Issueに自動記録
   )
   ↓
7. Draft PR作成
   ↓
8. CI通過 → Ready → Merge
```

**💡 Coding Session のメリット:**
- ✅ 作業内容が自動的にKaguraメモリーに保存
- ✅ 重要な決定・エラー解決法が検索可能に
- ✅ GitHub Issueに包括的サマリーを自動投稿
- ✅ セッション間でコンテキストが保持される
- ✅ `kagura coding sessions`でいつでも過去の作業を確認可能

### 🔍 過去の作業を参照（v4.0.8+）

実装開始前に、Kaguraメモリーから過去の知識を取得:

```bash
# 最近のセッション確認
kagura coding sessions --project kagura-ai --limit 10

# 過去の設計決定を確認
kagura coding decisions --project kagura-ai --tag architecture

# 似たようなエラーの解決法を検索
kagura coding errors --project kagura-ai --type TypeError

# セマンティック検索
kagura coding search --project kagura-ai --query "memory integration"
```

**重要**: Claudeの一時的なコンテキストだけに頼らず、**Kaguraメモリーを積極的に活用**してください。

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
│   ├── core/              # Memory, Graph
│   │   ├── memory/        # Memory Manager (4-tier)
│   │   └── graph/         # GraphMemory (NetworkX)
│   ├── api/               # REST API (FastAPI)
│   │   ├── auth.py        # API Key authentication (Phase C)
│   │   └── routes/        # /mcp, /api/v1/*
│   ├── mcp/               # MCP Server & Tools
│   │   ├── permissions.py # Tool access control (Phase C)
│   │   └── builtin/       # 31 MCP tools
│   ├── cli/               # CLI commands
│   │   ├── mcp.py         # MCP commands
│   │   ├── api_cli.py     # API key mgmt (Phase C)
│   │   └── memory_cli.py  # Export/import (Phase C)
│   └── tools/             # Optional tools
│
├── tests/                 # テスト (1,451+ passing)
├── docs/                  # ユーザードキュメント
├── ai_docs/               # 開発ドキュメント
├── examples/              # 使用例
│
├── docker-compose.yml           # 開発環境
├── docker-compose.prod.yml      # 本番環境 (Phase C)
├── Caddyfile                    # HTTPS reverse proxy (Phase C)
├── pyproject.toml
├── CLAUDE.md                    # このファイル
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

1. **🆕 Kaguraメモリーで過去の解決法を検索**
   ```bash
   kagura coding errors --project kagura-ai --type {ErrorType}
   kagura coding search --project kagura-ai --query "{error message}"
   ```

2. **エラーをCoding Memoryに記録**
   ```python
   coding_record_error(
       error_type="TypeError",
       message="...",
       solution="...",  # 解決後に追加
   )
   ```

3. **Issueにコメント**（または`save_to_github=True`で自動記録）

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
