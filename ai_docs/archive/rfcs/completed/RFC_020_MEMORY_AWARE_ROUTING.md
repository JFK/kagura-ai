# RFC-020: Memory-Aware Routing - メモリ対応ルーティング

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-10
- **関連Issue**: #108
- **優先度**: Medium

## 概要

Agent Routingシステムに過去の会話履歴やコンテキストを考慮する機能を追加し、より適切なエージェント選択を実現します。

### 目標
- 会話履歴を考慮したルーティング
- ユーザーの意図をより正確に理解
- コンテキストの継続性を保つ
- ルーティング精度の向上

### 非目標
- 全く新しいルーティング戦略の作成
- 既存ルーティングの破壊的変更

## モチベーション

### 現在の課題

現在のRoutingは単一クエリのみを考慮：

```python
# 現状：単一クエリのみでルーティング
router = SemanticRouter()
router.add_route("translation", translation_agent)
router.add_route("code_review", review_agent)

# 前の会話を考慮しない
agent = await router.route("How about this one?")
# ⚠️ "this one"が何を指すか分からない
```

**問題**:
1. 代名詞や省略表現が理解できない
2. 会話の流れを無視
3. ユーザーが明示的に指定する必要がある

### 解決するユースケース

**ケース1: 代名詞の解決**
```
User: Translate "Hello" to Japanese
→ translation_agent選択

User: Now to French
→ 会話履歴から"translation"タスクと認識
→ translation_agent選択（正しい）
```

**ケース2: コンテキストの継続**
```
User: Review this code: [code]
→ code_review_agent選択

User: What about performance?
→ 会話履歴から"code review"のコンテキスト維持
→ code_review_agent選択（正しい）
```

**ケース3: タスク切り替えの検出**
```
User: Review this code: [code]
→ code_review_agent選択

User: By the way, translate this: "Hello"
→ 明確なタスク切り替えを検出
→ translation_agent選択（正しい）
```

### なぜ今実装すべきか
- RFC-016でルーティングの基礎実装完了
- RFC-018でメモリシステム実装完了
- 両者を統合することで価値向上

## 設計

### アーキテクチャ

```
┌──────────────────────────────────────┐
│     User Query + Context             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│   Memory-Aware Router                │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  1. Query Analysis             │ │
│  │     - Detect pronouns          │ │
│  │     - Identify task keywords   │ │
│  └───────────┬────────────────────┘ │
│              │                       │
│              ▼                       │
│  ┌────────────────────────────────┐ │
│  │  2. Context Retrieval          │ │
│  │     - Get recent messages      │ │
│  │     - Get semantic context     │ │
│  └───────────┬────────────────────┘ │
│              │                       │
│              ▼                       │
│  ┌────────────────────────────────┐ │
│  │  3. Context-Enhanced Routing   │ │
│  │     - Combine query + context  │ │
│  │     - Route selection          │ │
│  └───────────┬────────────────────┘ │
│              │                       │
└──────────────┼───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│        Selected Agent                │
└──────────────────────────────────────┘
```

### API設計

#### 基本的な使い方

```python
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

# メモリマネージャーを渡す
memory = MemoryManager(agent_name="assistant", enable_rag=True)
router = MemoryAwareRouter(memory=memory)

# ルート登録
router.add_route("translation", translation_agent)
router.add_route("code_review", review_agent)
router.add_route("summarization", summary_agent)

# コンテキスト考慮したルーティング
agent = await router.route("What about this one?")
# メモリから前の会話を取得して適切なエージェント選択
```

#### 設定オプション

```python
router = MemoryAwareRouter(
    memory=memory,
    context_window=5,           # 直近5メッセージを考慮
    use_semantic_context=True,  # RAGでセマンティック検索
    fallback_strategy="llm",    # コンテキスト不明時の戦略
)
```

### コンポーネント設計

#### 1. MemoryAwareRouter

