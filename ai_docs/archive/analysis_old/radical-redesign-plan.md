# Kagura AI 2.0 - ラディカル・リデザイン計画

> **前提**: 後方互換性は完全に捨てる。理想的なDXを追求し、ゼロから設計し直す。

---

## エグゼクティブサマリー

Kagura AI 2.0は、**"Code is Agent, Agent is Code"** のコンセプトで完全再設計する。YAMLを完全廃止し、PythonコードだけでAIエージェントを定義・実行できるフレームワークへ。

### 設計哲学

1. **Zero Configuration**: 設定ファイル不要、コードだけで完結
2. **Type-First**: 型がそのまま仕様、ドキュメント、バリデーションになる
3. **Runtime is Design Time**: 実行時に自己最適化、自己改善
4. **Agent as Function**: エージェント = 型付き非同期関数

---

## 🚀 理想的なDX

### Before (Kagura AI 1.x)

```yaml
# agent.yml
description: "Summarizer"
prompt:
  - template: "Summarize: {content}"
response_fields:
  - summary

# state_model.yml
state_fields:
  - name: content
    type: str
  - name: summary
    type: str
```

```python
# main.py
agent = Agent.assigner("summarizer", {"content": text})
result = await agent.execute()
```

**問題点**:
- 3ファイル必要
- YAML学習コスト
- IDE補完効かない
- デバッグ困難

### After (Kagura AI 2.0)

```python
from kagura import agent

@agent
async def summarize(content: str) -> str:
    """Summarize the given content in 3 sentences."""
    # この関数自体がエージェント
    # docstringがプロンプト
    # 型ヒントがスキーマ
    pass  # 実装不要、自動でLLM呼び出し

# 使い方
summary = await summarize("Long text here...")
```

**さらに高度な例**:

```python
from kagura import agent, tool, workflow
from pydantic import BaseModel

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

@tool  # LLM使わない高速実行
async def fetch_url(url: str) -> str:
    """Fetch content from URL"""
    async with httpx.AsyncClient() as client:
        return await client.get(url).text()

@agent
async def search(query: str) -> list[SearchResult]:
    """Search the web for the query"""
    pass

@agent
async def summarize_page(url: str) -> str:
    """Fetch and summarize a web page"""
    content = await fetch_url(url)  # ツールを直接呼び出し
    return f"Summary of {content[:100]}..."

@workflow  # 複数エージェントの組み合わせ
async def research(topic: str) -> str:
    """Research a topic and create a comprehensive report"""
    results = await search(topic)
    summaries = await asyncio.gather(*[
        summarize_page(r.url) for r in results[:5]
    ])
    return "\n\n".join(summaries)

# 全て同じインターフェース
report = await research("AI agents")
```

---

## 🏗️ コアアーキテクチャ

### 1. Agent as Decorated Function

```python
# kagura/core/decorators.py
from typing import TypeVar, Callable, ParamSpec, Awaitable
from functools import wraps
import inspect

P = ParamSpec('P')
T = TypeVar('T')

def agent(
    fn: Callable[P, Awaitable[T]] = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    system: str = None,
    **llm_kwargs
) -> Callable[P, Awaitable[T]]:
    """
    Convert a function into an AI agent.

    The function's signature becomes the input/output schema.
    The docstring becomes the prompt template.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # 1. 引数を型に基づいて検証
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # 2. プロンプト生成 (docstring + 引数)
            prompt = _build_prompt(doc, bound.arguments)

            # 3. LLM呼び出し
            llm = LLM(model=model, temperature=temperature, **llm_kwargs)
            response = await llm.generate(
                prompt=prompt,
                response_schema=sig.return_annotation
            )

            # 4. 型に基づいて自動パース
            return _parse_response(response, sig.return_annotation)

        # メタデータ保存
        wrapper._is_agent = True
        wrapper._signature = sig
        wrapper._model = model

        return wrapper

    return decorator if fn is None else decorator(fn)
```

### 2. Automatic Prompt Generation

