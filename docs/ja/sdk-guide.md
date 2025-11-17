# Kagura AI SDK ガイド

Kagura AI v4.0 SDK を使った AI エージェント構築の完全ガイド。

---

## 目次

- [クイックスタート](#クイックスタート)
- [コアコンセプト](#コアコンセプト)
- [Agent デコレーター](#agent-デコレーター)
- [カスタムツール](#カスタムツール)
- [メモリー管理](#メモリー管理)
- [並列実行](#並列実行)
- [エラーハンドリング](#エラーハンドリング)
- [テスト](#テスト)
- [ベストプラクティス](#ベストプラクティス)

---

## クイックスタート

### インストール

```bash
pip install kagura-ai
```

### 最初のエージェント

```python
import asyncio
from kagura import agent

@agent
async def hello(name: str) -> str:
    """{{ name }} に親しみやすく挨拶してください。"""
    pass  # 実装は AI に置き換わる

# エージェントを実行
result = asyncio.run(hello("Alice"))
print(result)  # "こんにちは Alice さん！ようこそ..."
```

**仕組み:**
1. `@agent` デコレーターで関数を AI エージェントに変換
2. docstring が AI プロンプトになる（Jinja2 テンプレート）
3. 関数シグネチャが入出力を定義
4. AI が実行時に実装を生成

---

## コアコンセプト

### 1. エージェント関数

エージェント関数は `@agent` でデコレートされた Python 関数です：

```python
@agent
async def my_agent(input: str) -> str:
    """ここにプロンプトテンプレート: {{ input }}"""
    pass
```

**主要コンポーネント:**
- **関数名**: エージェントを識別（テレメトリーで使用）
- **パラメーター**: エージェントの入力を定義（プロンプトに渡される）
- **戻り値の型**: 出力構造を定義（文字列、Pydantic モデルなど）
- **Docstring**: Jinja2 プロンプトテンプレート

### 2. プロンプトテンプレート

docstring で Jinja2 構文を使って動的プロンプトを作成：

```python
@agent
async def translator(text: str, target_lang: str) -> str:
    """
    以下のテキストを {{ target_lang }} に翻訳してください：

    {{ text }}

    翻訳のみを提供し、説明は不要です。
    """
    pass
```

### 3. 構造化出力

Pydantic モデルで型安全で検証された出力を実現：

```python
from pydantic import BaseModel, Field

class Sentiment(BaseModel):
    sentiment: str = Field(description="positive、negative、または neutral")
    confidence: float = Field(ge=0, le=1, description="信頼度スコア")
    reasoning: str = Field(description="簡潔な説明")

@agent
async def analyze_sentiment(text: str) -> Sentiment:
    """次のテキストの感情分析: {{ text }}"""
    pass

# 型安全なアクセス
result = await analyze_sentiment("これ最高！")
print(result.sentiment)  # IDE の自動補完が効く！
print(result.confidence)  # 0.95
```

---

## Agent デコレーター

### 基本的な使い方

```python
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass
```

### 設定オプション

```python
from kagura import agent, LLMConfig

config = LLMConfig(
    model="gpt-4o",                  # 使用するモデル
    temperature=0.7,                 # 創造性 (0-1)
    max_tokens=1000,                 # 最大応答長
    enable_cache=True,               # レスポンスキャッシュを有効化
)

@agent(config=config)
async def configured_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass
```

### モデル選択

Kagura は [LiteLLM](https://github.com/BerriAI/litellm) でマルチプロバイダーをサポート：

```python
# OpenAI
@agent(model="gpt-4o")
async def openai_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

# Anthropic Claude
@agent(model="claude-3-5-sonnet-20241022")
async def claude_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

# Google Gemini
@agent(model="gemini/gemini-2.0-flash")
async def gemini_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

# Ollama (ローカル)
@agent(model="ollama/llama3.2")
async def local_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass
```

**対応プロバイダー:** OpenAI、Anthropic、Google、Azure、AWS Bedrock、Ollama など 100 以上。

### メモリー有効化エージェント

```python
from kagura import agent
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="assistant")

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """
    あなたはメモリーを持つ便利なアシスタントです。
    ユーザー: {{ query }}
    """
    pass

# コンテキスト付き会話
await assistant("私の名前は Alice です", memory_manager=memory)
await assistant("私の名前は？", memory_manager=memory)
# 応答: "あなたの名前は Alice です"
```

### ツール有効化エージェント

```python
from kagura import agent, tool

@tool
async def search_web(query: str) -> str:
    """次のクエリで Web 検索: {{ query }}"""
    # 検索実装
    return f"{query} の結果"

@agent(tools=[search_web])
async def researcher(topic: str) -> str:
    """
    search_web(query) を使って {{ topic }} を調査。
    発見をまとめてください。
    """
    pass

# エージェントは自動的に search_web を呼び出す
result = await researcher("最新の AI トレンド")
```

---

## カスタムツール

ツールはカスタム関数でエージェント機能を拡張します。

### ツールの作成

```python
from kagura import tool

@tool
async def calculate(expression: str) -> float:
    """数式を安全に評価します。

    Args:
        expression: "2 + 2" や "sqrt(16)" のような数式

    Returns:
        計算結果
    """
    # 安全な評価（ast.literal_eval などを使用）
    import ast
    return float(ast.literal_eval(expression))
```

### エージェントでツールを使用

```python
from kagura import agent, tool

@tool
async def get_weather(city: str) -> str:
    """都市の現在の天気を取得。"""
    # 天気 API を呼び出し
    return f"{city} は晴れ、22℃"

@tool
async def get_time(timezone: str = "UTC") -> str:
    """タイムゾーンの現在時刻を取得。"""
    from datetime import datetime
    return datetime.now().isoformat()

@agent(tools=[get_weather, get_time])
async def assistant(request: str) -> str:
    """
    次のリクエストを処理: {{ request }}

    利用可能なツール:
    - get_weather(city): 天気を取得
    - get_time(timezone): 現在時刻を取得
    """
    pass

# エージェントは自動的に適切なツールを呼び出す
result = await assistant("東京の天気と現在時刻は？")
```

### ツールのガイドライン

**ベストプラクティス:**
1. **明確な docstring**: 目的、パラメーター、戻り値を記述
2. **型ヒント**: パラメーター検証のために使用
3. **エラーハンドリング**: 失敗を適切に処理
4. **冪等性**: 同じ入力は可能な限り同じ出力を生成
5. **副作用**: 状態変更や外部呼び出しを文書化

**エラーハンドリング付きの例:**

```python
@tool
async def fetch_url(url: str) -> str:
    """URL からコンテンツを取得。

    Args:
        url: 取得する URL

    Returns:
        ページコンテンツまたはエラーメッセージ
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            return response.text[:5000]  # サイズ制限
    except httpx.HTTPError as e:
        return f"{url} の取得エラー: {e}"
```

---

## メモリー管理

Kagura は永続ストレージとセマンティック検索機能を備えた統合メモリーシステムを提供します。

**重要:** v4.4.0 から、すべてのメモリーは永続化されます。`scope="working"` パラメーターと一時メモリーメソッド（`set_temp()`、`get_temp()`）は削除されました。

### 1. コンテキストメモリー（会話履歴）

最近のメッセージをコンテキストに保持：

```python
from kagura import agent
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="chatbot",
    max_messages=10  # 直近 10 メッセージを保持
)

@agent(enable_memory=True)
async def chatbot(message: str, memory_manager: MemoryManager) -> str:
    """会話アシスタント。ユーザー: {{ message }}"""
    pass

# マルチターン会話
await chatbot("こんにちは、Python を学んでいます", memory_manager=memory)
await chatbot("私の名前は？", memory_manager=memory)
await chatbot("学習中の内容のリソースを推薦して", memory_manager=memory)
```

### 2. 永続メモリー（長期保存）

ChromaDB でセッション間で事実を保存：

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="assistant",
    enable_session_memory=True,
    session_id="user_123"
)

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """永続メモリーを持つアシスタント。ユーザー: {{ query }}"""
    pass

# 長期的な事実を保存
await assistant("私の好きな色は青です", memory_manager=memory)

# 後のセッション - メモリーは永続化
memory2 = MemoryManager(
    agent_name="assistant",
    enable_session_memory=True,
    session_id="user_123"
)
await assistant("私の好きな色は？", memory_manager=memory2)
# 応答: "あなたの好きな色は青です"
```

### 3. RAG メモリー（セマンティック検索）

ドキュメントをセマンティックにインデックス・検索：

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(
    agent_name="docs_bot",
    enable_rag=True,
    rag_collection="my_docs"
)

# ドキュメントをインデックス
await memory.rag_store(
    content="Kagura AI は MCP ネイティブなメモリープラットフォームです",
    metadata={"source": "README.md"}
)

@agent(enable_memory=True)
async def docs_bot(question: str, memory_manager: MemoryManager) -> str:
    """
    ドキュメントに基づいて回答: {{ question }}
    RAG メモリーで関連ドキュメントを検索。
    """
    pass

result = await docs_bot("Kagura AI とは？", memory_manager=memory)
```

### 4. Graph Memory（関係性）

エンティティと関係性を追跡：

```python
from kagura.core.graph import GraphMemory

graph = GraphMemory(user_id="user_123", agent_name="assistant")

# インタラクションを保存
graph.add_interaction(
    user_query="ハイキングが好きです",
    ai_response="それは素晴らしい！ハイキングは健康的なアウトドア活動ですね。",
    metadata={"topic": "趣味"}
)

# 関連情報を検索
related = graph.get_related_nodes(node_id="hiking_interest", depth=2)
```

### メモリー戦略

**適切なメモリータイプの選択:**

| メモリータイプ | ユースケース | 永続化 | 検索 |
|------------|----------|-------------|--------|
| **コンテキスト** | 最近のメッセージ | 永続 (SQLite) | シーケンシャル |
| **永続** | ユーザー設定 | 永続 (SQLite) | キー・バリュー検索 |
| **RAG** | ドキュメント QA | 永続 (ChromaDB) | セマンティック |
| **Graph** | 関係性 | 永続 (NetworkX) | グラフトラバーサル |

**v4.3.x から v4.4.0 へのマイグレーション:**
- すべてのメモリーが永続化 - 一時/セッション専用メモリーはなし
- すべての `memory_store()` 呼び出しから `scope="working"` を削除
- `set_temp()`/`get_temp()` をクライアント側の変数または永続ストレージに置き換え
- すべての永続データには `remember()`/`recall()` を使用

---

## 並列実行

独立した操作を並行処理で高速化。

### parallel_gather

複数の操作を同時実行：

```python
from kagura import agent
from kagura.core.parallel import parallel_gather

@agent
async def translator(text: str, lang: str) -> str:
    """{{ text }} を {{ lang }} に翻訳"""
    pass

# シリアル（遅い）
spanish = await translator("こんにちは", "スペイン語")
french = await translator("こんにちは", "フランス語")
japanese = await translator("こんにちは", "日本語")

# パラレル（3倍速）
spanish, french, japanese = await parallel_gather(
    translator("こんにちは", "スペイン語"),
    translator("こんにちは", "フランス語"),
    translator("こんにちは", "日本語")
)
```

### parallel_map

バッチを効率的に処理：

```python
from kagura.core.parallel import parallel_map

@agent
async def analyze(text: str) -> str:
    """次のテキストの感情分析: {{ text }}"""
    pass

reviews = [
    "素晴らしい製品！",
    "ひどい経験でした。",
    "全体的にまあまあ。",
    # ... さらに 100 件のレビュー
]

# 一度に 10 件処理
results = await parallel_map(
    lambda review: analyze(review),
    reviews,
    max_concurrent=10
)
```

### マルチエージェントパイプライン

独立したステップを並列化：

```python
from kagura.core.parallel import parallel_gather

@agent
async def summarize(text: str) -> str:
    """要約: {{ text }}"""
    pass

@agent
async def extract_keywords(text: str) -> list[str]:
    """次からキーワードを抽出: {{ text }}"""
    pass

@agent
async def categorize(text: str) -> str:
    """分類: {{ text }}"""
    pass

# すべての操作を並列実行
article = "長い記事のテキスト..."
summary, keywords, category = await parallel_gather(
    summarize(article),
    extract_keywords(article),
    categorize(article)
)
```

---

## エラーハンドリング

### 基本的なエラーハンドリング

```python
from kagura import agent
from kagura.core.exceptions import AgentError, LLMError

@agent
async def my_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

try:
    result = await my_agent("テスト")
except LLMError as e:
    print(f"LLM エラー: {e}")
    # API 障害、レート制限などを処理
except AgentError as e:
    print(f"エージェントエラー: {e}")
    # エージェント固有のエラーを処理
except Exception as e:
    print(f"予期しないエラー: {e}")
```

### Tenacity でリトライ

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from kagura import agent

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_agent_with_retry(input: str) -> str:
    return await my_agent(input)

# 失敗時に自動的にリトライ
result = await call_agent_with_retry("テスト")
```

### フォールバックパターン

```python
@agent(model="gpt-4o")
async def primary_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

@agent(model="gpt-4o-mini")
async def fallback_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

async def robust_call(input: str) -> str:
    try:
        return await primary_agent(input)
    except Exception:
        # より安価/シンプルなモデルにフォールバック
        return await fallback_agent(input)

result = await robust_call("テスト")
```

---

## テスト

### エージェントのユニットテスト

```python
import pytest
from kagura import agent

@agent
async def sentiment_analyzer(text: str) -> str:
    """次のテキストの感情分析: {{ text }}
    戻り値: positive、negative、または neutral"""
    pass

@pytest.mark.asyncio
async def test_sentiment_analyzer():
    # ポジティブな感情
    result = await sentiment_analyzer("これ最高！")
    assert "positive" in result.lower()

    # ネガティブな感情
    result = await sentiment_analyzer("これはひどい")
    assert "negative" in result.lower()
```

### LLM 呼び出しのモック

```python
from unittest.mock import AsyncMock, patch
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

@pytest.mark.asyncio
@patch('kagura.core.llm.call_llm')
async def test_agent_with_mock(mock_llm):
    # LLM レスポンスをモック
    mock_llm.return_value = "モックされたレスポンス"

    result = await my_agent("テスト")
    assert result == "モックされたレスポンス"

    # LLM が呼び出されたことを検証
    mock_llm.assert_called_once()
```

### ツールのテスト

```python
from kagura import tool

@tool
async def calculate(expression: str) -> float:
    """計算: {{ expression }}"""
    import ast
    return float(ast.literal_eval(expression))

@pytest.mark.asyncio
async def test_calculate_tool():
    assert await calculate("2 + 2") == 4.0
    assert await calculate("10 * 5") == 50.0

    # エラーハンドリングのテスト
    with pytest.raises(Exception):
        await calculate("無効")
```

### 統合テスト

```python
@pytest.mark.asyncio
async def test_agent_with_memory():
    from kagura.core.memory import MemoryManager

    memory = MemoryManager(agent_name="test_agent")

    # 最初のインタラクション
    result1 = await chatbot("私の名前は Alice です", memory_manager=memory)
    assert "Alice" in result1

    # メモリーは永続化されるべき
    result2 = await chatbot("私の名前は？", memory_manager=memory)
    assert "Alice" in result2
```

---

## ベストプラクティス

### 1. プロンプトエンジニアリング

**具体的で明確に:**

```python
# ❌ 曖昧
@agent
async def bad_agent(input: str) -> str:
    """{{ input }} で何かする"""
    pass

# ✅ 具体的
@agent
async def good_agent(text: str) -> str:
    """
    次のテキストの感情分析: {{ text }}

    次のいずれかで応答: positive、negative、neutral
    信頼度スコア (0-1) と簡潔な理由を含める。
    """
    pass
```

**プロンプトに例を提供:**

```python
@agent
async def extractor(text: str) -> dict:
    """
    次から人物情報を抽出: {{ text }}

    例:
    - "太郎は 30 歳です" -> {"name": "太郎", "age": 30}
    - "花子は教師として働いています" -> {"name": "花子", "occupation": "教師"}

    利用可能なフィールドで JSON を返す。
    """
    pass
```

### 2. 型安全性

**複雑な出力には Pydantic モデルを使用:**

```python
from pydantic import BaseModel, Field

class Analysis(BaseModel):
    sentiment: str = Field(description="positive/negative/neutral")
    confidence: float = Field(ge=0, le=1)
    keywords: list[str] = Field(max_length=10)

@agent
async def analyze(text: str) -> Analysis:
    """分析: {{ text }}"""
    pass

# 型安全、検証済み
result = await analyze("素晴らしい製品！")
print(result.sentiment)  # IDE の自動補完
```

### 3. リソース管理

**コネクションプーリングと制限を使用:**

```python
from kagura import LLMConfig

config = LLMConfig(
    model="gpt-4o-mini",
    max_tokens=500,          # 応答長を制限
    enable_cache=True,       # 同一リクエストをキャッシュ
    timeout=30,              # ハングを防ぐ
)

@agent(config=config)
async def efficient_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass
```

**並列実行を制限:**

```python
from kagura.core.parallel import parallel_map

# 1000 件の同時リクエストで API を圧倒しない
results = await parallel_map(
    agent_func,
    inputs,
    max_concurrent=10  # 適切な制限
)
```

### 4. モニタリング

**コストと使用状況を追跡:**

```bash
# CLI モニタリング
kagura monitor stats
kagura monitor cost --agent my_agent
```

**エージェントを計装:**

```python
import logging

logger = logging.getLogger(__name__)

@agent
async def monitored_agent(input: str) -> str:
    """{{ input }} を処理"""
    pass

try:
    result = await monitored_agent("テスト")
    logger.info("エージェント成功", extra={"input": "テスト"})
except Exception as e:
    logger.error("エージェント失敗", exc_info=True)
    raise
```

### 5. セキュリティ

**入力を検証:**

```python
from pydantic import BaseModel, Field, validator

class SafeInput(BaseModel):
    query: str = Field(max_length=1000)

    @validator('query')
    def no_injection(cls, v):
        dangerous = ['DROP', 'DELETE', 'EXEC']
        if any(word in v.upper() for word in dangerous):
            raise ValueError("潜在的に危険な入力")
        return v

@agent
async def safe_agent(input: SafeInput) -> str:
    """{{ input.query }} を処理"""
    pass
```

**ツール出力をサニタイズ:**

```python
@tool
async def safe_search(query: str) -> str:
    """安全に検索"""
    # クエリを検証
    if len(query) > 500:
        return "クエリが長すぎます"

    # 検索実行
    results = execute_search(query)

    # 結果をサニタイズ
    return sanitize_html(results[:5000])
```

---

## 次のステップ

### さらに学ぶ

- [API リファレンス](api-reference.md) - 完全な API ドキュメント
- [チュートリアル](ja/tutorials/) - ステップバイステップガイド
- [サンプル](https://github.com/JFK/kagura-ai/tree/main/examples) - 実世界のコード例
- [アーキテクチャ](architecture.md) - システム設計

### 統合

- [MCP 統合](mcp-setup.md) - Claude Desktop に接続
- [REST API](rest-api-usage.md) - HTTP API アクセス
- [セルフホスティング](self-hosting.md) - 独自インスタンスをデプロイ

### コミュニティ

- [GitHub](https://github.com/JFK/kagura-ai) - Issue 報告、コントリビュート
- [コントリビュートガイド](https://github.com/JFK/kagura-ai/blob/main/CONTRIBUTING.md)

---

## まとめ

**重要なポイント:**

1. **`@agent` デコレーター**で関数を AI エージェントに変換
2. **Jinja2 プロンプト**で動的で文脈に応じたインタラクション
3. **Pydantic モデル**で型安全で検証済みの出力
4. **カスタムツール**でエージェント機能を拡張
5. **メモリー階層**で異なる永続化ニーズに対応
6. **並列実行**で独立した操作を高速化
7. **エラーハンドリング**と**テスト**で信頼性を確保

**構築を開始:**

```python
from kagura import agent

@agent
async def my_first_agent(task: str) -> str:
    """次のタスクを完了: {{ task }}"""
    pass

result = await my_first_agent("量子コンピューティングを 3 文で要約")
print(result)
```

Kagura AI で楽しいコーディングを！🎉
