# Kagura AI

![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

**メモリ、ルーティング、マルチモーダルRAG搭載のProduction-Ready AIエージェントフレームワーク**

Kagura AI は、シンプルさと開発者体験に焦点を当てたproduction-readyフレームワークです。一つの`@agent`デコレータで、あらゆる Python 関数を AI エージェントに変換し、メモリ管理、インテリジェントルーティング、マルチモーダルRAG、コンテキスト圧縮などの高度な機能を活用できます。

---

## ✨ 特徴

### コアフレームワーク
- **@agent デコレータ**: 1行で AI エージェントを作成
- **@tool デコレータ**: Python関数を呼び出し可能なツールに変換 ⭐️ NEW
- **@workflow デコレータ**: マルチエージェントオーケストレーション ⭐️ NEW
- **Jinja2 テンプレート**: docstring 内での強力なプロンプトテンプレート
- **型ベース解析**: 型ヒントを使用した自動レスポンス解析
- **Pydantic モデル**: 構造化された出力のファーストクラスサポート
- **コード実行**: 安全な Python コード生成・実行
- **インタラクティブ REPL**: `kagura repl` で高速プロトタイピング
- **Chat REPL**: `kagura chat` でプリセットエージェント利用 ⭐️ NEW
- **マルチ LLM サポート**: [LiteLLM](https://github.com/BerriAI/litellm) 経由で OpenAI、Anthropic、Google などをサポート

### 高度な機能
- **メモリ管理**: 3層メモリシステム（Context/Persistent/RAG）、ChromaDBによるセマンティック検索
- **エージェントルーティング**: Intent/Semantic/Memory-Aware戦略によるインテリジェントルーティング
- **マルチモーダルRAG**: Gemini API + ChromaDBで画像、PDF、音声、動画をインデックス・検索
- **Web統合**: Brave Search + DuckDuckGo + Webスクレイピングでリアルタイム情報取得
- **コンテキスト圧縮**: 長時間会話のための効率的なトークン管理
- **MCP統合**: Claude DesktopでKaguraエージェントを直接使用
- **Shell統合**: Git自動化を含むセキュアなシェルコマンド実行
- **カスタムコマンド**: YAMLフロントマター付きMarkdownファイルで再利用可能なAIタスクを定義
- **テストフレームワーク**: セマンティックアサーションとモッキング機能を内蔵
- **Observability**: テレメトリ、コスト追跡、パフォーマンス監視

## 🚀 クイックスタート

### インストール

```bash
# 基本インストール
pip install kagura-ai

# AI機能付き（メモリ、ルーティング、コンテキスト圧縮）
pip install kagura-ai[ai]

# Web＆マルチモーダル（画像、PDF、音声、動画、Web検索）
pip install kagura-ai[web]

# OAuth2認証
pip install kagura-ai[auth]

# 全機能（推奨）
pip install kagura-ai[full]
```

**詳細は[インストールガイド](https://www.kagura-ai.com/en/installation/)を参照してください。**

### 基本的な例

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''{{ name }}に挨拶する'''
    pass

# エージェントを実行
result = await hello("世界")
print(result)  # "こんにちは、世界！"
```

### Pydantic を使った構造化出力

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''次のテキストから人物情報を抽出: {{ text }}'''
    pass

result = await extract_person("アリスは30歳で、ソフトウェアエンジニアとして働いています")
print(f"{result.name}, {result.age}, {result.occupation}")
# 出力: アリス, 30, ソフトウェアエンジニア
```

### メモリ管理

```python
from kagura import agent

@agent(enable_memory=True)
async def chat_with_memory(message: str) -> str:
    '''あなたは親切なアシスタントです。会話を記憶してください。
    ユーザーメッセージ: {{ message }}'''
    pass

# メモリは呼び出し間で永続化
await chat_with_memory("私の名前はアリスです")
await chat_with_memory("私の名前は何ですか？")  # "あなたの名前はアリスです"
```

### MCP統合（Claude Desktop）

Kaguraエージェントを Claude Desktop で直接使用：

```bash
# MCPサーバー起動
kagura mcp serve

# Claude Desktop設定（macOS）
# ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "kagura-ai": {
      "command": "kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

Claude Desktop内でエージェントと対話できます！

### Observability

```bash
# テレメトリ監視（自動記録）
kagura monitor list    # 最近の実行
kagura monitor stats   # 統計
kagura monitor cost    # コスト分析
```

すべての`@agent`実行が自動的に記録されます（v2.5.5）

## 📚 ドキュメント

- [完全なドキュメント](https://www.kagura-ai.com/)
- [API リファレンス](https://www.kagura-ai.com/en/api/)
- [サンプルコード](./examples/)
- [コントリビューションガイド](./CONTRIBUTING_JA.md)

## 🎯 最新アップデート

最新機能:
- **自動テレメトリ**: 全@agent実行を自動追跡（v2.5.5）
- **統合MCPサーバー**: 単一設定で全機能をClaude Desktopから利用（v2.5.4）
- **15個のBuilt-in MCPツール**: Memory、Web、File、Observability、Meta、Multimodal
- **高速CLI起動**: Lazy loadingで98.7%高速化（8.8秒 → 0.1秒）（v2.5.3）
- **コンテキスト圧縮**: トークンカウントとコンテキストウィンドウ管理
- **Memory-Aware Routing**: 会話コンテキストによるインテリジェントルーティング
- **テストフレームワーク**: セマンティックアサーション付きAgentTestCase
- **36個の包括的なサンプル**: 基本から実世界のアプリケーションまで8カテゴリ

## 🎯 2.0の新機能

Kagura AI 2.0 は 1.x からの**完全な再設計**です：

### 以前 (1.x)
```yaml
# agent.yml
type: atomic
llm:
  model: gpt-4
prompt:
  - language: ja
    template: "あなたは親切なアシスタントです"
```

### 現在 (2.0+)
```python
@agent
async def assistant(query: str) -> str:
    '''あなたは親切なアシスタントです。質問に答えて: {{ query }}'''
    pass
```

**主な変更点:**
- **Python ファースト**: YAML 設定が不要
- **シンプルな API**: 複雑な設定の代わりに1つのデコレータ
- **型安全性**: 完全な型ヒントと Pydantic サポート
- **コード実行**: 安全なコード生成・実行機能を内蔵
- **優れた DX**: 高速開発のためのインタラクティブ REPL

## 🤝 コントリビューション

コントリビューションを歓迎します！ガイドラインについては [CONTRIBUTING_JA.md](./CONTRIBUTING_JA.md) を参照してください。

### 開発環境のセットアップ

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --dev
```

テストの実行:
```bash
pytest
```

型チェック:
```bash
pyright
```

## 📄 ライセンス

Apache License 2.0 - 詳細は [LICENSE](./LICENSE) を参照

## 🙏 謝辞

Kagura AI は日本の伝統芸能「神楽（かぐら）」にちなんで名付けられ、調和、つながり、創造性の原理を体現しています。

---

Kagura AI コミュニティが ❤️ を込めて開発
