# RFC-019: Unified Agent Builder - 統合エージェントビルダー

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-10
- **関連Issue**: #107
- **優先度**: High

## 概要

複数の機能（Memory、Routing、Tools、Hooks等）を簡単に組み合わせられる統合的なエージェントビルダーを提供します。

### 目標
- 複数機能の統合を簡単に
- 一貫性のあるAPI設計
- 型安全なビルダーパターン
- デフォルト設定の賢い選択

### 非目標
- 既存の`@agent`デコレータの置き換え
- 破壊的な変更

## モチベーション

### 現在の課題
1. 複数機能を使う際の設定が煩雑
2. 各機能が独立しており統合が難しい
3. デフォルト設定の選択が不明確
4. 初心者にとって学習コストが高い

```python
# 現状：複数の設定が必要
from kagura import agent
from kagura.core.memory import MemoryManager
from kagura.routing import SemanticRouter

memory = MemoryManager(agent_name="assistant", enable_rag=True)
router = SemanticRouter()

@agent(model="gpt-4o-mini")
async def my_agent(query: str) -> str:
    # メモリ、ルーティングを手動で管理
    pass
```

### 解決するユースケース
- **簡単な統合**: 複数機能を数行で組み合わせ
- **プリセット**: 一般的な構成をプリセットとして提供
- **段階的な学習**: シンプルから始めて徐々に機能追加
- **一貫性**: 統一されたAPI

### なぜ今実装すべきか
- v2.1.0で多くの機能が実装された
- 統合性の欠如がユーザビリティの障壁に
- 早期に統一APIを提供すべき

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────┐
│      AgentBuilder (Fluent API)      │
│                                     │
│  .with_memory(type="rag")           │
│  .with_routing(strategy="semantic") │
│  .with_tools([tool1, tool2])        │
│  .with_hooks(pre=hook1)             │
│  .build()                           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        AgentConfiguration           │
│  - Memory config                    │
│  - Routing config                   │
│  - Tools config                     │
│  - Hooks config                     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         Enhanced Agent              │
│  - Original @agent functionality    │
│  - + Integrated features            │
└─────────────────────────────────────┘
```

### API設計

#### 基本的な使い方

```python
from kagura import AgentBuilder

# シンプルなエージェント
agent = (
    AgentBuilder("my_agent")
    .with_model("gpt-4o-mini")
    .build()
)

result = await agent("Hello")
```

#### 全機能を使う例

```python
from kagura import AgentBuilder
from kagura.tools import search_tool, calculate_tool
from kagura.hooks import validation_hook, logging_hook

agent = (
    AgentBuilder("advanced_agent")
    .with_model("gpt-4o-mini")
    .with_memory(
        type="rag",                    # working, context, persistent, rag
        persist_dir="/path/to/memory",
        max_messages=100
    )
    .with_routing(
        strategy="semantic",           # keyword, llm, semantic
        routes={
            "translation": translation_agent,
            "code_review": review_agent,
        }
    )
    .with_tools([search_tool, calculate_tool])
    .with_hooks(
        pre=[validation_hook],
        post=[logging_hook]
    )
    .with_context(
        temperature=0.7,
        max_tokens=2000
    )
    .build()
)

# 使用
result = await agent("Translate this to Japanese")
```

#### プリセット

```python
from kagura.presets import ChatbotPreset, CodeReviewPreset, ResearchPreset

# プリセットベースのカスタマイズ
agent = (
    ChatbotPreset("my_chatbot")
    .with_model("gpt-4o-mini")
    .customize(temperature=0.8)
    .build()
)

# 利用可能なプリセット
# - ChatbotPreset: メモリ有効、会話履歴管理
# - CodeReviewPreset: コード分析ツール、静的解析統合
# - ResearchPreset: Web検索、RAGメモリ、要約機能
# - TranslationPreset: 複数言語対応、用語辞書
```

### コンポーネント設計

#### 1. AgentBuilder

```python
# src/kagura/builder/agent_builder.py
from typing import Optional, Any, Callable
from pathlib import Path

