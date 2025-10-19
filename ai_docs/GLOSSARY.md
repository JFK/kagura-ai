# Kagura AI 用語集 - v3.0

**Last Updated**: 2025-10-19
**Version**: v3.0

Kagura AI v3.0で使用される用語・略語の定義集。

---

## コア概念

### SDK (Software Development Kit)
Kagura AIの主要な位置づけ。Python開発者が既存アプリに組み込むライブラリ。

**用途**: FastAPI、データパイプライン、自動化スクリプト等への統合

### Agent (エージェント)
`@agent`デコレータで定義されたPython関数。LLMを呼び出し、型ヒントに基づいて自動的にレスポンスをパースする。

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
```

### Tool (ツール)
`@tool`デコレータで定義された関数。エージェントが使用できる機能（Web検索、ファイル操作等）。

```python
@tool
async def search_db(query: str) -> list[dict]:
    '''Search database'''
    return db.query(query)
```

### tool_registry
全ツールの統一管理システム。Chat、MCP、SDKのどのインターフェースからも同じツールが利用可能。

### Prompt Template
エージェント関数のdocstring内で使用されるJinja2テンプレート。

```python
'''Translate to {{ lang }}: {{ text }}'''
```

### Type-Based Parsing
関数の戻り値型ヒントに基づいて、LLMレスポンスを自動パースする機能。

**対応型**: str, int, float, bool, list[T], dict, Pydantic models

---

## v3.0機能

### Interactive Chat (対話型チャット)
`kagura chat`コマンドで起動するClaude Code風の対話環境。SDKの全機能を試せるボーナス機能。

**Note**: v3.0ではChatはボーナス機能として位置づけ（メインはSDK統合）

### Personal Tools
ChatやSDKで利用できる日常ツール（daily_news、weather_forecast、search_recipes、find_events）。

### Meta Agent
Chat内で`/create agent <description>`でカスタムエージェントを生成する機能。

### `/stats` Command
Chat内でトークン使用量とコストを表示するコマンド。

---

## 技術用語

### Pydantic v2
Pythonのデータバリデーションライブラリ。Kagura AIでは型パーサーとデータ検証に使用。

### LiteLLM
複数のLLMプロバイダ（OpenAI、Anthropic、Google等）を統一的に扱うライブラリ。

**Kagura AIのLLM統合**:
- OpenAI SDK: gpt-*, o1-* (直接、最速)
- Gemini SDK: gemini/* (直接、multimodal)
- LiteLLM: その他100+プロバイダ

### Jinja2
Pythonテンプレートエンジン。プロンプト内で変数埋め込み、ループ、条件分岐に使用。

### ChromaDB
ベクトルデータベース。Memory RAG、セマンティック検索に使用。

### MCP (Model Context Protocol)
Anthropic提唱のプロトコル。Claude DesktopでKaguraエージェントを使用可能に。

---

## 開発ツール

### pyright
Microsoft製の型チェッカー。Kagura AIは`--strict`モードで100%型安全性を保証。

### ruff
高速なPythonリンター・フォーマッター。

### pytest
Pythonテストフレームワーク。非同期テスト（`@pytest.mark.asyncio`）に対応。

### pytest-xdist
pytestの並列実行プラグイン。テストを60-80%高速化。

### uv
高速パッケージマネージャ。pip/poetryの代替。

---

## プロジェクト固有用語

### Kagura (神楽)
日本の伝統芸能。調和と創造性を象徴し、本SDKの設計思想の源泉。

### SDK-First
v3.0の設計哲学。Python SDKとしての統合を主目的とし、Chatは試用・実験用のボーナス機能として位置づけ。

**理由**: GitHub = エンジニア向けプラットフォーム

### Python-First Design
設定ファイル不要、Pythonコードのみでエージェントを定義する設計。

**特徴**:
- 型安全性（pyright strict）
- IDE補完
- リファクタリング容易
- バージョン管理

### Issue-Driven Development
GitHub Issueを起点とした開発フロー。全ての変更はIssueから始まる。

```
Issue作成 → Branch作成 → 実装 → Draft PR → CI → Merge
```

### Conventional Commits
コミットメッセージの標準形式。

```
<type>(<scope>): <subject> (#issue-number)

feat(core): implement feature (#XX)
fix(chat): fix bug (#XX)
docs(readme): update (#XX)
```

---

## CLI Commands

### kagura chat
対話型チャットを起動（Claude Code風）。

### kagura init
ユーザー設定をインタラクティブに設定（名前、場所、好み等）。

### kagura mcp serve
MCPサーバーを起動（Claude Desktop統合用）。

### kagura monitor stats
テレメトリデータ表示（実行回数、トークン、コスト）。

### Chat Commands (kagura chat内)

- `/help` - ヘルプ表示
- `/model <name>` - モデル切り替え
- `/create agent <desc>` - カスタムエージェント生成
- `/stats` - トークン・コスト表示
- `/save`, `/load` - セッション保存・読込
- `/exit` - 終了

---

## 略語

| 略語 | 正式名称 | 説明 |
|------|---------|------|
| **LLM** | Large Language Model | 大規模言語モデル (GPT-4, Claude, Gemini等) |
| **SDK** | Software Development Kit | ソフトウェア開発キット |
| **API** | Application Programming Interface | アプリケーション プログラミング インターフェース |
| **CLI** | Command Line Interface | コマンドライン インターフェース |
| **MCP** | Model Context Protocol | Anthropic提唱のプロトコル |
| **RAG** | Retrieval-Augmented Generation | 検索拡張生成 |
| **AST** | Abstract Syntax Tree | 抽象構文木 |
| **TDD** | Test-Driven Development | テスト駆動開発 |
| **CI/CD** | Continuous Integration/Delivery | 継続的インテグレーション/デリバリー |
| **PR** | Pull Request | プルリクエスト |
| **RFC** | Request for Comments | 技術仕様提案 |

---

## ディレクトリ略語

| パス | 説明 |
|------|------|
| `src/kagura/` | ソースコード |
| `tests/` | テストコード |
| `docs/` | ユーザードキュメント |
| `ai_docs/` | AI開発ドキュメント |
| `examples/` | SDK使用例 |
| `.github/workflows/` | CI/CD設定 |

---

## v3.0キーフレーズ

### "Python-First AI Agent SDK"
v3.0の正式名称。Pythonコードのみでエージェント構築、SDKとして統合。

### "SDK-first, Chat as bonus"
v3.0の設計哲学。SDK統合がメイン、Chatは試用・実験用。

### "One Decorator"
`@agent`デコレータ1つでAIエージェント作成。

### "Type-Safe"
pyright strict modeによる100%型安全性。

### "Production-Ready"
Memory、Tools、Testing等が標準装備。

---

## 参考資料

### 公式
- [GitHub](https://github.com/JFK/kagura-ai)
- [PyPI](https://pypi.org/project/kagura-ai/)
- [Documentation](https://www.kagura-ai.com/)

### 依存ライブラリ
- [Pydantic v2](https://docs.pydantic.dev/)
- [LiteLLM](https://docs.litellm.ai/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [Click](https://click.palletsprojects.com/)
- [Rich](https://rich.readthedocs.io/)
- [ChromaDB](https://www.trychroma.com/)

### プロトコル
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Last Updated**: 2025-10-19 (v3.0)