```python
# kagura/core/prompt.py
from jinja2 import Template

def _build_prompt(docstring: str, arguments: dict) -> str:
    """
    docstringをJinja2テンプレートとして扱い、引数を埋め込む
    """
    template = Template(docstring)
    return template.render(**arguments)

# 例
@agent
async def translate(text: str, target_lang: str = "ja") -> str:
    """
    Translate the following text to {{ target_lang }}:

    {{ text }}
    """
    pass

# 自動生成されるプロンプト:
# "Translate the following text to ja:\n\nHello world"
```

### 3. Type-Based Response Parsing

```python
# kagura/core/parser.py
from typing import get_origin, get_args
from pydantic import BaseModel

def _parse_response(response: str, return_type: type) -> Any:
    """
    Return typeに基づいて自動パース
    """
    if return_type == str:
        return response

    if isinstance(return_type, type) and issubclass(return_type, BaseModel):
        # Pydanticモデル
        return return_type.model_validate_json(response)

    origin = get_origin(return_type)
    if origin == list:
        # list[T]
        item_type = get_args(return_type)[0]
        import json
        data = json.loads(response)
        return [_parse_response(json.dumps(item), item_type) for item in data]

    # その他の型にも対応
    # ...
```

### 4. Workflow Composition

```python
# kagura/core/workflow.py

@workflow
async def multi_step(input: str) -> dict:
    """
    Multi-step workflow with automatic orchestration
    """
    # 依存関係を自動で解決し、並列実行
    step1 = await agent1(input)
    step2, step3 = await asyncio.gather(
        agent2(step1),
        agent3(step1)
    )
    return {"result": await agent4(step2, step3)}

# または、LangGraphライクなグラフ定義
class ResearchFlow:
    @workflow.node
    async def search(self, query: str) -> list[str]:
        pass

    @workflow.node
    async def summarize(self, urls: list[str]) -> list[str]:
        pass

    @workflow.node
    async def synthesize(self, summaries: list[str]) -> str:
        pass

    # 自動的にグラフを構築
    graph = search >> summarize >> synthesize
```

---

## 💡 既存Issueを超える追加機能

### 1. **Built-in Streaming** (Issue外)

```python
from kagura import agent, stream

@agent(streaming=True)
async def write_essay(topic: str) -> str:
    """Write a long essay about {{ topic }}"""
    pass

# ストリーミング受信
async for chunk in stream(write_essay("AI")):
    print(chunk, end="", flush=True)
```

### 2. **Automatic Retry & Error Recovery** (Issue外)

```python
from kagura import agent, retry

@agent
@retry(max_attempts=3, backoff=2.0)
async def unreliable_task(data: str) -> str:
    """Process data that might fail"""
    pass

# または、フォールバック戦略
@agent(
    fallback_model="gpt-3.5-turbo",  # gpt-4失敗時
    timeout=30.0
)
async def robust_task(input: str) -> str:
    pass
```

### 3. **Observability Built-in** (Issue外)

```python
from kagura import agent, trace

@agent
@trace  # 自動的にOpenTelemetryでトレース
async def monitored_agent(x: str) -> str:
    """Automatically traced and logged"""
    pass

# ダッシュボードで可視化
# - 実行時間
# - トークン数
# - コスト
# - エラー率
```

### 4. **Built-in Caching** (Issue外)

```python
from kagura import agent, cache

@agent
@cache(ttl=3600)  # 1時間キャッシュ
async def expensive_analysis(text: str) -> dict:
    """Expensive LLM call"""
    pass

# 同じ入力は再利用
result1 = await expensive_analysis("test")  # LLM呼び出し
result2 = await expensive_analysis("test")  # キャッシュから
```

### 5. **Agent Composition & Inheritance** (Issue外)