class AgentBuilder:
    """Fluent API for building agents with integrated features"""

    def __init__(self, name: str):
        self.name = name
        self._config = AgentConfiguration()

    def with_model(self, model: str) -> "AgentBuilder":
        """Set LLM model"""
        self._config.model = model
        return self

    def with_memory(
        self,
        type: str = "working",           # working, context, persistent, rag
        persist_dir: Optional[Path] = None,
        max_messages: int = 100,
        enable_rag: bool = False,
    ) -> "AgentBuilder":
        """Configure memory system"""
        self._config.memory = MemoryConfig(
            type=type,
            persist_dir=persist_dir,
            max_messages=max_messages,
            enable_rag=enable_rag,
        )
        return self

    def with_routing(
        self,
        strategy: str = "semantic",      # keyword, llm, semantic
        routes: Optional[dict] = None,
    ) -> "AgentBuilder":
        """Configure agent routing"""
        self._config.routing = RoutingConfig(
            strategy=strategy,
            routes=routes or {},
        )
        return self

    def with_tools(self, tools: list[Callable]) -> "AgentBuilder":
        """Add tools to agent"""
        self._config.tools = tools
        return self

    def with_hooks(
        self,
        pre: Optional[list[Callable]] = None,
        post: Optional[list[Callable]] = None,
    ) -> "AgentBuilder":
        """Add pre/post hooks"""
        self._config.hooks = HooksConfig(
            pre=pre or [],
            post=post or [],
        )
        return self

    def with_context(self, **kwargs: Any) -> "AgentBuilder":
        """Set LLM generation parameters"""
        self._config.context.update(kwargs)
        return self

    def build(self) -> Callable:
        """Build the final agent"""
        return self._build_agent()

    def _build_agent(self) -> Callable:
        """Internal: construct the agent with all features"""
        from kagura import agent
        from kagura.core.memory import MemoryManager
        from kagura.routing import create_router

        # Build base agent
        @agent(model=self._config.model, **self._config.context)
        async def enhanced_agent(*args, **kwargs):
            # Integrate memory
            if self._config.memory:
                memory = MemoryManager(
                    agent_name=self.name,
                    **self._config.memory.dict()
                )
                # Use memory in agent

            # Integrate routing
            if self._config.routing:
                router = create_router(
                    strategy=self._config.routing.strategy,
                    routes=self._config.routing.routes
                )
                # Use router to select agent

            # Integrate tools
            if self._config.tools:
                # Make tools available to agent
                pass

            # Execute with hooks
            if self._config.hooks:
                # Run pre-hooks
                for hook in self._config.hooks.pre:
                    await hook(*args, **kwargs)

            # Main execution
            result = "TODO: execute agent"

            if self._config.hooks:
                # Run post-hooks
                for hook in self._config.hooks.post:
                    await hook(result)

            return result

        return enhanced_agent
```

#### 2. Configuration Classes

```python
# src/kagura/builder/config.py
from pydantic import BaseModel
from typing import Optional, Any, Callable
from pathlib import Path

class MemoryConfig(BaseModel):
    type: str = "working"
    persist_dir: Optional[Path] = None
    max_messages: int = 100
    enable_rag: bool = False

class RoutingConfig(BaseModel):
    strategy: str = "semantic"
    routes: dict[str, Callable] = {}

class HooksConfig(BaseModel):
    pre: list[Callable] = []
    post: list[Callable] = []

class AgentConfiguration(BaseModel):
    model: str = "gpt-4o-mini"
    memory: Optional[MemoryConfig] = None
    routing: Optional[RoutingConfig] = None
    tools: list[Callable] = []
    hooks: Optional[HooksConfig] = None
    context: dict[str, Any] = {}
```

#### 3. Presets

```python
# src/kagura/presets/chatbot.py
from kagura.builder import AgentBuilder

class ChatbotPreset(AgentBuilder):
    """Preset for conversational chatbots"""

    def __init__(self, name: str):
        super().__init__(name)
        # Default configuration for chatbots
        self.with_memory(
            type="context",
            max_messages=100
        ).with_context(
            temperature=0.8,
            max_tokens=1000
        )

# src/kagura/presets/research.py
class ResearchPreset(AgentBuilder):
    """Preset for research and analysis tasks"""

    def __init__(self, name: str):
        super().__init__(name)
        from kagura.builtin.web import search_tool

        self.with_memory(
            type="rag",
            enable_rag=True
        ).with_tools([search_tool]).with_context(
            temperature=0.3,
            max_tokens=2000
        )
```

### 統合例

#### 例1: シンプルなチャットボット

```python
from kagura import AgentBuilder

chatbot = (
    AgentBuilder("chatbot")
    .with_model("gpt-4o-mini")
    .with_memory(type="context", max_messages=50)
    .build()
)

