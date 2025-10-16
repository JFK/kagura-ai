# Kagura AI

[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)](https://pypi.org/project/kagura-ai/)
[![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)](https://codecov.io/gh/JFK/kagura-ai)
[![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)](https://github.com/JFK/kagura-ai/actions)

> **Pythonコード1行で本格的なAIエージェントを構築**

Kagura AIは、メモリ管理、Web検索、コード実行、マルチモーダル分析など、実用的な機能をすべて内蔵した、最もシンプルなAIエージェントフレームワークです。

**Kagura AIを選ぶ3つの理由:**
1. 🎯 **最もシンプルなAPI** - デコレータ1つ、型ヒント、以上
2. 🚀 **本番環境対応** - メモリ、Web、マルチモーダルが標準装備
3. 💡 **最高の開発体験** - 対話型チャット、完全な型安全性、1,300以上のテスト

```bash
pip install kagura-ai[full]
```

[ドキュメント](https://www.kagura-ai.com/) • [サンプル](./examples/) • [APIリファレンス](https://www.kagura-ai.com/en/api/)

---

## ⚡ クイックスタート

### 最初のエージェント（30秒）

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''{{ text }}を{{ lang }}に翻訳'''

result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

以上です。設定ファイルも複雑なセットアップも不要 - Pythonだけ。

### 対話型チャット（Claude Code体験）

```bash
kagura chat
```

試してみましょう：
```
[You] > report.pdfを読んで3つのポイントにまとめて

[AI] > (GeminiでPDFを分析、要約を提供)

[You] > 類似レポートをWeb検索して

[AI] > (Brave Searchで関連コンテンツを検索)

[You] > この画像を分析: chart.png

[AI] > (Geminiで画像を分析)
```

ファイル操作、Web検索、マルチモーダル分析がすべて自動で動作します。

---

## 🌟 なぜKagura AI？

### 他フレームワークとの比較

| 機能 | LangChain | AutoGen | CrewAI | **Kagura AI** |
|-----|-----------|---------|--------|--------------|
| **セットアップの簡単さ** | 50行以上 | 30行以上 | YAML設定 | **デコレータ1つ** ✅ |
| **型安全性** | ❌ なし | ❌ なし | ❌ なし | **✅ 完全（pyright strict）** |
| **コード実行** | ⚠️ 手動 | ⚠️ 限定的 | ❌ なし | **✅ サンドボックス内蔵** |
| **メモリシステム** | ⚠️ 手動 | ⚠️ 基本的 | ⚠️ 基本的 | **✅ 3層（Context/Persistent/RAG）** |
| **Web検索** | ⚠️ プラグイン | ❌ なし | ⚠️ 限定的 | **✅ 標準装備（Brave + DDG）** |
| **マルチモーダル** | ⚠️ 手動 | ❌ なし | ❌ なし | **✅ 標準装備（Gemini）** |
| **テストフレームワーク** | ⚠️ 手動 | ❌ なし | ❌ なし | **✅ 内蔵（AgentTestCase）** |
| **対話型チャット** | ❌ なし | ❌ なし | ❌ なし | **✅ Claude Code風** |

### Kagura AIの違い

#### 1. 真のPython-First

**他のフレームワーク:**
```yaml
# config.yaml - 20行以上
agent:
  name: my_agent
  llm:
    provider: openai
    model: gpt-4
  tools: [web_search, calculator]
  memory:
    type: chromadb
    config: {...}
```

**Kagura AI:**
```python
@agent(enable_memory=True, tools=["web_search"])
async def my_agent(query: str) -> str:
    '''{{ query }}に答えて'''
```

#### 2. 型安全な構造化出力

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    keywords: list[str]
    score: float

@agent
async def analyze(text: str) -> Analysis:
    '''分析: {{ text }}'''

result = await analyze("Pythonが大好き！")
print(result.sentiment)  # 型安全！IDEの自動補完が効く！
```

#### 3. 本格的な本番機能

多くのフレームワークで手動統合が必要な機能：
- ❌ メモリ管理
- ❌ Web検索
- ❌ 画像/PDF分析
- ❌ コード実行

**Kagura AIではすべて標準装備:**

```python
@agent(
    enable_memory=True,        # 3層メモリ
    tools=["web_search"],       # Web検索内蔵
    enable_code_execution=True  # 安全なサンドボックス
)
async def research_agent(topic: str) -> str:
    '''{{ topic }}を調査。以下が可能:
    - 会話を記憶
    - Webで最新情報を検索
    - データ分析用のPythonコードを実行
    '''
```

---

## 🎨 実際の動作

### 例1: コード実行によるデータ分析

```python
@agent
async def data_analyst(question: str, csv_path: str) -> str:
    '''{{ csv_path }}を分析して{{ question }}に答えて

    pandas、matplotlib、numpyを使ったPythonコードが書けます。
    '''

result = await data_analyst("売上のトレンドは？", "sales.csv")
# AIがpandasコードを書いて実行、グラフ付きで洞察を返す
```

### 例2: マルチモーダルRAG（画像+PDF）

```python
@agent(enable_memory=True)
async def document_qa(question: str) -> str:
    '''./docs/内のドキュメントに基づいて回答

    利用可能なツール:
    - rag_search(query): インデックス済みドキュメントを検索（PDF、画像）
    '''

# ドキュメントを一度インデックス
from kagura.core.memory import MemoryRAG
rag = MemoryRAG()
await rag.index_directory("./docs")

# 質問する
result = await document_qa("Q3レポートのPDF内の図は何を示していますか？")
# AIがPDFと画像を検索、図を見つけてGeminiで分析
```

### 例3: Web調査エージェント

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''{{ topic }}を調査

    手順:
    1. Webで最新情報を検索
    2. 関連ページを取得・分析
    3. 発見事項を統合
    '''

result = await researcher("Python 3.13の新機能")
# AIがWebを検索、記事を読み、発見事項をまとめる
```

### 例4: メモリを持つ会話

```python
@agent(enable_memory=True, memory_scope="session")
async def assistant(message: str) -> str:
    '''あなたは親切なアシスタントです。会話を記憶してください。

    ユーザー: {{ message }}'''

# メモリ付き会話
await assistant("好きな色は青です")
await assistant("私の好きな色は？")  # "あなたの好きな色は青です"
await assistant("プレゼントを勧めて")  # 記憶した好みを使用
```

---

## 📦 インストール

### 基本

```bash
pip install kagura-ai
```

### 機能付き（推奨）

```bash
# すべての機能（メモリ、Web、マルチモーダル、認証、MCP）
pip install kagura-ai[full]

# または必要なものだけ:
pip install kagura-ai[ai]    # メモリ + ルーティング + コンテキスト圧縮
pip install kagura-ai[web]   # Web検索 + マルチモーダル（画像、PDF、動画）
pip install kagura-ai[auth]  # OAuth2認証
pip install kagura-ai[mcp]   # Claude Desktop統合
```

### 環境設定

```bash
# 最低1つのLLM APIキーが必要
export OPENAI_API_KEY=sk-...

# オプション: Web検索
export BRAVE_SEARCH_API_KEY=...

# オプション: マルチモーダル（Gemini）
export GOOGLE_API_KEY=...
```

すべてのオプションは[設定ガイド](docs/en/configuration/environment-variables.md)を参照。

---

## 🚀 使い方

### オプションA: 対話型チャット（最も簡単）

Kaguraの機能を探索するのに最適：

```bash
kagura chat
```

**できること:**
- 📄 ファイルの読み取りと分析（PDF、画像、コード）
- 🌐 Web検索とURL取得
- 🎬 YouTube動画の要約
- 💻 Pythonコードの安全な実行
- 🔍 ドキュメントについての質問

**セッション例:**
```
[You] > design.pdfを読んで主要な要件を抽出して

[AI] > PDFを分析します。

      主要な要件:
      1. ユーザー認証システム
      2. リアルタイム通知
      3. モバイル対応デザイン

[You] > 要件1のベストプラクティスを検索して

[AI] > (Webを検索、ソース付きでベストプラクティスを提供)

[You] > 認証のサンプルコードを書いて

[AI] > (コードを生成して表示)
```

### オプションB: プログラム的にエージェント構築

統合と自動化に最適：

```python
from kagura import agent
from pydantic import BaseModel

class Report(BaseModel):
    summary: str
    action_items: list[str]
    priority: str

@agent
async def meeting_analyzer(transcript: str) -> Report:
    '''会議の議事録を分析して抽出:
    - 要約
    - アクションアイテム
    - 優先度

    議事録: {{ transcript }}'''

# アプリで使用
report = await meeting_analyzer("今日はQ4の目標について話し合いました...")
for item in report.action_items:
    print(f"TODO: {item}")
```

---

## 📚 詳しく学ぶ

### 5分チュートリアル

初めての方はこちらから：

1. **[最初のエージェント](docs/en/tutorials/01-basic-agent.md)** - 2分でHello World
2. **[構造化出力](docs/en/tutorials/02-pydantic.md)** - Pydanticによる型安全なレスポンス
3. **[対話型チャット](docs/en/tutorials/03-chat.md)** - Claude Code風の体験
4. **[メモリとコンテキスト](docs/en/tutorials/04-memory.md)** - 会話を記憶
5. **[WebとマルチモーダルModel](docs/en/tutorials/05-web-multimodal.md)** - Web検索、画像分析

### 実世界のサンプル

[examples/](./examples/)に36以上のサンプル：

- **[データ分析](examples/06_advanced/data_analysis.py)** - Pandas + AI
- **[Web調査](examples/05_web/research_agent.py)** - Web検索 + 統合
- **[画像分析](examples/04_multimodal/image_analysis.py)** - Gemini搭載ビジョン
- **[ドキュメントQA](examples/04_multimodal/multimodal_rag_demo.py)** - PDFと画像のRAG
- **[実世界のユースケース](examples/08_real_world/)** - 本番対応サンプル

### ドキュメント

- **[完全ドキュメント](https://www.kagura-ai.com/)** - 完全ガイド
- **[APIリファレンス](docs/en/api/)** - すべてのデコレータ、クラス、関数
- **[設定](docs/en/configuration/)** - 環境変数、LLMモデル
- **[MCP統合](docs/en/guides/mcp-integration.md)** - Claude Desktopで使用

---

## 🛠️ 高度な機能

### メモリ管理

コンテキスト認識エージェント用の3層メモリシステム：

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''あなたは親切なアシスタントです。{{ message }}'''

# 自動的に記憶:
# - コンテキストメモリ: 現在の会話
# - 永続メモリ: ユーザー設定
# - RAGメモリ: 履歴のセマンティック検索
```

### エージェントルーティング

適切なエージェントを自動選択：

```python
from kagura.routing import SemanticRouter

router = SemanticRouter()
router.add_route("translation", translator)
router.add_route("code_review", reviewer)
router.add_route("data_analysis", analyzer)

# インテリジェントルーティング
agent = await router.route("これを日本語に翻訳")
# 自動的に'translator'を選択
```

### マルチモーダルRAG

画像、PDF、動画をインデックス・検索：

```python
from kagura.core.memory import MultimodalRAG

rag = MultimodalRAG()

# ドキュメントをインデックス（PDF、画像、動画）
await rag.index_directory("./knowledge_base")

# セマンティック検索
results = await rag.search("四半期売上グラフ")
# PDF/画像内の関連グラフを検索
```

### Web統合

Web検索とスクレイピングを内蔵：

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''{{ topic }}を調査:
    - web_search(query): Web検索（Brave/DuckDuckGo）
    - web_fetch(url): Webページ取得
    '''

result = await researcher("最新のPythonフレームワーク")
```

### MCP統合

KaguraエージェントをClaude Desktopで使用：

```bash
# 一度だけのセットアップ
kagura mcp start
kagura mcp config claude

# Claude Desktopで使用可能に！
# すべての@agent関数がClaudeツールになる
```

### テストフレームワーク

テストユーティリティを内蔵：

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_sentiment_analysis(self):
        result = await my_agent("これ最高！")

        # セマンティックアサーション
        self.assert_semantic_match(
            result,
            "ポジティブな感情"
        )
```

### 可視化

パフォーマンスとコストを自動追跡：

```bash
kagura monitor stats
# エージェントごとの実行回数、時間、コストを表示

kagura monitor cost --group-by agent
# エージェント別コスト内訳
```

---

## 🎯 主な機能

### フレームワーク基本
- ✅ **@agentデコレータ** - 1行でAIエージェント作成
- ✅ **@toolデコレータ** - Python関数をエージェントツールに変換
- ✅ **@workflowデコレータ** - マルチエージェントオーケストレーション
- ✅ **Jinja2テンプレート** - docstring内の動的プロンプト
- ✅ **型安全パース** - Pydanticによる自動レスポンス解析
- ✅ **マルチLLMサポート** - LiteLLM経由で100以上のプロバイダー

### 本番機能
- ✅ **メモリ管理** - 3層システム（Context/Persistent/RAG）
- ✅ **エージェントルーティング** - Semantic/Intent/Memory-aware
- ✅ **コード実行** - セキュアなPythonサンドボックス（AST検証）
- ✅ **Web統合** - 検索（Brave/DuckDuckGo）+ スクレイピング
- ✅ **マルチモーダルRAG** - 画像、PDF、音声、動画（Gemini搭載）
- ✅ **コンテキスト圧縮** - 長い会話のトークン管理
- ✅ **テストフレームワーク** - セマンティックアサーション付きAgentTestCase
- ✅ **可視化** - テレメトリ、コスト追跡、監視

### 開発者体験
- ✅ **対話型チャット** - Claude Code風の体験（`kagura chat`）
- ✅ **MCP統合** - Claude Desktopでエージェント使用
- ✅ **完全な型安全性** - pyright strictモード、100%型付け
- ✅ **1,300以上のテスト** - 90%以上のカバレッジ
- ✅ **36以上のサンプル** - 基本から実世界のユースケースまで

---

## 💡 実世界のサンプル

### コード付きデータ分析

```python
@agent
async def data_scientist(question: str, data_file: str) -> str:
    '''{{ data_file }}を分析して{{ question }}に答えて

    pandas、numpy、matplotlibを使ったPythonコードが書けます。
    コードはセキュアなサンドボックスで実行されます。
    '''

result = await data_scientist(
    "月次売上のトレンドは？",
    "sales.csv"
)
# AIがpandasコードを書き、グラフを生成、洞察を返す
```

### ドキュメントインテリジェンス

```python
@agent(enable_memory=True)
async def doc_assistant(question: str) -> str:
    '''./knowledge_base/内のドキュメントについての質問に回答

    rag_search(query)で以下から関連情報を検索:
    - PDF、画像、動画（Gemini搭載分析）
    - ChromaDBによるセマンティック検索
    '''

# すべてのドキュメントから質問
result = await doc_assistant(
    "Q3の財務報告書をすべてまとめて"
)
```

### Web調査アシスタント

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''{{ topic }}を調査:
    1. Webで最新情報を検索
    2. 関連記事を取得・分析
    3. ソース付きで発見事項を統合

    ツール:
    - web_search(query): Web検索（Brave Search / DuckDuckGo）
    - web_fetch(url): Webページ取得
    '''

result = await researcher("2025年のAI規制")
# ソース付きの包括的な調査結果を返す
```

### メモリ付き会話エージェント

```python
@agent(enable_memory=True, memory_scope="user")
async def personal_assistant(message: str) -> str:
    '''あなたはパーソナルアシスタントです。ユーザーの好みを記憶してください。

    メッセージ: {{ message }}'''

# コンテキスト付きの複数ターン会話
await personal_assistant("簡潔な回答が好きです")
await personal_assistant("フランスの首都は？")
# "パリです。"（簡潔さの好みを記憶）

await personal_assistant("私が言った好みは何でしたか？")
# "簡潔な回答を好むとおっしゃいました。"
```

---

## 🎓 サンプルで学ぶ

カテゴリ別に整理された[36以上のサンプル](./examples/)：

- **[01_basic](examples/01_basic/)** - Hello World、テンプレート、型ヒント（7例）
- **[02_memory](examples/02_memory/)** - メモリシステム、RAG（6例）
- **[03_routing](examples/03_routing/)** - エージェントルーティング、選択（4例）
- **[04_multimodal](examples/04_multimodal/)** - 画像、PDF、音声、動画（5例）
- **[05_web](examples/05_web/)** - Web検索、スクレイピング、YouTube（5例）
- **[06_advanced](examples/06_advanced/)** - ワークフロー、テスト、フック（4例）
- **[07_presets](examples/07_presets/)** - プリセットエージェント（3例）
- **[08_real_world](examples/08_real_world/)** - 本番ユースケース（2例）

各サンプルは完全にドキュメント化されテスト済みです。

---

## 🚀 高度な使い方

### カスタムツール

```python
from kagura import tool, agent

@tool
def search_database(query: str) -> list[dict]:
    '''内部データベースを検索'''
    return db.query(query)

@agent(tools=[search_database])
async def data_agent(question: str) -> str:
    '''データベースを使って回答: {{ question }}

    search_database(query)で情報を検索できます。
    '''
```

### マルチエージェントワークフロー

```python
from kagura import workflow

@workflow.stateful
async def research_workflow(topic: str) -> dict:
    '''完全な調査ワークフロー'''

    # ステップ1: 計画
    plan = await planner_agent(topic)

    # ステップ2: 各ポイントを調査
    findings = []
    for point in plan.points:
        result = await research_agent(point)
        findings.append(result)

    # ステップ3: 統合
    summary = await synthesis_agent(findings)

    return {"plan": plan, "findings": findings, "summary": summary}
```

### MCPサーバー（Claude Desktop統合）

```bash
# MCPサーバー起動
kagura mcp start

# Claude Desktop設定
kagura mcp config claude

# Claude Desktopで使用可能に！
```

すべての`@agent`関数が自動的にClaudeツールとして利用可能になります。

---

## 📚 ドキュメント

### はじめに
- [インストールガイド](docs/en/installation.md)
- [クイックスタート（5分）](docs/en/quickstart.md)
- [対話型チャットチュートリアル](docs/en/tutorials/03-chat.md)

### チュートリアル
- [基本的なエージェント作成](docs/en/tutorials/01-basic-agent.md)
- [Pydanticによる構造化出力](docs/en/tutorials/02-pydantic.md)
- [メモリ管理](docs/en/tutorials/04-memory.md)
- [WebとマルチモーダルModel](docs/en/tutorials/05-web-multimodal.md)
- [コード実行](docs/en/tutorials/07-code-execution.md)

### ガイド
- [メモリ管理](docs/en/guides/memory-management.md)
- [エージェントルーティング](docs/en/guides/routing.md)
- [マルチモーダルRAG](docs/en/guides/multimodal-rag.md)
- [Web統合](docs/en/guides/web-integration.md)
- [MCP統合](docs/en/guides/mcp-integration.md)
- [エージェントテスト](docs/en/guides/testing.md)

### リファレンス
- [APIリファレンス](docs/en/api/)
- [設定](docs/en/configuration/)
- [サンプル](./examples/)

---

## 🏗️ アーキテクチャ

Kagura AIは実績のある技術で構築：

- **LLM統合**: [LiteLLM](https://github.com/BerriAI/litellm)（100以上のプロバイダー）
- **メモリ**: [ChromaDB](https://www.trychroma.com/)（ベクトルストレージ）
- **ルーティング**: [Semantic Router](https://github.com/aurelio-labs/semantic-router)
- **マルチモーダル**: [Google Gemini API](https://ai.google.dev/)
- **バリデーション**: [Pydantic v2](https://docs.pydantic.dev/)
- **テスト**: [pytest](https://pytest.org/) + カスタムフレームワーク

完全な型安全性（pyright strict）と1,300以上のテストを備えています。

---

## 🤝 コントリビューション

コントリビューションを歓迎します！

```bash
# セットアップ
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras

# テスト実行
pytest -n auto

# 型チェック
pyright src/kagura/

# リント
ruff check src/
```

詳細は[CONTRIBUTING.md](./CONTRIBUTING.md)を参照してください。

---

## 📊 プロジェクト統計

- **1,300以上のテスト**（90%以上のカバレッジ）
- **100%型付け**（pyright strictモード）
- **36以上のサンプル**（すべてテスト済み）
- **31以上のRFC**（16以上実装済み）
- **活発な開発**（50以上のリリース）

---

## 🗺️ ロードマップ

### 最近完了（v2.5.x）
- ✅ 環境変数の統一管理
- ✅ CLI簡素化（11,000行以上削除）
- ✅ コンテキスト圧縮システム
- ✅ MCP完全統合
- ✅ テレメトリと可視化

### 近日実装（v2.6.0）
- 🔄 自動検出とインテント認識（RFC-033 Phase 1）
- 🔄 シークレット管理システム（RFC-029）
- 🔄 プリインストールエージェントコレクション

### 将来（v2.7.0+）
- 🔮 音声ファーストインターフェース（RFC-004）
- 🔮 Google Workspace統合（RFC-023）
- 🔮 マルチエージェントオーケストレーション（RFC-009）

詳細は[UNIFIED_ROADMAP.md](ai_docs/UNIFIED_ROADMAP.md)を参照。

---

## 📄 ライセンス

Apache License 2.0 - 詳細は[LICENSE](./LICENSE)を参照

---

## 🌸 名前の由来

「神楽（かぐら）」は日本の伝統芸能で、調和、つながり、創造性を体現しています - このフレームワークの核心にある原理です。

---

**Kagura AIコミュニティが❤️を込めて開発**

[GitHub](https://github.com/JFK/kagura-ai) • [ドキュメント](https://www.kagura-ai.com/) • [PyPI](https://pypi.org/project/kagura-ai/) • [Discord](https://discord.gg/kagura-ai)
