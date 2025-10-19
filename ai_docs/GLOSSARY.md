# Kagura AI 用語集

**最終更新**: 2025-10-04 (v2.0.0対応)

Kagura AIプロジェクトで使用される用語・略語の定義集です。Claude Codeやチームメンバーが一貫した用語を使用するための参照ドキュメントです。

---

## コア概念（v2.0.0）

### Agent (エージェント)
`@agent`デコレータで定義されたPython関数。LLMを呼び出し、型ヒントに基づいて自動的にレスポンスをパースする。

```python
@agent
async def translate(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
    pass
```

### Decorator-Based Agent (デコレータベースエージェント)
v2.0.0の設計哲学。YAMLではなくPythonデコレータでエージェントを定義する。

**v1.x（旧）**: YAML設定ファイル
**v2.0.0（新）**: `@agent` Pythonデコレータ

### Prompt Template (プロンプトテンプレート)
エージェント関数のdocstring内で使用されるJinja2テンプレート。引数を`{{ variable }}`で埋め込む。

```python
@agent
async def summarize(text: str, max_length: int = 100) -> str:
    '''Summarize the following text in {{ max_length }} words:

    {{ text }}
    '''
    pass
```

### Type-Based Parsing (型ベースパーサー)
関数の戻り値型ヒントに基づいて、LLMレスポンスを自動パースする機能。

**対応型**:
- `str`, `int`, `float`, `bool`
- `list[T]`, `dict[K, V]`
- Pydanticモデル
- `Optional[T]`, `Union[...]`

### CodeExecutor (コード実行エンジン)
安全にPythonコードを生成・実行するエンジン。AST検証、import制限、タイムアウト機能を持つ。

### REPL (Read-Eval-Print Loop)
`kagura repl`コマンドで起動するインタラクティブシェル。エージェントの定義・実行が可能。

---

## 技術用語

### Pydantic v2
Pythonのデータバリデーションライブラリ。Kagura AIでは型パーサーとデータ検証に使用。

**例**:
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''
    pass