```python
# src/kagura/routing/memory_aware.py
from typing import Optional, Callable
from kagura.core.memory import MemoryManager
from kagura.routing import BaseRouter

class MemoryAwareRouter(BaseRouter):
    """Router that considers conversation history"""

    def __init__(
        self,
        memory: MemoryManager,
        context_window: int = 5,
        use_semantic_context: bool = True,
        fallback_strategy: str = "llm",
    ):
        super().__init__()
        self.memory = memory
        self.context_window = context_window
        self.use_semantic_context = use_semantic_context
        self.fallback_strategy = fallback_strategy

    async def route(self, query: str) -> Callable:
        """Route with memory context"""
        # 1. Query analysis
        needs_context = self._needs_context(query)

        if not needs_context:
            # Direct routing for explicit queries
            return await self._route_direct(query)

        # 2. Context retrieval
        context = await self._retrieve_context(query)

        # 3. Context-enhanced routing
        enhanced_query = self._enhance_query(query, context)
        return await self._route_with_context(enhanced_query)

    def _needs_context(self, query: str) -> bool:
        """Check if query needs context"""
        # Detect pronouns and implicit references
        pronouns = ["this", "that", "it", "them", "those", "these"]
        question_words = ["what", "how", "why"]

        query_lower = query.lower()

        # Has pronouns without explicit subject
        if any(p in query_lower for p in pronouns):
            return True

        # Short question without clear intent
        if any(q in query_lower for q in question_words) and len(query.split()) < 5:
            return True

        return False

    async def _retrieve_context(self, query: str) -> dict:
        """Retrieve conversation context"""
        context = {
            "recent_messages": [],
            "semantic_context": [],
        }

        # Get recent messages
        messages = self.memory.context.get_messages(limit=self.context_window)
        context["recent_messages"] = messages

        # Get semantic context (if RAG enabled)
        if self.use_semantic_context and self.memory.rag:
            semantic_results = self.memory.recall_semantic(query, top_k=3)
            context["semantic_context"] = semantic_results

        return context

    def _enhance_query(self, query: str, context: dict) -> str:
        """Enhance query with context"""
        enhanced_parts = [query]

        # Add recent messages
        if context["recent_messages"]:
            recent = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in context["recent_messages"][-3:]
            ])
            enhanced_parts.append(f"\n\nRecent conversation:\n{recent}")

        # Add semantic context
        if context["semantic_context"]:
            semantic = "\n".join([
                result["content"]
                for result in context["semantic_context"][:2]
            ])
            enhanced_parts.append(f"\n\nRelevant context:\n{semantic}")

        return "\n".join(enhanced_parts)

    async def _route_with_context(self, enhanced_query: str) -> Callable:
        """Route using enhanced query"""
        # Use base routing strategy with enhanced query
        return await super().route(enhanced_query)

    async def _route_direct(self, query: str) -> Callable:
        """Direct routing without context"""
        return await super().route(query)
```

#### 2. Context Analyzer

```python
# src/kagura/routing/context_analyzer.py
from typing import Optional

class ContextAnalyzer:
    """Analyze queries for context dependencies"""

    PRONOUNS = ["this", "that", "it", "they", "them", "those", "these"]
    IMPLICIT_WORDS = ["also", "too", "again", "more"]

    def needs_context(self, query: str) -> bool:
        """Determine if query needs context"""
        return (
            self._has_pronouns(query)
            or self._has_implicit_reference(query)
            or self._is_followup_question(query)
        )

    def _has_pronouns(self, query: str) -> bool:
        """Check for pronouns"""
        return any(p in query.lower().split() for p in self.PRONOUNS)

    def _has_implicit_reference(self, query: str) -> bool:
        """Check for implicit references"""
        return any(w in query.lower() for w in self.IMPLICIT_WORDS)

    def _is_followup_question(self, query: str) -> bool:
        """Check if it's a follow-up question"""
        followup_starters = ["what about", "how about", "and", "but"]
        return any(query.lower().startswith(s) for s in followup_starters)

    def extract_intent_from_context(
        self, query: str, messages: list[dict]
    ) -> Optional[str]:
        """Extract intent from conversation history"""
        if not messages:
            return None

        # Look for task keywords in recent messages
        task_keywords = {
            "translation": ["translate", "翻訳", "language"],
            "code_review": ["review", "code", "analyze"],
            "summarization": ["summary", "summarize", "要約"],
        }

        # Check last few messages
        for msg in reversed(messages[-3:]):
            content = msg["content"].lower()
            for task, keywords in task_keywords.items():
                if any(k in content for k in keywords):
                    return task

        return None
```

### 統合例

#### 例1: 基本的な会話継続

```python
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="assistant")
router = MemoryAwareRouter(memory=memory)

router.add_route("translation", translation_agent)
router.add_route("code_review", review_agent)

# First query - explicit
agent = await router.route("Translate 'Hello' to Japanese")
# → translation_agent

result = await agent("Translate 'Hello' to Japanese")
memory.add_message("user", "Translate 'Hello' to Japanese")
memory.add_message("assistant", result)

# Follow-up query - implicit
agent = await router.route("How about French?")
# → Looks at context, finds "translation" → translation_agent

result = await agent("How about French?")
```