# 会話履歴が自動的に管理される
await chatbot("Hello!")
await chatbot("What's my name?")  # 前の会話を覚えている
```

#### 例2: プリセットを使った研究アシスタント

```python
from kagura.presets import ResearchPreset

researcher = (
    ResearchPreset("researcher")
    .with_model("gpt-4o")
    .customize(max_tokens=4000)
    .build()
)

result = await researcher("Research the latest trends in AI")
# 自動的にWeb検索、RAGメモリ使用
```

#### 例3: 完全カスタマイズ

```python
from kagura import AgentBuilder
from my_tools import custom_db_tool, custom_api_tool
from my_hooks import auth_hook, audit_hook

agent = (
    AgentBuilder("enterprise_agent")
    .with_model("gpt-4o")
    .with_memory(
        type="rag",
        persist_dir="/data/memory",
        enable_rag=True
    )
    .with_routing(
        strategy="llm",
        routes={
            "database": db_agent,
            "api": api_agent,
        }
    )
    .with_tools([custom_db_tool, custom_api_tool])
    .with_hooks(
        pre=[auth_hook],
        post=[audit_hook]
    )
    .with_context(
        temperature=0.2,
        max_tokens=3000
    )
    .build()
)
```

## 実装計画

### Phase 1: Core Builder (v2.2.0) - 1週間
- [ ] AgentBuilder基本実装
- [ ] Configuration classes
- [ ] 基本的な統合（memory, tools）
- [ ] テスト・ドキュメント

### Phase 2: Advanced Features (v2.2.0) - 1週間
- [ ] Routing統合
- [ ] Hooks統合
- [ ] Preset実装（3-5種類）
- [ ] サンプル・チュートリアル

### Phase 3: Enhanced Presets (v2.3.0)
- [ ] 10+のプリセット
- [ ] カスタムプリセット作成API
- [ ] プリセット共有機能

## 技術的詳細

### 依存関係

既存のKagura依存関係のみ（新規追加なし）

### 型安全性

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class TypedAgentBuilder(Generic[T]):
    """Type-safe agent builder"""

    def build(self) -> Callable[..., T]:
        """Returns typed agent"""
        pass

# Usage with type hints
builder: TypedAgentBuilder[str] = AgentBuilder("my_agent")
agent: Callable[..., str] = builder.build()
```

## テスト戦略

### ユニットテスト

```python
def test_agent_builder_basic():
    agent = AgentBuilder("test").build()
    assert agent is not None

def test_agent_builder_with_memory():
    agent = (
        AgentBuilder("test")
        .with_memory(type="context")
        .build()
    )
    assert agent._config.memory is not None

def test_preset_initialization():
    from kagura.presets import ChatbotPreset
    agent = ChatbotPreset("chatbot").build()
    assert agent._config.memory.type == "context"
```

### 統合テスト

```python
@pytest.mark.asyncio
async def test_full_integration():
    agent = (
        AgentBuilder("integration_test")
        .with_model("gpt-4o-mini")
        .with_memory(type="working")
        .with_tools([test_tool])
        .build()
    )

    result = await agent("test query")
    assert result is not None
```

## ドキュメント

### 必要なドキュメント
1. Agent Builder クイックスタート
2. 各設定オプションの詳細説明
3. プリセット一覧とカスタマイズ方法
4. マイグレーションガイド（@agentからBuilderへ）

### サンプルコード
- 各プリセットの使用例
- カスタムビルダーパターン
- 段階的な機能追加例

## 代替案

### 案1: クラスベースのビルダー
```python
class MyAgent(AgentBuilder):
    def __init__(self):
        super().__init__("my_agent")
        self.with_memory(...)
```
**却下理由**: Fluent APIの方が直感的

### 案2: 設定ファイルベース
```yaml
# agent.yml
name: my_agent
memory:
  type: rag
tools:
  - search
```
**却下理由**: Python-firstの哲学に反する

## 未解決の問題

1. **パフォーマンス**: 多機能統合時のオーバーヘッド
2. **デバッグ**: ビルダーで構築したエージェントのエラー追跡
3. **後方互換性**: 既存の`@agent`との共存

## 参考資料

- [Fluent Interface Pattern](https://en.wikipedia.org/wiki/Fluent_interface)
- [Builder Pattern in Python](https://refactoring.guru/design-patterns/builder/python/example)

## 改訂履歴

- 2025-10-10: 初版作成