```python
from kagura import agent

# ベースエージェント
@agent
async def base_translator(text: str, target: str) -> str:
    """Translate text to {{ target }}"""
    pass

# 特化エージェント
@agent(base=base_translator, target="ja")
async def to_japanese(text: str) -> str:
    """Specialized Japanese translator"""
    pass

# または、クラスベース
class TranslatorAgent:
    def __init__(self, target_lang: str):
        self.target = target_lang

    @agent
    async def translate(self, text: str) -> str:
        """Translate {{ text }} to {{ self.target }}"""
        pass

ja_translator = TranslatorAgent("ja")
result = await ja_translator.translate("Hello")
```

### 6. **Hot Reload for Development** (Issue外)

```bash
# 開発モード
kagura dev agents/my_agent.py --watch

# ファイル変更を検知して自動リロード
# ブラウザでインタラクティブにテスト可能
```

### 7. **Type-Safe Tool Calling** (Issue外)

```python
from kagura import agent, tools

# ツール定義
@tools.register
def calculate(expression: str) -> float:
    """Calculate mathematical expression"""
    return eval(expression)

@tools.register
async def search_web(query: str) -> list[str]:
    """Search the web"""
    # 実装

# エージェントから自動で使用
@agent(tools="auto")  # 自動で必要なツールを選択
async def solve_math_problem(problem: str) -> str:
    """
    Solve the math problem: {{ problem }}
    You can use tools if needed.
    """
    pass

# ツールを自動判断して使う
result = await solve_math_problem("What is 123 * 456?")
```

### 8. **Multi-Modal Support** (Issue外)

```python
from kagura import agent
from pathlib import Path

@agent(model="gpt-4o")
async def describe_image(image: Path | str) -> str:
    """Describe what you see in this image"""
    pass

# 画像を渡すだけ
description = await describe_image("photo.jpg")

# または、複数モダリティ
@agent
async def analyze_video(
    video: Path,
    question: str
) -> str:
    """
    Analyze the video and answer: {{ question }}
    """
    pass
```

### 9. **Built-in Memory & Context** (Issue外)

```python
from kagura import agent, memory

# メモリ付きエージェント
@agent
@memory(type="redis", ttl=86400)
async def chatbot(message: str, user_id: str) -> str:
    """
    Context-aware chatbot that remembers conversation.
    Current message: {{ message }}
    """
    pass

# 自動的に過去の会話を参照
response1 = await chatbot("My name is Alice", user_id="123")
response2 = await chatbot("What's my name?", user_id="123")
# -> "Your name is Alice"
```

### 10. **Agent Testing Framework** (Issue外)

```python
from kagura.testing import AgentTest

class TestSummarizer(AgentTest):
    agent = summarize

    async def test_basic_summary(self):
        result = await self.agent("Long text...")
        self.assert_length(result, max=100)
        self.assert_contains(result, ["key", "point"])

    async def test_multilingual(self):
        result = await self.agent("日本語テキスト")
        self.assert_language(result, "ja")

# モックLLM使用
@pytest.mark.mock_llm(response="Mocked summary")
async def test_with_mock():
    result = await summarize("test")
    assert result == "Mocked summary"
```

---

## 🔧 新しいプロジェクト構造

