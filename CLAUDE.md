# Kagura AI 開発ガイド

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
```python
coding_start_session(
    user_id="kiyota",
    project_id="kagura-ai",
    description="[User's task description]",
    tags='["feature", "bug-fix", etc.]'
)
```

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
```python
# ユーザーに確認してから:
coding_end_session(
    user_id="kiyota",
    project_id="kagura-ai",
    success='true',
    save_to_github='true'  # GitHub Issueに記録
)
```

#### 💡 Example Auto-flow

```
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
```

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
- **現状**: v4.0.9 stable リリース済み

### v4.3.0の位置づけ

**Kagura AI v4.3.0** = **Code Quality & Organization Release**

- **目標**: コードベースの保守性・拡張性向上、技術的負債の解消
- **アプローチ**: 段階的リファクタリング（後方互換性100%維持）
- **特徴**:
  - **Phase 1 完了**: Utils統合（`utils/`と`cli/utils/`を`utils/`配下に統合）
  - **Phase 2 部分完了**: MCP Tool自動検出レジストリ実装
  - **Phase 3 完了**: Core Memory分割（`coding_memory.py` 2,116行 → 582行、72.5%削減）
  - **Phase 4 完了**: CLI Commands分割（`cli/mcp/`, `cli/memory/`, `cli/coding/`に再編）
  - **Phase 5 進行中**: 継続的改善（テスト90%+、型カバレッジ100%）
  - **Phase 6 進行中**: ドキュメント更新（本フェーズ）
