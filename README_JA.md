# Kagura AI

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

> **Python-First AI Agent SDK**

本番環境対応のAIエージェントを1つのデコレータで構築。完全な型安全性、内蔵ツール、包括的なテストフレームワーク。

```bash
pip install kagura-ai[full]
```

---

## ⚡ クイックスタート（30秒）

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''{{ text }}を{{ lang }}に翻訳'''

result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

以上です。デコレータ1つ、型ヒント、完了。

---

## 🎯 なぜKagura AI？

### Python開発者向けに設計

| 必要な機能 | 他のSDK | Kagura AI |
|-----------|---------|-----------|
| **シンプルなAPI** | 50行以上の設定 | **デコレータ1つ** ✅ |
| **型安全性** | 実行時エラー | **pyright strict** ✅ |
| **メモリシステム** | 手動セットアップ | **内蔵** ✅ |
| **Web検索** | 外部プラグイン | **内蔵** ✅ |
| **コード実行** | 安全でない | **サンドボックス化** ✅ |
| **テスト** | DIY | **フレームワーク内蔵** ✅ |

### 本番環境向け設計

```python
from kagura import agent
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    keywords: list[str]
    confidence: float

@agent(enable_memory=True, tools=["web_search"])
async def analyzer(text: str) -> Analysis:
    '''{{ text }}の感情分析とキーワード抽出

    最新情報が必要ならweb_search(query)を使用
    '''

# 型安全、メモリ有効、Web接続
result = await analyzer("最新のAIトレンド")
print(result.sentiment)  # IDEの自動補完が効く！
```

---

## 🚀 主な機能

### 1. 1行でエージェント作成

```python
@agent
async def summarizer(text: str) -> str:
    '''3つのポイントで要約: {{ text }}'''
```

### 2. 型安全な構造化出力

```python
from pydantic import BaseModel

class Report(BaseModel):
    summary: str
    action_items: list[str]

@agent
async def meeting_analyzer(transcript: str) -> Report:
    '''会議分析: {{ transcript }}'''

report = await meeting_analyzer("...")
for item in report.action_items:  # 完全な型付き！
    print(f"TODO: {item}")
```

### 3. 内蔵ツール

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''{{ topic }}を調査:
    - web_search(query): Brave Search API
    - web_fetch(url): Webページ取得
    '''
```

内蔵ツール: ファイル操作、Web検索、コード実行、YouTube データなど。

### 4. メモリ管理

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''会話を記憶します

    ユーザー: {{ message }}'''

# 複数ターンの会話でコンテキスト保持
await assistant("好きな色は青です")
await assistant("私の好きな色は？")  # 記憶している！
```

### 5. カスタムツール

```python
from kagura import tool, agent

@tool
async def search_database(query: str) -> list[dict]:
    '''内部データベース検索'''
    return db.query(query)

@agent(tools=[search_database])
async def data_agent(question: str) -> str:
    '''データベースで回答: {{ question }}'''
```

### 6. マルチLLMサポート

```python
# OpenAI
@agent(model="gpt-4o")
async def translator(text: str) -> str: ...

# Anthropic
@agent(model="claude-3-5-sonnet-20241022")
async def writer(prompt: str) -> str: ...

# Google
@agent(model="gemini/gemini-2.0-flash")
async def analyzer(text: str) -> str: ...
```

LiteLLM統合で100以上のモデルをサポート。

---

## 💼 実世界のユースケース

### SDK統合例

#### Webアプリケーション（FastAPI）

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''カスタマーサポートの質問に回答: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}
```

#### データパイプライン

```python
from kagura import agent

@agent(tools=["web_search"])
async def data_enricher(company_name: str) -> dict:
    '''{{ company_name }}のデータ補完

    手順:
    1. Web検索で会社情報を収集
    2. 業界、規模、所在地、説明を抽出
    3. 構造化データとして返す
    '''

# ETLパイプラインで使用
enriched = await data_enricher("Anthropic")
```

#### 自動化スクリプト

```python
from kagura import agent, workflow

@agent
async def email_classifier(email: str) -> str:
    '''メール分類: urgent/important/spam

    Email: {{ email }}'''

@workflow.chain
async def inbox_automation(emails: list[str]):
    for email in emails:
        category = await email_classifier(email)
        # カテゴリに基づいてルーティング
```

---

## 🎨 高度な機能

### マルチモーダル分析

```python
@agent
async def image_analyzer(image_path: str, question: str) -> str:
    '''画像を分析して回答: {{ question }}

    画像: {{ image_path }}'''

result = await image_analyzer("chart.png", "トレンドは？")
# Gemini Vision APIを自動使用
```

### ドキュメントRAG

```python
from kagura.core.memory import MemoryRAG

@agent(enable_memory=True)
async def doc_qa(question: str) -> str:
    '''インデックス済みドキュメントから回答

    rag_search(query)で関連情報を検索
    '''

