# Kagura AI 用語集

## 概要

Kagura AIプロジェクトで使用される用語・略語の定義集です。Claude Codeやチームメンバーが一貫した用語を使用するための参照ドキュメントです。

---

## コア概念

### Agent (エージェント)
AIタスクを実行する自己完結型のモジュール。YAML設定で定義され、独立した状態管理を持つ。

### Atomic Agent (アトミックエージェント)
LLMを使用したタスク特化型エージェント。単一の明確な目的を持ち、構造化された出力を生成する。

**例**: テキスト要約エージェント、検索意図抽出エージェント

### Tool Agent (ツールエージェント)
LLMを使用しないデータ処理エージェント。高速な実行が求められるタスクに使用。

**例**: データフォーマット変換、API呼び出し、ファイル処理

### Workflow Agent (ワークフローエージェント)
複数のエージェントをオーケストレーションするエージェント。条件分岐、エラーハンドリング、状態共有を管理。

**例**: 複数ステップの検索パイプライン、マルチエージェント協調タスク

---

## 技術用語

### State (状態)
エージェント間で共有されるデータ構造。Pydanticモデルで型定義される。

```python
class AgentState(BaseModel):
    input: str
    output: Optional[str] = None
    metadata: dict[str, Any] = {}
```

### State Model (状態モデル)
エージェントの入出力データ構造を定義するYAMLファイル (`state_model.yml`)。

### LiteLLM
複数のLLMプロバイダ (OpenAI, Anthropic, Ollama等) を統一的に扱うためのライブラリ。

### LangGraph
エージェントワークフローをグラフ構造で管理するオーケストレーションライブラリ。

### Pydantic
Pythonのデータバリデーションライブラリ。型安全性を保証。

---

## YAML設定関連

### agent.yml
エージェントの設定ファイル。以下を定義:
- エージェント名
- ロール
- 使用するLLMモデル
- プロンプト
- ツール

### state_model.yml
エージェントの状態モデル定義ファイル。入出力のスキーマを記述。

### Custom Tools (カスタムツール)
エージェントに追加機能を提供するPython関数。`tools.py`に実装。

---

## CLI関連

### kagura
Kagura AIのコマンドラインインターフェース。

**主要コマンド**:
- `kagura chat`: 対話モード
- `kagura generate`: エージェント生成
- `kagura run`: エージェント実行

---

## プロジェクト固有用語

### Kagura (神楽)
日本の伝統芸能。調和、協調、創造性を象徴し、本プロジェクトの設計思想の源泉。

### Harmony (調和)
多様な技術を統合し、一貫したワークフローを実現する設計原則。

### Connection (協調)
エージェント間のシームレスな通信と状態共有を実現する設計原則。

### Creativity (創造性)
革新的なAIソリューションと伝統的な原則を融合させる設計原則。

---

## 開発・運用用語

### Issue Template (イシューテンプレート)
GitHub Issueの標準フォーマット。Claude Code最適化されたタスク定義を含む。

### Draft PR (ドラフトPR)
レビュー前のプルリクエスト。Claude Codeが作成するPRは常にDraftで開始。

### CI/CD
継続的インテグレーション/デリバリー。テスト・ビルド・デプロイの自動化。

### pre-commit hook
コミット前に自動実行されるチェック (lint, format, type check)。

---

## 略語

| 略語 | 正式名称 | 説明 |
|------|---------|------|
| **LLM** | Large Language Model | 大規模言語モデル (GPT-4, Claude等) |
| **AI** | Artificial Intelligence | 人工知能 |
| **CLI** | Command Line Interface | コマンドライン インターフェース |
| **YAML** | YAML Ain't Markup Language | 設定ファイル形式 |
| **API** | Application Programming Interface | アプリケーション プログラミング インターフェース |
| **PR** | Pull Request | プルリクエスト |
| **CI** | Continuous Integration | 継続的インテグレーション |
| **CD** | Continuous Delivery | 継続的デリバリー |
| **MCP** | Model Context Protocol | モデルコンテキストプロトコル |

---

## ディレクトリ・ファイル略語

| パス | 説明 |
|------|------|
| `src/` | ソースコード |
| `tests/` | テストコード |
| `docs/` | ユーザー向けドキュメント |
| `ai_docs/` | Claude Code向けドキュメント |
| `examples/` | サンプルコード |
| `.github/` | GitHub設定 (Issue Template, Workflows) |

---

## エラー関連

### ConfigurationError
設定ファイル (`agent.yml`, `state_model.yml`) の不正による例外。

### ValidationError
Pydanticモデルのバリデーション失敗による例外。

### LLMError
LLM呼び出し失敗 (APIエラー, タイムアウト等) による例外。

---

## よく使われるフレーズ

### "YAML-First Configuration"
コードではなくYAML設定でエージェントを定義する設計方針。

### "Type-Safe State Management"
Pydanticによる型安全な状態管理。

### "Multi-Agent Orchestration"
複数エージェントを協調動作させるワークフロー。

### "Modular and Decoupled"
疎結合で再利用可能なモジュール設計。

---

## 参考資料

- [Kagura AI公式ドキュメント](https://www.kagura-ai.com/)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## 更新ルール

- 新しい用語が追加されたら、このドキュメントを更新
- 略語は正式名称と合わせて記載
- 具体例を含めることで理解を促進
- 四半期ごとに見直し、古い用語を削除