- **成果**: ファイルサイズ50-75%削減、重複コード<5%、後方互換性100%
- **リリース予定**: 2025年11月
- **追跡**: [Issue #612](https://github.com/JFK/kagura-ai/issues/612)

### v4.3.0の位置づけ

**Kagura AI v4.3.0** = **Code Quality & Organization Release**

- **目標**: コードベースの保守性・拡張性向上、技術的負債の解消
- **アプローチ**: 段階的リファクタリング（後方互換性維持、Facade pattern活用）
- **特徴**:
  - 大規模ファイル分割（2000行超 → 500行目標）
  - コード重複削減（~15% → <5%）
  - Utils統合（`utils/`と`cli/utils/`の重複解消）
  - MCP Tool個別ファイル化（保守性・テスト性向上）
  - CLI高速化（起動時間1.2s → <500ms目標）
  - Core Memory リファクタリング（SessionManager等に分割）
- **リリース予定**: 2-3週間（11週間の段階的展開）
- **破壊的変更**: 最小限（2リリース期間のDeprecation警告付き）
- **追跡**: Issue #612（マスタートラッキング）

### 技術スタック

- **言語**: Python 3.11+
- **主要依存**: Pydantic v2, LiteLLM, FastAPI, NetworkX, ChromaDB
- **開発ツール**: pytest, pyright, ruff, uv

---

## 🎯 開発ルール

### 👨‍💻 コード品質基準

#### シニアエンジニアレベルの原則

Kagura AIは**プロダクションレベル**のコードベースです。以下の原則を**常に**遵守してください:

##### 🏗️ 設計原則

1. **SOLID原則の遵守**
   - **Single Responsibility**: 1クラス1責任
   - **Open/Closed**: 拡張に開いて、修正に閉じる
   - **Liskov Substitution**: 派生クラスは基底クラスと置換可能
   - **Interface Segregation**: インターフェースは最小限に
   - **Dependency Inversion**: 抽象に依存、具象に依存しない

2. **DRY (Don't Repeat Yourself)**
   - 重複コードは即座にリファクタリング
   - 共通ロジックは適切に抽象化
   - ただし、誤った抽象化（過度な汎用化）は避ける

3. **KISS (Keep It Simple, Stupid)**
   - 複雑さは必要最小限に
   - 「賢い」コードより「明快な」コードを優先
   - 将来の拡張性より現在の明瞭性

##### 🔍 実装品質

1. **型安全性**
   ```python
   # ❌ 悪い例
   def process(data):
       return data.get("value")
   
   # ✅ 良い例
   def process(data: dict[str, Any]) -> str | None:
       """Process data and extract value.
       
       Args:
           data: Input dictionary containing value
           
       Returns:
           Extracted value or None if not found
       """
       return data.get("value")
   ```

2. **エラーハンドリング**
   - 例外は適切にキャッチし、意味のあるメッセージを提供
   - ログレベルを適切に使い分け（DEBUG, INFO, WARNING, ERROR）
   - リソースリークを防ぐ（context manager使用）
   ```python
   # ✅ 良い例
   try:
       with open(file_path) as f:
           data = f.read()
   except FileNotFoundError:
       logger.error(f"File not found: {file_path}")
       raise
   except Exception as e:
       logger.error(f"Unexpected error reading {file_path}: {e}")
       raise
   ```

3. **パフォーマンス考慮**
   - O(n²)以上のアルゴリズムは要検討
   - データベースクエリはN+1問題に注意
   - 不要なファイルI/Oを避ける
   - 大量データ処理はジェネレーター/イテレーターを活用

4. **セキュリティ**
   - ユーザー入力は必ずバリデーション
   - SQLインジェクション、XSS対策
   - 機密情報のログ出力禁止
   - API keyは環境変数で管理

##### 📖 可読性・保守性

1. **命名**
   ```python
   # ❌ 悪い例
   x = get_data()
   def proc(d): ...
   
   # ✅ 良い例
   user_count = get_active_user_count()
   def process_user_data(data: UserData) -> ProcessedResult: ...
   ```
   - 変数名は意図を明確に: `x` → `user_count`
   - 関数名は動詞で開始: `process_user_data()`
   - boolean変数は`is_`, `has_`, `can_`で開始

2. **関数設計**
   - 1関数は最大50行（理想は20行以内）
   - 引数は最大5個（それ以上はオブジェクト化）
   - 副作用を最小化（純粋関数を優先）
   ```python
   # ✅ 良い例: 純粋関数
   def calculate_total(items: list[Item]) -> Decimal:
       """Calculate total price of items."""
       return sum(item.price for item in items)
   ```

3. **コメント**
   - **WHY**を説明（WHATはコードが説明すべき）
   - 複雑なロジックには必ず説明
   - TODOコメントにはIssue番号を記載
   ```python
   # ✅ 良い例
   # Use binary search here because dataset can be >1M records
   # and linear search would cause timeout (see Issue #123)
   index = binary_search(sorted_data, target)
   ```

##### 🧪 テストの質

1. **意味のあるテスト**
   ```python
   # ❌ カバレッジのためのテスト
   def test_add():
       assert add(1, 2) == 3
   
   # ✅ エッジケース・バリデーションのテスト
   def test_add_handles_overflow():
       """Test that add() raises ValueError on integer overflow."""
       with pytest.raises(ValueError, match="Integer overflow"):
           add(sys.maxsize, 1)
   
   def test_add_validates_input_types():
       """Test that add() rejects non-numeric inputs."""
       with pytest.raises(TypeError):
           add("1", 2)
   ```

2. **テストケース設計**
   - 正常系・異常系・境界値を網羅
   - テスト名は仕様書として読める: `test_user_creation_fails_with_duplicate_email()`
   - モック使用は最小限（実装依存を避ける）
   - Given-When-Then パターンを活用

##### ⚡ パフォーマンス最適化

- プロファイリング結果に基づいて最適化
- 早すぎる最適化は悪（まず動作、次に最適化）
- ボトルネックを特定してから対処
```python
# プロファイリング例
import cProfile
cProfile.run('expensive_function()', sort='cumtime')
```

##### 🔄 リファクタリング

- コードレビューで改善点を見つけたら即座に対応
- 「後でやる」は「やらない」と同義
- Boy Scout Rule: 来た時よりも美しく

#### ❌ 禁止事項

1. **ハードコーディング**
   ```python
   # ❌ 悪い例
   API_KEY = "sk-1234567890"
   DB_URL = "postgresql://localhost:5432/mydb"
   
   # ✅ 良い例
   API_KEY = os.getenv("API_KEY")
   DB_URL = os.getenv("DATABASE_URL")
   ```

2. **グローバル変数**
   - 必要な場合はシングルトンパターンを検討
   - 設定値は環境変数か設定ファイルへ

3. **過度な複雑さ**
   - 深いネスト（3階層まで）
   - 長大な関数（50行超）
   - 神クラス（500行超）

4. **不適切な依存**
   - 循環依存
   - テストコードへの本番コード依存

#### 📊 コードレビュー観点

Pull Request時に以下を自己チェック:

- [ ] 型ヒントが完全か？（`pyright --strict`通過）
- [ ] Docstringが明確か？（Google形式）
- [ ] テストが十分か（カバレッジ90%+、意味のあるテスト）？
- [ ] エラーハンドリングが適切か？
- [ ] パフォーマンス問題はないか？
- [ ] セキュリティ問題はないか？
- [ ] 命名が明確か？
- [ ] コメントが必要な複雑性はないか？
- [ ] リファクタリングの余地はないか?
- [ ] SOLID原則に従っているか？

**💡 原則**: 「6ヶ月後の自分が理解できるコード」を書く

---

### コーディング規約

- **命名**: `snake_case` (モジュール/関数), `PascalCase` (クラス)
- **型ヒント**: 必須（`pyright --strict`準拠）
- **Docstring**: Google形式、必須
- **テスト**: カバレッジ90%+、意味のあるテストケース

### コミットメッセージ（Conventional Commits）

```
<type>(<scope>): <subject> (#issue-number)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
**Scope**: `core`, `api`, `mcp`, `graph`, `cli`, `docs`

### ブランチ戦略

**詳細**: `.github/BRANCH_POLICY.md` を参照

#### ブランチ命名規則

**必須パターン**:
```
{issue-number}-{type}/{description}

例:
565-fix/integration-tests
550-feat/cli-utilities
563-docs/cleanup
```

**緊急修正のみ**: `hotfix/{description}` も許可（Issue後作成）

#### ワークフロー

```bash
# 1. Issue作成
gh issue create --title "..." --body "..."

# 2. Issueからブランチ作成（推奨）
gh issue develop [Issue番号] --checkout
# → 自動的に正しい命名でブランチ作成

# 3. 実装・テスト・コミット

# 4. Draft PR作成
gh pr create --draft --title "..." --body "..."

# 5. Ready & Merge
gh pr ready [PR番号]
gh pr merge [PR番号] --squash
```

#### 重要ルール

- **⛔️ mainへの直接コミット禁止** - Branch protection有効
- **📏 ブランチ寿命**: 最大7日（それ以上は分割）
- **🔄 毎日同期**: `git rebase origin/main` で最新に保つ
- **🗑️ マージ後削除**: 自動削除（GitHub設定）

#### マージ戦略

- **Squash merge**: feature, fix, docs, chore（通常）
- **Merge commit**: release branch（LTSのみ）

---

## 🔄 リファクタリング原則（v4.3.0追加）

### コード重複チェック

実装前に必ず確認:
```bash
# 類似コード検索
grep -r "def similar_function" src/
rg "class SimilarClass" src/

# 過去の実装検索（Kagura Memory活用）
kagura coding search --project kagura-ai --query "similar logic"
kagura coding sessions --project kagura-ai --limit 10
```

### ファイルサイズ制限

- **上限**: 800行（警告レベル）
- **目標**: 500行以下（推奨）
- **超過時の対応**:
  1. 責任を明確化（Single Responsibility Principle）
  2. 関連機能ごとにモジュール分割
  3. Facade patternで後方互換性維持（必要な場合）

**例**: `coding_memory.py` (2,116行) → `coding/session_manager.py`, `coding/file_tracker.py`等に分割

### Shared Utilities優先

- ❌ **避ける**: 各モジュールで重複実装
- ✅ **推奨**: `src/kagura/utils/`に共通化

**構造**:
```
utils/
├── cli/          # CLI専用ユーティリティ
├── memory/       # Memory関連ヘルパー
├── api/          # API関連ヘルパー
└── common/       # 共通ユーティリティ（JSON, errors, db等）
```

### リファクタリング時のチェックリスト

実装前:
- [ ] 類似コードが既存にないか検索
- [ ] 過去のKagura sessionsで類似作業がないか確認
- [ ] 既存のutilsで代替できないか確認

実装後:
- [ ] ファイルサイズが500行以下か（目標）
- [ ] テストカバレッジ90%+維持
- [ ] `pyright --strict`通過
- [ ] `ruff check src/`でエラーなし
- [ ] 後方互換性維持（破壊的変更がある場合はDeprecation警告）

### 段階的リファクタリング戦略

1. **Phase 1**: 低リスク（Utils統合、Prompt抽出）
2. **Phase 2**: 中リスク（MCP Tools分割、CLI整理）
3. **Phase 3**: 高リスク（Core Memory分割、Facade pattern適用）

**重要**: 各Phaseは独立してマージ可能。ロールバックも可能。

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
4. 🆕 過去の知識確認 & コード重複チェック（v4.3.0追加）
   ├─ 過去のセッション検索: kagura coding search --query "..."
   ├─ 類似コード検索: grep/rg で重複確認
   ├─ 既存utils確認: src/kagura/utils/ で代替可能か
   └─ リファクタリング機会: ファイルサイズ、重複コード確認
   ↓
5. 実装（TDD推奨）
   ├─ 重要な会話を記録: coding_track_interaction()
   ├─ ファイル変更を記録: coding_track_file_change()
   ├─ 設計決定を記録: coding_record_decision()
   ├─ エラーを記録: coding_record_error()
   └─ リファクタリング実施: 500行超なら分割検討
   ↓
6. テスト（pytest, pyright, ruff）
   ↓
7. 🆕 Session終了 & GitHub記録
   coding_end_session(
       success=True,
       save_to_github=True  # GitHub Issueに自動記録
   )
   ↓
8. Draft PR作成（v4.3.0: release branchへ）
   ↓
9. CI通過 → Ready → Merge
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

## 📁 プロジェクト構造

### v4.3.0での主要な変更点

**Utils統合** (Phase 1完了予定):
```
utils/                          # 🆕 統合されたユーティリティ
├── cli/                        # CLI専用（旧cli/utils/から移動）
│   ├── progress.py
│   ├── rich_helpers.py
│   └── time_formatters.py
├── memory/                     # Memory関連
│   └── factory.py
├── api/                        # API関連
│   └── check.py
└── common/                     # 共通
    ├── json_helpers.py
    ├── errors.py
    └── db.py
```

**MCP Tools再編** (Phase 2完了予定):
```
mcp/tools/                      # 🆕 Tool個別ファイル化（旧builtin/から移行）
├── coding/
│   ├── session.py              # start/end/resume/status
│   ├── file_tracking.py        # track_file_change
│   ├── error_tracking.py       # record_error, search_errors
│   └── ...
└── memory/
    ├── storage.py              # store, recall, delete
    ├── search.py               # search, search_ids, fetch
    └── ...
```

**Coding Memory分割** (Phase 3完了予定):
```
core/memory/coding/             # 🆕 CodingMemory分割
├── session_manager.py          # Session lifecycle
├── file_change_tracker.py      # File change recording
├── error_recorder.py           # Error tracking
├── decision_recorder.py        # Design decisions
└── github_integration.py       # GitHub Issue/PR
```

**CLI Commands再編** (Phase 4完了予定):
```
cli/commands/                   # 🆕 サブコマンド個別ファイル
├── mcp/
│   ├── serve.py
│   ├── stats.py
│   └── ...
└── memory/
    ├── store.py
    ├── search.py
    └── ...
```

---

### ディレクトリ構造

```
kagura-ai/
├── src/kagura/
│   ├── __init__.py
│   │
│   ├── agents/                    # Agent実装（ChatBot, Translator等）
│   │   ├── chatbot.py
│   │   ├── code_execution.py
│   │   ├── summarizer.py
│   │   └── translator.py
│   │
│   ├── api/                       # REST API (FastAPI)
│   │   ├── auth.py                # API Key authentication
│   │   ├── dependencies.py
│   │   ├── models.py
│   │   ├── routes/                # API endpoints
│   │   │   ├── graph.py           # Graph memory routes
│   │   │   ├── mcp_transport.py   # MCP-over-HTTP transport
│   │   │   ├── memory.py          # Memory CRUD routes
│   │   │   ├── models.py          # LLM model routes
│   │   │   ├── search.py          # Search routes
│   │   │   └── system.py          # Health check, info
│   │   └── server.py
│   │
│   ├── auth/                      # OAuth2 authentication
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── oauth2.py
│   │
│   ├── builder/                   # Agent builder (meta-programming)
│   │   ├── agent_builder.py
│   │   └── config.py
│   │
│   ├── builtin/                   # Built-in tools
│   │   ├── file.py                # File operations
│   │   ├── git.py                 # Git operations
│   │   ├── github_agent.py
│   │   ├── shell.py               # Shell command execution
│   │   └── shell_agent.py
│   │
│   ├── chat/                      # Interactive chat interface
│   │   ├── command_fixer.py       # Command auto-correction
│   │   ├── completer.py           # Auto-completion
│   │   ├── display.py             # Rich display
│   │   ├── session.py             # Chat session management
│   │   ├── shell_tool.py
│   │   ├── stats.py
│   │   ├── tools.py
│   │   └── utils.py
│   │
│   ├── cli/                       # CLI commands (v4.3.0: モジュール化)
│   │   ├── mcp/                   # 🆕 MCP commands (Phase 4)
│   │   │   ├── __init__.py
│   │   │   ├── serve.py
│   │   │   ├── stats.py
│   │   │   ├── tools.py
│   │   │   └── doctor.py
│   │   ├── memory/                # 🆕 Memory commands (Phase 4)
│   │   │   ├── __init__.py
│   │   │   ├── store.py
│   │   │   ├── search.py
│   │   │   ├── delete.py
│   │   │   └── export.py
│   │   ├── coding/                # 🆕 Coding commands (Phase 4)
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py
│   │   │   ├── errors.py
│   │   │   └── decisions.py
│   │   ├── api_cli.py             # API key management
│   │   ├── auth_cli.py            # OAuth2 authentication
│   │   ├── chat.py                # Chat interface
│   │   ├── config_cli.py          # Configuration management
│   │   ├── doctor.py              # System diagnostics
│   │   ├── init.py                # Project initialization
│   │   ├── lazy.py                # Lazy loading utilities
│   │   ├── main.py                # CLI entry point
│   │   └── telemetry_cli.py       # Telemetry commands
│   │
│   ├── commands/                  # Command pattern implementation
│   │   ├── command.py
│   │   ├── executor.py
│   │   ├── hook_decorators.py
│   │   ├── hooks.py
│   │   └── loader.py
│   │
│   ├── config/                    # Configuration management
│   │   ├── env.py                 # Environment variables
│   │   ├── manager.py             # Config manager
│   │   ├── memory_config.py       # Memory configuration
│   │   ├── models.py              # Config models
│   │   ├── paths.py               # Path utilities
│   │   └── project.py             # Project-specific config
│   │
│   ├── core/                      # Core functionality
│   │   ├── cache.py               # Caching layer
│   │   ├── compression/           # Context compression (v4.0.9)
│   │   │   ├── exceptions.py
│   │   │   ├── manager.py
│   │   │   ├── monitor.py
│   │   │   ├── policy.py
│   │   │   └── token_counter.py
│   │   ├── decorators.py
│   │   ├── executor.py
│   │   ├── graph/                 # Graph memory (NetworkX)
│   │   │   └── memory.py
│   │   ├── llm.py                 # LLM abstraction (LiteLLM)
│   │   ├── llm_gemini.py          # Gemini-specific
│   │   ├── llm_openai.py          # OpenAI-specific
│   │   ├── memory/                # 3-tier memory system (v4.4.0: Working Memory removed)
│   │   │   ├── README.md
│   │   │   ├── bm25_search.py     # BM25 keyword search
│   │   │   ├── coding/            # 🆕 Coding memory (Phase 3: 2,116行 → 8モジュール)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── session_manager.py      # Session lifecycle
│   │   │   │   ├── file_change_tracker.py  # File change tracking
│   │   │   │   ├── error_recorder.py       # Error recording
│   │   │   │   ├── decision_recorder.py    # Design decisions
│   │   │   │   ├── interaction_tracker.py  # AI-User interactions
│   │   │   │   ├── github_integration.py   # GitHub Issue/PR integration
│   │   │   │   ├── search.py               # Session search & retrieval
│   │   │   │   └── models.py               # Pydantic models
│   │   │   ├── coding_dependency.py  # Code dependency analysis
│   │   │   ├── coding_memory.py   # Coding memory (Facade、Phase 3で582行に削減)
│   │   │   ├── context.py         # Context management
│   │   │   ├── embeddings.py      # Embedding generation
│   │   │   ├── export.py          # Memory export/import
│   │   │   ├── github_recorder.py # GitHub integration (deprecated → coding/github_integration.py)
│   │   │   ├── hybrid_search.py   # Hybrid search (BM25+RAG)
│   │   │   ├── interaction_tracker.py  # AI-User interaction
│   │   │   ├── lexical_search.py  # Lexical search
│   │   │   ├── manager.py         # Memory manager (main)
│   │   │   ├── memory_abstractor.py  # Memory abstraction
│   │   │   ├── models/
│   │   │   │   └── coding.py      # Coding models (deprecated → coding/models.py)
│   │   │   ├── multimodal_rag.py  # Multimodal RAG
│   │   │   ├── neural/            # Neural memory network
│   │   │   │   ├── activation.py   # Activation tracking
│   │   │   │   ├── co_activation.py  # Co-activation patterns
│   │   │   │   ├── config.py
│   │   │   │   ├── decay.py        # Memory decay
│   │   │   │   ├── engine.py       # Neural engine
│   │   │   │   ├── hebbian.py      # Hebbian learning
│   │   │   │   ├── models.py
│   │   │   │   ├── scoring.py      # Relevance scoring
│   │   │   │   └── utils.py
│   │   │   ├── persistent.py      # Persistent (disk) memory
│   │   │   ├── rag.py             # RAG (ChromaDB)
│   │   │   ├── recall_scorer.py   # Recall scoring
│   │   │   ├── reranker.py        # Result reranking
│   │   │   └── working.py         # Working (RAM) memory
│   │   ├── model_selector.py
│   │   ├── parallel.py            # Parallel execution
│   │   ├── parser.py
│   │   ├── prompt.py
│   │   ├── registry.py
│   │   ├── shell.py
│   │   ├── shell_safety.py        # Shell command safety
│   │   ├── streaming.py
│   │   ├── tool_registry.py
│   │   ├── workflow.py
│   │   └── workflow_registry.py
│   │
│   ├── exceptions.py              # Global exceptions
│   │
│   ├── llm/                       # LLM utilities
│   │   ├── coding_analyzer.py     # Code analysis with LLM
│   │   ├── prompts.py             # Prompt templates
│   │   └── vision.py              # Vision capabilities
│   │
│   ├── loaders/                   # Data loaders
│   │   ├── cache.py
│   │   ├── directory.py           # Directory scanning
│   │   ├── file_types.py          # File type detection
│   │   └── gemini.py              # Gemini File API
│   │
│   ├── mcp/                       # MCP Server & Tools (34+ tools)
│   │   ├── builtin/               # Built-in MCP tools
│   │   │   ├── academic.py        # arXiv search
│   │   │   ├── brave_search.py    # Brave Search API
│   │   │   ├── cache.py           # Cache management
│   │   │   ├── coding.py          # Coding memory tools (20+)
│   │   │   ├── common.py
│   │   │   ├── fact_check.py      # Fact checking
│   │   │   ├── file_ops.py        # File operations
│   │   │   ├── github.py          # GitHub CLI integration
│   │   │   ├── media.py           # Media file handling
│   │   │   ├── memory.py          # Memory tools (10+)
│   │   │   ├── meta.py            # Meta-agent tools
│   │   │   ├── multimodal.py      # Multimodal RAG
│   │   │   ├── observability.py   # Telemetry tools
│   │   │   ├── routing.py         # Query routing
│   │   │   ├── web.py             # Web scraping
│   │   │   └── youtube.py         # YouTube tools
│   │   ├── config.py
│   │   ├── diagnostics.py         # MCP diagnostics
│   │   ├── permissions.py         # Tool access control
│   │   ├── schema.py
│   │   ├── server.py              # MCP server implementation
│   │   └── tool_classification.py
│   │
│   ├── meta/                      # Meta-agent (self-improvement)
│   │   ├── error_analyzer.py
│   │   ├── fixer.py
│   │   ├── generator.py
│   │   ├── meta_agent.py
│   │   ├── parser.py
│   │   ├── self_improving.py
│   │   ├── spec.py
│   │   ├── templates/             # Agent templates
│   │   │   ├── agent_base.py.j2
│   │   │   ├── agent_with_code_exec.py.j2
│   │   │   ├── agent_with_memory.py.j2
│   │   │   └── agent_with_tools.py.j2
│   │   └── validator.py
│   │
│   ├── observability/             # Telemetry & monitoring
│   │   ├── collector.py           # Data collection
│   │   ├── dashboard.py           # Dashboard
│   │   ├── instrumentation.py     # Instrumentation
│   │   ├── pricing.py             # Cost tracking
│   │   └── store.py               # Data storage
│   │
│   ├── routing/                   # Query routing
│   │   ├── exceptions.py
│   │   └── router.py
│   │
│   ├── testing/                   # Testing utilities
│   │   ├── mocking.py
│   │   ├── plugin.py              # pytest plugin
│   │   ├── testcase.py
│   │   └── utils.py
│   │
│   ├── tools/                     # Tool utilities
│   │   └── __init__.py
│   │
│   ├── utils/                     # 🆕 Shared utilities (v4.3.0: Phase 1統合)
│   │   ├── cli/                   # CLI専用ユーティリティ (旧cli/utils/から移動)
│   │   │   ├── __init__.py
│   │   │   ├── progress.py        # Progress indicators
│   │   │   ├── rich_helpers.py    # Rich console formatting
│   │   │   └── time_formatters.py # Time display utilities
│   │   ├── memory/                # Memory関連ヘルパー
│   │   │   ├── __init__.py
│   │   │   └── factory.py         # MemoryManager factory
│   │   ├── api/                   # API関連ヘルパー
│   │   │   ├── __init__.py
│   │   │   └── check.py           # API connectivity testing
│   │   ├── common/                # 共通ユーティリティ
│   │   │   ├── __init__.py
│   │   │   ├── json_helpers.py    # JSON serialization
│   │   │   ├── errors.py          # Unified error handling
│   │   │   ├── db.py              # Database helpers
│   │   │   └── metadata.py        # Metadata extraction
│   │   └── media_detector.py      # Media file detection
│   │
│   ├── version.py
│   │
│   └── web/                       # Web scraping & search
│       ├── decorators.py
│       ├── scraper.py
│       └── search.py
│
├── tests/                         # テスト (1,451+ passing)
├── docs/                          # ユーザードキュメント
├── ai_docs/                       # 開発ドキュメント
├── examples/                      # 使用例
│
├── docker-compose.yml             # 開発環境
├── docker-compose.prod.yml        # 本番環境
├── Caddyfile                      # HTTPS reverse proxy
├── pyproject.toml
├── CLAUDE.md                      # このファイル
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

- **ユニットテスト**: 各関数・クラス
- **統合テスト**: モジュール間連携
- **エッジケース**: 境界値
- **エラーハンドリング**: 例外処理
- **パフォーマンステスト**: ボトルネック検証

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
       stack_trace="...",
       solution="...",  # 解決後に追加
   )
   ```

3. **Issueにコメント**（または`save_to_github=True`で自動記録）

4. **解決後にドキュメント更新**

---

## 📚 重要なドキュメント

### 開発前に確認

1. **Issue内容**（必読）
2. `ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md` - v4.0ロードマップ
3. `ai_docs/V4.0_STRATEGIC_PIVOT.md` - v4.0戦略方針
4. `ai_docs/CODING_STANDARDS.md` - コーディング規約
5. `ai_docs/ARCHITECTURE.md` - アーキテクチャ
6. `ai_docs/MEMORY_STRATEGY.md` - メモリー戦略

### 参考リンク

- **API仕様**: `docs/api-reference.md`, `docs/api/reference.yaml`
- **CHANGELOG**: `CHANGELOG.md`
- **README**: `README.md`

---

## 💡 開発のベストプラクティス

### 実装開始前

1. **Issue確認**: 目的と要件を理解
2. **過去の作業検索**: Kaguraメモリーで類似実装を確認
3. **設計検討**: アーキテクチャへの影響を評価
4. **テスト計画**: テストケースを先に考える（TDD）

### 実装中

1. **小さく分割**: 1コミット1機能
2. **頻繁にコミット**: 動作する状態を保つ
3. **継続的テスト**: pytest watch mode活用
4. **メモリー記録**: 重要な決定・エラーを記録

### 実装後

1. **自己レビュー**: コードレビュー観点をチェック
2. **ドキュメント更新**: README、docstring、CHANGELOG
3. **CI確認**: すべてのテストが通ることを確認
4. **Session終了**: Kagura sessionを適切に終了

---

**このガイドに従って、プロダクションレベルの高品質なコードを生成してください。不明点は必ず質問してください！**