# 一度インデックス
rag = MemoryRAG()
await rag.index_directory("./docs")

# いつでもクエリ
answer = await doc_qa("Q3レポートに売上について何が書いてある？")
```

### エージェントテスト

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_translation(self):
        result = await translator("Hello", lang="ja")

        # セマンティックアサーション（LLM搭載）
        self.assert_semantic_match(
            result,
            "日本語の挨拶"
        )
```

### コスト追跡

```python
from kagura.observability import track_cost

@agent
@track_cost
async def expensive_agent(query: str) -> str:
    '''複雑な分析: {{ query }}'''

# 自動コスト追跡
# 表示: kagura monitor stats
```

---

## 🎮 ボーナス: 対話型チャット

コードを書かずに試したい？

```bash
kagura chat
```

すべての機能を内蔵したClaude Code風の体験：

```
[You] > report.pdfを読んで要約して

[AI] > (Gemini VisionでPDF分析)

      主な発見:
      1. 売上が前年比23%増
      2. 新市場拡大成功
      3. エンジニアチーム倍増

[You] > 類似レポートを検索

[AI] > (Brave Searchで関連コンテンツ検索)

[You] > 比較チャートを作成

[AI] > (Pythonコード記述、サンドボックスで実行、チャート表示)
```

ファイル操作、Web検索、コード実行、マルチモーダル分析がすべて自動で動作。

---

## 📦 インストール

### 基本

```bash
pip install kagura-ai
```

### 全機能（推奨）

```bash
pip install kagura-ai[full]  # メモリ + Web + マルチモーダル + 認証 + MCP
```

### 必要なものだけ

```bash
pip install kagura-ai[ai]    # メモリ + ルーティング + コンテキスト圧縮
pip install kagura-ai[web]   # Web検索 + マルチモーダル
pip install kagura-ai[auth]  # OAuth2
pip install kagura-ai[mcp]   # Claude Desktop統合
```

### 環境設定

```bash
# 最低1つのLLM APIキーが必要
export OPENAI_API_KEY=sk-...

# オプション機能
export BRAVE_SEARCH_API_KEY=...  # Web検索
export GOOGLE_API_KEY=...         # マルチモーダル（Gemini）
```

---

## 📚 ドキュメント

### 開発者向け（SDK）
- [APIリファレンス](docs/api/) - 全デコレータ、クラス、関数
- [SDKガイド](docs/sdk-guide.md) - @agent, @tool, memory, workflows
- [サンプル](./examples/) - 30以上のコード例

### ユーザー向け（Chat）
- [Chatガイド](docs/chat-guide.md) - 対話型チャット機能
- [クイックスタート](docs/quickstart.md) - 5分で開始

### 統合
- [MCP統合](docs/en/guides/claude-code-mcp-setup.md) - Claude Desktopセットアップ
- [テストガイド](docs/en/tutorials/14-testing.md) - エージェントのテスト

---

## 🏗️ アーキテクチャ

実績のある技術で構築:

- **LLM**: OpenAI SDK（直接）+ LiteLLM（100以上のプロバイダー）
- **メモリ**: ChromaDB（ベクトルストレージ）
- **バリデーション**: Pydantic v2
- **テスト**: pytest + カスタムフレームワーク
- **型安全性**: pyright strictモード

**品質指標**:
- 1,300以上のテスト（90%以上のカバレッジ）
- 100%型付け
- 本番環境対応

---

## 🔧 開発

```bash
# セットアップ
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras

# テスト
pytest -n auto

# 型チェック
pyright src/kagura/

# リント
ruff check src/
```

詳細は[CONTRIBUTING.md](./CONTRIBUTING.md)参照。

---

## 🗺️ ロードマップ

### 最近リリース（v2.7.x）
- ✅ ストリーミングサポート（90%高速化）
- ✅ ユーザー設定システム（`kagura init`）
- ✅ Personal tools（ニュース、天気、レシピ、イベント）
- ✅ MCP完全統合（15内蔵ツール）
- ✅ コンテキスト圧縮（10,000メッセージ対応）

### v3.0実装予定
- 🔄 ドキュメント刷新（SDK-first）
- 🔄 Meta Agent強化（Chat内`/create`）
- 🔄 コスト可視化（Chat内`/stats`）

### 将来（v3.1+）
- 🔮 自動検出とインテント認識
- 🔮 音声インターフェース
- 🔮 Google Workspace統合

---

## 📄 ライセンス

Apache License 2.0 - [LICENSE](./LICENSE)参照

---

## 🌸 名前の由来

「神楽（かぐら）」は日本の伝統芸能で、調和と創造性を体現 - このSDKの核心原理です。

---

**型安全なAIを求める開発者のために ❤️**

[GitHub](https://github.com/JFK/kagura-ai) • [PyPI](https://pypi.org/project/kagura-ai/) • [ドキュメント](https://www.kagura-ai.com/)