```
kagura-2.0/
├── kagura/
│   ├── __init__.py              # 全APIエクスポート
│   ├── core/
│   │   ├── agent.py            # Agent基底クラス
│   │   ├── decorators.py       # @agent, @tool, @workflow
│   │   ├── llm.py              # LLM抽象化レイヤー
│   │   ├── parser.py           # 型ベース自動パース
│   │   ├── prompt.py           # プロンプト生成
│   │   └── schema.py           # スキーマ生成
│   ├── integrations/
│   │   ├── mcp.py              # MCP Server
│   │   ├── api.py              # FastAPI統合
│   │   ├── langchain.py        # LangChain互換
│   │   └── llamaindex.py       # LlamaIndex互換
│   ├── tools/
│   │   ├── registry.py         # ツール登録
│   │   ├── builtin/            # 組み込みツール
│   │   │   ├── web.py
│   │   │   ├── files.py
│   │   │   └── math.py
│   │   └── decorators.py       # @tool
│   ├── memory/
│   │   ├── base.py
│   │   ├── redis.py
│   │   └── vector.py           # Qdrant統合
│   ├── observability/
│   │   ├── tracing.py          # OpenTelemetry
│   │   ├── metrics.py
│   │   └── logging.py
│   ├── testing/
│   │   ├── framework.py        # テストフレームワーク
│   │   ├── mocks.py           # モックLLM
│   │   └── fixtures.py
│   └── cli/
│       ├── dev.py              # 開発サーバー
│       ├── serve.py            # 本番サーバー
│       ├── test.py             # テスト実行
│       └── deploy.py           # デプロイ
├── examples/
│   ├── basic/
│   │   └── hello.py            # 最小例
│   ├── advanced/
│   │   ├── workflow.py
│   │   ├── multimodal.py
│   │   └── rag.py
│   └── production/
│       ├── api_server.py
│       └── mcp_server.py
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## 📦 新しい依存関係

### 最小構成

```toml
[project]
name = "kagura-ai"
version = "2.0.0"
dependencies = [
    # コア
    "pydantic>=2.10",
    "litellm>=1.53",

    # 非同期
    "asyncio",
    "httpx>=0.27",

    # テンプレート
    "jinja2>=3.1",

    # 型チェック
    "typing-extensions>=4.12",
]

[project.optional-dependencies]
# API Server
api = [
    "fastapi>=0.110",
    "uvicorn>=0.27",
]

# MCP Server
mcp = [
    "mcp>=1.1",
]

# Observability
observability = [
    "opentelemetry-api>=1.20",
    "opentelemetry-sdk>=1.20",
]

# Memory
memory = [
    "redis>=5.0",
]

# RAG
rag = [
    "qdrant-client>=1.7",
    "fastembed>=0.2",
]

# Development
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.8",
    "pyright>=1.1",
]

# Full
full = [
    "kagura-ai[api,mcp,observability,memory,rag,dev]",
]
```

---

## 🚀 マイグレーション戦略

### 段階的移行は不要 - クリーンブレイク

1. **Kagura 2.0 = 別パッケージ**
   ```bash
   pip install kagura-ai==2.0.0  # 新バージョン
   pip install kagura-ai==1.x    # 旧バージョン(保守モード)
   ```

2. **変換ツール提供**
   ```bash
   # 旧エージェントを新形式に変換
   kagura migrate agents/old_agent/

   # 生成: agents/old_agent/agent.py
   ```

3. **ドキュメント明確化**
   - Kagura 1.x: メンテナンスモード(重大バグのみ修正)
   - Kagura 2.0: アクティブ開発

---

## 📊 開発スケジュール (20週間)

### Phase 1: Core Engine (Week 1-6)

**目標**: 基本的なエージェント実行

- [ ] Week 1-2: `@agent`デコレータ実装
- [ ] Week 3-4: LLM統合・自動プロンプト生成
- [ ] Week 5-6: 型ベースパース・バリデーション

**成果物**:
```python
@agent
async def hello(name: str) -> str:
    """Say hello to {{ name }}"""
    pass
```

### Phase 2: Advanced Features (Week 7-12)

**目標**: プロダクション機能

- [ ] Week 7-8: `@tool`, `@workflow`
- [ ] Week 9-10: Streaming, Retry, Cache
- [ ] Week 11-12: Memory, Observability

**成果物**:
```python
@workflow
@cache(ttl=3600)
async def complex_task(x: str) -> dict:
    pass