```

### LiteLLM
複数のLLMプロバイダ（OpenAI、Anthropic、Google等）を統一的に扱うライブラリ。

**対応プロバイダ**:
- OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini 1.5, Gemini 2.0)
- その他（Ollama、Azure等）

### Jinja2
Pythonテンプレートエンジン。プロンプト内で変数埋め込み、ループ、条件分岐に使用。

```python
'''
{% for item in items %}
- {{ item }}
{% endfor %}
'''
```

### Click
PythonのCLIフレームワーク。`kagura`コマンドの実装に使用。

### Rich
ターミナルUIライブラリ。シンタックスハイライト、テーブル、プログレスバーに使用。

### pyright
Microsoft製の型チェッカー。Kagura AIは`--strict`モードで100%型安全性を保証。

### ruff
高速なPythonリンター・フォーマッター。PEP 8準拠をチェック。

### pytest
Pythonテストフレームワーク。非同期テスト（`@pytest.mark.asyncio`）に対応。

---

## プロジェクト固有用語

### Kagura (神楽)
日本の伝統芸能。調和、協調、創造性を象徴し、本プロジェクトの設計思想の源泉。

### Python-First Design
v2.0.0の設計哲学。YAMLではなくPythonコードでエージェントを定義する。

**理由**:
- 型安全性（pyright）
- IDE補完
- リファクタリング容易性
- バージョン管理

### Issue-Driven Development
GitHub Issueを起点とした開発フロー。全ての変更はIssueから始まる。

**フロー**:
```
Issue作成 → Claude Code実行 → Draft PR → CI → Review → Merge
```

### Draft PR (ドラフトPR)
レビュー前のプルリクエスト。全てのPRは最初Draftで作成される。

### Conventional Commits
コミットメッセージの標準形式。

```
<type>(<scope>): <subject> (#issue-number)

feat(core): implement @agent decorator (#20)
fix(executor): prevent import bypass (#21)
```

---

## RFC（Request for Comments）

### RFC-002: Multimodal RAG
画像・音声・PDFを含むマルチモーダルRAGチャット。v2.2.0で実装予定。

### RFC-003: Personal Assistant
使うほど賢くなるパーソナルAIアシスタント。v2.3.0で実装予定。

### RFC-004: Voice First Interface
音声入出力機能。v2.5.0+で実装予定。優先度: Medium

### RFC-005: Meta Agent
AIエージェントを作るAI。v2.4.0で実装予定。優先度: High

### RFC-006: Live Coding
リアルタイムペアプログラミング、Chat REPL。v2.1.0とv2.5.0で段階実装。優先度: High

### RFC-007: MCP Integration ⭐️
Model Context Protocol統合。v2.1.0で実装予定。優先度: **Very High**

### RFC-008: Plugin Marketplace
コミュニティエージェント共有プラットフォーム。v2.4.0で実装予定。優先度: High

### RFC-009: Multi-Agent Orchestration
複数エージェント協調システム。v2.4.0で実装予定。優先度: Medium-High

### RFC-010: Observability
エージェント可視化・コスト追跡。v2.5.0+で実装予定。優先度: Medium

### RFC-011: Scheduled Automation
Cron風スケジュール実行。v2.5.0+で実装予定。優先度: Medium

### RFC-012: Commands & Hooks
Markdownコマンド、PreToolUse/PostToolUse Hooks。v2.1.0で実装予定。優先度: High

### RFC-013: OAuth2 Auth
APIキー不要のブラウザ認証。v2.3.0で実装予定。優先度: Medium-High

### RFC-014: Web Integration
Web検索・スクレイピング。v2.2.0で実装予定。優先度: High

### RFC-015: Agent API Server
HTTP API経由でエージェント登録・実行。REST API、WebSocket、JWT認証。v2.6.0で実装予定。優先度: High

---

## CLI関連

### kagura
Kagura AIのコマンドラインインターフェース。

**v2.0.0で実装済みコマンド**:
- `kagura repl` - インタラクティブREPL
- `kagura --version` - バージョン表示

**v2.1.0以降で実装予定**:
- `kagura chat` - Chat REPL（RFC-006）
- `kagura mcp start` - MCPサーバー起動（RFC-007）
- `kagura auth login` - OAuth2ログイン（RFC-013）

### REPL内コマンド
- `/help` - ヘルプ表示
- `/agents` - 定義済みエージェント一覧
- `/exit` - REPL終了
- `/clear` - 画面クリア

---

## 開発・運用用語

### TDD (Test-Driven Development)
テスト駆動開発。Kagura AIでは実装前にテストを書くことを必須とする。

### Coverage (カバレッジ)
テストがコードのどれだけをカバーしているかの指標。

**目標**:
- 全体: 90%+
- コアモジュール: 95%+
- 新規実装: 100%

### Phase
開発のフェーズ。DEVELOPMENT_ROADMAP.mdで定義。

- **Phase 0**: 準備・環境整備
- **Phase 1**: Core Engine
- **Phase 2**: Code Execution
- **Phase 3**: CLI & REPL
- **Phase 4**: 統合・テスト
- **Phase 5**: リリース

### CI/CD
継続的インテグレーション/デリバリー。GitHub Actionsで自動化。

**実行内容**:
- pytest（全テスト）
- pyright（型チェック）
- ruff（リント）
- codecov（カバレッジ）

---

## 略語

| 略語 | 正式名称 | 説明 |
|------|---------|------|
| **LLM** | Large Language Model | 大規模言語モデル (GPT-4, Claude, Gemini等) |
| **AI** | Artificial Intelligence | 人工知能 |
| **CLI** | Command Line Interface | コマンドライン インターフェース |
| **API** | Application Programming Interface | アプリケーション プログラミング インターフェース |
| **PR** | Pull Request | プルリクエスト |
| **CI** | Continuous Integration | 継続的インテグレーション |
| **CD** | Continuous Delivery | 継続的デリバリー |
| **MCP** | Model Context Protocol | Anthropic提唱のモデルコンテキストプロトコル |
| **TDD** | Test-Driven Development | テスト駆動開発 |
| **REPL** | Read-Eval-Print Loop | 対話的実行環境 |
| **AST** | Abstract Syntax Tree | 抽象構文木（コード解析に使用） |
| **RFC** | Request for Comments | 技術仕様提案ドキュメント |

---

## ディレクトリ・ファイル略語

| パス | 説明 |
|------|------|
| `src/kagura/` | v2.0.0ソースコード（変更可能） |
| `src/kagura_legacy/` | v1.xレガシーコード（変更禁止） |
| `tests/` | v2.0.0テストコード |
| `tests/*_legacy/` | v1.xレガシーテスト（変更禁止） |
| `docs/` | ユーザー向けドキュメント（Phase 4で更新） |
| `ai_docs/` | Claude Code向けドキュメント |
| `ai_docs/rfcs/` | RFC仕様書 |
| `examples/` | サンプルコード（Phase 4で更新） |
| `.github/` | GitHub設定（Issue Template、Workflows） |

---

## エラー・例外クラス

### ValidationError
Pydanticモデルのバリデーション失敗による例外。

### LLMError
LLM呼び出し失敗（APIエラー、タイムアウト等）による例外。

### ExecutionError
CodeExecutor実行失敗による例外。

### TemplateError
Jinja2テンプレートのレンダリング失敗による例外。

---

## よく使われるフレーズ

### "Python-First Framework"
YAMLではなくPythonコードでエージェントを定義する設計方針（v2.0.0）。

### "Decorator-Based Design"
`@agent`デコレータによる宣言的なエージェント定義。

### "Type-Safe Agent Development"
pyrightによる100%型安全性の保証。

### "One-Line AI Transformation"
1行のデコレータで関数をAIエージェントに変換。

```python
@agent  # ← この1行
async def my_agent(query: str) -> str:
    '''{{ query }}'''
    pass
```

### "Issue-Driven AI Development"
GitHub IssueとClaude Codeによる開発フロー。

---

## バージョン対応表

| バージョン | リリース時期 | 主要機能 |
|-----------|-------------|---------|
| v2.0.0 | 2025 Q4 | Core、Executor、CLI、REPL |
| v2.1.0 | 2026 Q1 | MCP、Chat REPL、Commands & Hooks |
| v2.2.0 | 2026 Q2 | Multimodal RAG、Web統合 |
| v2.3.0 | 2026 Q3 | Personal AI、OAuth2 |
| v2.4.0 | 2026 Q4 | Meta Agent、Marketplace、Orchestration |
| v2.5.0+ | 2027 Q1+ | Voice、LSP、Observability、Automation |
| v2.6.0 | 2027 Q2 | API Server、REST/WebSocket、認証 |
| v2.7.0 | 2027 Q3 | Web UI、Dashboard、Marketplace UI |
| v2.8.0+ | 2027 Q4+ | SaaS化、マルチテナント、従量課金 |

詳細は`UNIFIED_ROADMAP.md`参照。

---

## 参考資料

### 公式ドキュメント
- [Kagura AI Website](https://www.kagura-ai.com/)
- [PyPI Package](https://pypi.org/project/kagura-ai/)
- [GitHub Repository](https://github.com/JFK/kagura-ai)

### 依存ライブラリ
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)

### 開発ツール
- [pytest Documentation](https://docs.pytest.org/)
- [pyright Documentation](https://microsoft.github.io/pyright/)
- [ruff Documentation](https://docs.astral.sh/ruff/)

### プロトコル・標準
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)

---

## 更新ルール

- 新しい用語が追加されたら、このドキュメントを更新
- 略語は正式名称と合わせて記載
- 具体例を含めることで理解を促進
- バージョンアップ時に古い用語を削除
- v2.0.0基準で記述（v1.x用語は削除済み）

---

**最終更新**: 2025-10-04 (v2.0.0対応)