#### 例2: セマンティックコンテキスト

```python
# RAG有効化
memory = MemoryManager(agent_name="assistant", enable_rag=True)
router = MemoryAwareRouter(memory=memory, use_semantic_context=True)

# Store semantic context
memory.store_semantic("User prefers detailed code reviews with security focus")
memory.store_semantic("User works with Python and React")

# Query
agent = await router.route("Review this code")
# → Retrieves semantic context → code_review_agent with context
```

#### 例3: AgentBuilderとの統合

```python
from kagura import AgentBuilder
from kagura.routing import MemoryAwareRouter

agent = (
    AgentBuilder("smart_agent")
    .with_memory(type="rag", enable_rag=True)
    .with_routing(
        strategy="memory_aware",  # NEW
        context_window=5,
        routes={
            "translation": translation_agent,
            "code_review": review_agent,
        }
    )
    .build()
)

# Automatically uses memory-aware routing
await agent("Translate 'Hello'")
await agent("What about 'Goodbye'?")  # Context-aware
```

## 実装計画

### Phase 1: Core Implementation (v2.2.0) - 1週間
- [ ] MemoryAwareRouter実装
- [ ] ContextAnalyzer実装
- [ ] 基本的な代名詞検出
- [ ] テスト

### Phase 2: Advanced Features (v2.2.0) - 3日
- [ ] セマンティックコンテキスト統合
- [ ] Intent extraction from history
- [ ] Fallback策の実装

### Phase 3: Optimization (v2.3.0)
- [ ] パフォーマンス最適化
- [ ] キャッシング戦略
- [ ] より高度な自然言語理解

## 技術的詳細

### 依存関係

既存のKagura依存関係のみ（新規追加なし）

### パフォーマンス考慮

```python
class MemoryAwareRouter(BaseRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context_cache = {}  # Cache context lookups
        self._cache_ttl = 60      # Cache for 60 seconds

    async def _retrieve_context(self, query: str) -> dict:
        # Check cache first
        cache_key = f"{query}:{time.time() // self._cache_ttl}"
        if cache_key in self._context_cache:
            return self._context_cache[cache_key]

        # Retrieve and cache
        context = await self._do_retrieve_context(query)
        self._context_cache[cache_key] = context
        return context
```

## テスト戦略

### ユニットテスト

```python
def test_needs_context_with_pronoun():
    router = MemoryAwareRouter(memory=mock_memory)
    assert router._needs_context("What about this one?")
    assert not router._needs_context("Translate hello to Japanese")

@pytest.mark.asyncio
async def test_context_retrieval():
    memory = MemoryManager(agent_name="test")
    memory.add_message("user", "Translate hello")
    memory.add_message("assistant", "こんにちは")

    router = MemoryAwareRouter(memory=memory)
    context = await router._retrieve_context("What about goodbye?")

    assert len(context["recent_messages"]) == 2
```

### 統合テスト

```python
@pytest.mark.asyncio
async def test_memory_aware_routing():
    memory = MemoryManager(agent_name="test")
    router = MemoryAwareRouter(memory=memory)

    router.add_route("translation", translation_agent)
    router.add_route("code_review", review_agent)

    # First explicit query
    agent1 = await router.route("Translate hello")
    assert agent1 == translation_agent

    # Store context
    memory.add_message("user", "Translate hello")

    # Follow-up implicit query
    agent2 = await router.route("What about goodbye?")
    assert agent2 == translation_agent  # Same agent due to context
```

## ドキュメント

### 必要なドキュメント
1. Memory-Aware Routing クイックスタート
2. コンテキスト分析の仕組み
3. パフォーマンスチューニングガイド
4. ベストプラクティス

### サンプルコード
- 会話継続の例
- セマンティックコンテキストの利用
- カスタムコンテキスト分析

## 未解決の問題

1. **多言語対応**: 日本語の代名詞検出
2. **複雑な会話**: 複数のタスクが混在する場合
3. **プライバシー**: どこまでコンテキストを保存するか

## 参考資料

- [Conversational AI Context Management](https://arxiv.org/abs/2012.15025)
- [Dialogue State Tracking](https://aclanthology.org/)

## 改訂履歴

- 2025-10-10: 初版作成