```

### Phase 3: Integrations (Week 13-16)

**目標**: エコシステム統合

- [ ] Week 13-14: API Server, MCP Server
- [ ] Week 15-16: RAG (Qdrant), Tool Registry

**成果物**:
```bash
kagura serve my_agent --mcp
```

### Phase 4: DX & Polish (Week 17-20)

**目標**: 開発者体験最高化

- [ ] Week 17-18: CLI改善、ホットリロード
- [ ] Week 19-20: テストフレームワーク、ドキュメント

**成果物**:
```bash
kagura dev my_agent.py --watch
```

---

## 🎯 成功指標

### 開発者体験

| 指標 | 1.x | 2.0 目標 |
|------|-----|---------|
| エージェント作成時間 | 30分 | **30秒** |
| 必要ファイル数 | 3-5 | **1** |
| 学習時間 | 2時間 | **10分** |
| コード行数(Hello World) | 50行 | **5行** |

### 技術品質

| 指標 | 目標 |
|------|------|
| 型安全性 | 100% (型ヒント必須) |
| テストカバレッジ | 90%+ |
| ドキュメント | 全API |
| パフォーマンス | <100ms オーバーヘッド |

### コミュニティ

| 指標 | 6ヶ月目標 |
|------|-----------|
| GitHub Stars | 1000+ |
| 月間ダウンロード | 10k+ |
| コミュニティエージェント | 100+ |

---

## 💡 削除すべき機能(旧設計の負債)

1. **YAML設定**: 完全廃止
2. **複雑な状態管理**: Pydanticに一本化
3. **ConfigBase/AgentConfigManager**: 不要
4. **ModelRegistry**: 型システムで代替
5. **カスタムプロンプトテンプレート**: Jinja2で統一

---

## 🔥 キラー機能 (競合優位性)

### 1. Type-First Design

```python
# 型がそのまま仕様になる
@agent
async def api_call(
    endpoint: str,
    method: Literal["GET", "POST", "PUT"],
    headers: dict[str, str] | None = None
) -> dict:
    """Call API endpoint"""
    pass

# IDE補完完璧、ランタイムエラーほぼゼロ
```

### 2. Zero-Config Deployment

```bash
# コードだけでデプロイ
kagura deploy my_agent.py --platform vercel
# または
kagura deploy my_agent.py --platform aws-lambda
```

### 3. Automatic Optimization

```python
@agent(auto_optimize=True)
async def smart_agent(x: str) -> str:
    """This agent self-optimizes its prompts"""
    pass

# 実行データから自動でプロンプト改善
# A/Bテスト自動実施
```

---

## 📝 最初のリリース (v2.0.0-alpha)

### 最小機能セット

- [ ] `@agent` デコレータ
- [ ] 基本型サポート (str, int, list, dict, Pydantic)
- [ ] LiteLLM統合 (gpt-4o-mini, claude-3)
- [ ] ストリーミング
- [ ] 基本的なエラーハンドリング
- [ ] CLI: `kagura run`
- [ ] ドキュメント: Getting Started

### リリース基準

- ✅ 5行でHello Worldが動く
- ✅ 型安全性100%
- ✅ テストカバレッジ80%+
- ✅ ドキュメント完備

---

## 🎓 学習曲線

### 30秒でスタート

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    """Say hello to {{ name }}"""
    pass

print(await hello("World"))
```

### 5分で実用的

```python
from kagura import agent, tool

@tool
def fetch(url: str) -> str:
    import requests
    return requests.get(url).text

@agent
async def summarize_url(url: str) -> str:
    """Fetch {{ url }} and summarize it"""
    content = fetch(url)
    return f"Summary of {content[:100]}..."
```

### 30分でプロダクション

```python
from kagura import workflow, cache, retry, trace

@workflow
@cache(ttl=3600)
@retry(max_attempts=3)
@trace
async def production_pipeline(input: str) -> dict:
    """Full production-ready workflow"""
    # 複数エージェント組み合わせ
    # メモリ永続化
    # エラーハンドリング
    # 監視
    pass
```

---

## まとめ

Kagura AI 2.0は、**Pythonコードだけで完結するAIエージェントフレームワーク**として再出発する。

**コアバリュー**:
1. **Simplicity**: 5行でプロダクション級エージェント
2. **Type Safety**: 型がすべて
3. **Zero Config**: 設定ファイル不要
4. **Composability**: 関数のように組み合わせ可能

**キャッチフレーズ**:
> "AI Agents as Simple as Functions"

これが、Kagura AIの未来です。
