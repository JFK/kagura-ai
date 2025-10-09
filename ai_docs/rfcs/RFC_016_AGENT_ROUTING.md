# RFC-016: Agent Routing System - インテリジェントエージェントルーティング

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-06
- **関連Issue**: #87
- **優先度**: High

## 概要

ユーザーの入力や意図に基づいて、最適なエージェントを自動的に選択・実行するルーティングシステムを実装します。複数のエージェントが登録されている環境で、ユーザーは明示的にエージェントを指定せず、自然言語で要求を伝えるだけで適切なエージェントが自動選択されます。

### 目標
- **Intent-based Routing**: ユーザーの意図に基づいて最適なエージェントを選択
- **Semantic Routing**: 埋め込みベクトルによる意味的類似度判定
- **Chain Routing**: 複数エージェントの自動連携
- **Fallback Mechanism**: ルーティング失敗時の適切なフォールバック
- **RFC-009統合**: Multi-Agent OrchestrationとのシームレスなAGENT統合

### 非目標
- 完全自律型AIシステム（人間の判断を尊重）
- エージェント自動生成（RFC-005 Meta Agentの領域）

## モチベーション

### 現在の課題
1. エージェントを明示的に指定する必要がある
2. 適切なエージェントの選択がユーザー任せ
3. 複数エージェント間の連携が手動
4. 新しいエージェント追加時のユーザー学習コスト

### 解決するユースケース
- **チャットボット**: 「このコードレビューして」→ 自動的にcode_review_agentを選択
- **マルチタスク処理**: 「データ分析してレポート作成」→ 複数エージェントを自動連携
- **プラグイン管理**: 多数のカスタムエージェントから最適なものを自動選択
- **コンテキスト理解**: 会話履歴から適切なエージェントへルーティング

### なぜ今実装すべきか
- v2.0.0の基盤が完成
- RFC-009（Multi-Agent Orchestration）との統合タイミングが最適
- Chat REPL（RFC-006）での UX向上に貢献
- エコシステム拡大（RFC-008 Plugin Marketplace）の基盤

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         User Input                          │
│   "このコードをレビューして"                │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│         Agent Router                        │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Intent Classifier                  │   │
│  │  - Keyword matching                 │   │
│  │  - Pattern recognition              │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│  ┌──────────────▼──────────────────────┐   │
│  │  Semantic Matcher                   │   │
│  │  - Embedding similarity             │   │
│  │  - Vector search                    │   │
│  └──────────────┬──────────────────────┘   │
│                 │                           │
│  ┌──────────────▼──────────────────────┐   │
│  │  Agent Selector                     │   │
│  │  - Confidence scoring               │   │
│  │  - Fallback handling                │   │
│  └──────────────┬──────────────────────┘   │
└─────────────────┼───────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Agent A  │ │ Agent B  │ │ Agent C  │
│ (Review) │ │(Translate)│ │(Analyze) │
└──────────┘ └──────────┘ └──────────┘
```

### コンポーネント設計

#### 1. Intent-based Agent Routing

キーワード・パターンベースの基本ルーティング：

```python
from kagura import agent, AgentRouter

# エージェント定義
@agent(model="gpt-4o", description="Code review and quality analysis")
async def code_reviewer(code: str) -> str:
    """Review code: {{ code }}"""
    pass

@agent(model="gpt-4o-mini", description="Translate text between languages")
async def translator(text: str, target_lang: str) -> str:
    """Translate {{ text }} to {{ target_lang }}"""
    pass

@agent(model="gpt-4o", description="Data analysis and statistics")
async def data_analyzer(data: dict) -> dict:
    """Analyze data: {{ data }}"""
    pass

# ルーター作成
router = AgentRouter()

# エージェント登録（意図パターンと一緒に）
router.register(
    agent=code_reviewer,
    intents=["review", "check", "analyze code", "code quality"],
    description="Reviews code for quality, bugs, and best practices"
)

router.register(
    agent=translator,
    intents=["translate", "翻訳", "translation"],
    description="Translates text between different languages"
)

router.register(
    agent=data_analyzer,
    intents=["analyze", "statistics", "データ分析"],
    description="Analyzes data and provides statistical insights"
)

# 自動ルーティング
result = await router.route("このコードをレビューして")
# → code_reviewer が自動選択・実行される

result = await router.route("Translate 'Hello' to Japanese")
# → translator が自動選択される
```

#### 2. Semantic Agent Routing

埋め込みベクトルによる意味的類似度ルーティング：

```python
from kagura import agent, SemanticRouter

router = SemanticRouter(
    embedding_model="text-embedding-3-small",
    threshold=0.7  # 類似度閾値
)

# エージェント登録（サンプルクエリと一緒に）
router.register(
    agent=code_reviewer,
    samples=[
        "Can you review this code?",
        "このコードに問題ないですか？",
        "Check my implementation",
        "Code quality check needed"
    ]
)

router.register(
    agent=translator,
    samples=[
        "Translate this to English",
        "日本語に翻訳して",
        "What does this mean in French?",
        "Convert to Spanish"
    ]
)

# 意味ベースルーティング
result = await router.route("Could you look at my Python script?")
# → code_reviewer が選択される（"review this code"と意味的に類似）

result = await router.route("英語で何て言う？")
# → translator が選択される（"Translate to English"と類似）
```

#### 3. Chain Routing

複数エージェントの自動連携：

```python
from kagura import AgentChain

# チェーン定義
chain = AgentChain("data-pipeline")

# エージェントを順次登録
chain.add(
    agent=data_collector,
    description="Collects data from various sources"
)
chain.add(
    agent=data_cleaner,
    description="Cleans and validates collected data"
)
chain.add(
    agent=data_analyzer,
    description="Analyzes cleaned data"
)
chain.add(
    agent=report_generator,
    description="Generates reports from analysis"
)

# チェーン実行（自動的に順次実行）
result = await chain.run("Analyze sales data from API")
# → 4つのエージェントが順次実行される

# 部分実行も可能
result = await chain.run_from("data_cleaner", input_data=raw_data)
# → data_cleaner以降を実行
```

#### 4. Conditional Routing

条件分岐ルーティング：

```python
from kagura import ConditionalRouter

router = ConditionalRouter()

# 条件付きルート定義
@router.route_if(lambda input: "code" in input.lower())
async def handle_code_request(input: str):
    """Handle code-related requests"""
    if "review" in input.lower():
        return await code_reviewer(input)
    elif "generate" in input.lower():
        return await code_generator(input)
    else:
        return await general_code_agent(input)

@router.route_if(lambda input: "翻訳" in input or "translate" in input.lower())
async def handle_translation(input: str):
    """Handle translation requests"""
    return await translator(input)

# デフォルトルート
@router.default_route
async def handle_general(input: str):
    """Default handler for unmatched requests"""
    return await general_assistant(input)

# 実行
result = await router.route("このコードをレビューして")
# → handle_code_request → code_reviewer

result = await router.route("今日の天気は？")
# → handle_general → general_assistant
```

#### 5. Dynamic Multi-Agent Routing

複数エージェントを並列実行して最良の結果を選択：

```python
from kagura import MultiAgentRouter

router = MultiAgentRouter(
    strategy="best_of_n",  # または "vote", "ensemble"
    max_agents=3
)

router.register_all([
    code_reviewer_gpt4,
    code_reviewer_claude,
    code_reviewer_gemini
])

# 3つのエージェントを並列実行し、最良の結果を選択
result = await router.route("Review this function")
# → 3つのレビューを実行し、スコアリングして最良を返す

# 投票戦略
router_vote = MultiAgentRouter(strategy="vote")
result = await router_vote.route("Is this code secure?")
# → 複数エージェントの多数決で判断
```

#### 6. Context-aware Routing

会話履歴・コンテキストを考慮したルーティング：

```python
from kagura import ContextualRouter

router = ContextualRouter()

# セッション開始
session = router.create_session()

# 会話履歴を蓄積しながらルーティング
result1 = await session.route("データを分析して")
# → data_analyzer

result2 = await session.route("それをグラフ化して")
# → 前回のコンテキストから data_visualizer を選択

result3 = await session.route("ついでにレポートも")
# → report_generator（data_analyzerの結果を引き継ぐ）
```

### API設計

#### AgentRouter クラス

```python
from kagura import agent, AgentRouter
from typing import Callable, Optional, Any

class AgentRouter:
    """Route user input to appropriate agents"""

    def __init__(
        self,
        strategy: str = "intent",  # "intent" | "semantic" | "hybrid"
        fallback_agent: Optional[Callable] = None,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize agent router.

        Args:
            strategy: Routing strategy
            fallback_agent: Default agent when no match found
            confidence_threshold: Minimum confidence for routing
        """
        pass

    def register(
        self,
        agent: Callable,
        intents: list[str] = None,
        samples: list[str] = None,
        description: str = "",
        name: str = None
    ) -> None:
        """
        Register an agent with routing patterns.

        Args:
            agent: Agent function
            intents: Intent keywords/patterns
            samples: Sample queries for semantic matching
            description: Agent description
            name: Agent name (defaults to function name)
        """
        pass

    async def route(
        self,
        user_input: str,
        context: dict[str, Any] = None,
        **kwargs
    ) -> Any:
        """
        Route user input to appropriate agent.

        Args:
            user_input: User's natural language input
            context: Optional context information
            **kwargs: Additional arguments to pass to agent

        Returns:
            Agent execution result

        Raises:
            NoAgentFoundError: When no suitable agent found
        """
        pass

    def get_matched_agents(
        self,
        user_input: str,
        top_k: int = 3
    ) -> list[tuple[Callable, float]]:
        """
        Get top-k matched agents with confidence scores.

        Args:
            user_input: User input
            top_k: Number of top matches to return

        Returns:
            List of (agent, confidence_score) tuples
        """
        pass
```

#### AgentChain クラス

```python
from kagura import AgentChain

class AgentChain:
    """Chain multiple agents for sequential execution"""

    def __init__(self, name: str):
        """
        Initialize agent chain.

        Args:
            name: Chain name
        """
        pass

    def add(
        self,
        agent: Callable,
        description: str = "",
        condition: Optional[Callable] = None
    ) -> "AgentChain":
        """
        Add agent to chain.

        Args:
            agent: Agent function
            description: Step description
            condition: Optional condition function

        Returns:
            Self for chaining
        """
        pass

    async def run(
        self,
        initial_input: Any,
        **kwargs
    ) -> Any:
        """
        Execute entire chain.

        Args:
            initial_input: Initial input to first agent
            **kwargs: Additional arguments

        Returns:
            Final agent output
        """
        pass

    async def run_from(
        self,
        agent_name: str,
        input_data: Any
    ) -> Any:
        """
        Execute chain from specific agent.

        Args:
            agent_name: Starting agent name
            input_data: Input for starting agent

        Returns:
            Final output
        """
        pass
```

### 統合例

#### 例1: Chat REPL with Auto-Routing

```python
from kagura import agent, AgentRouter

# エージェント定義
@agent(model="gpt-4o")
async def code_reviewer(code: str) -> str:
    """Review {{ code }}"""
    pass

@agent(model="gpt-4o-mini")
async def translator(text: str, lang: str = "en") -> str:
    """Translate {{ text }} to {{ lang }}"""
    pass

@agent(model="gpt-4o-mini")
async def general_assistant(query: str) -> str:
    """Help with: {{ query }}"""
    pass

# ルーター設定
router = AgentRouter(fallback_agent=general_assistant)

router.register(
    code_reviewer,
    intents=["review", "check", "レビュー"],
    description="Code review and quality analysis"
)

router.register(
    translator,
    intents=["translate", "翻訳", "translation"],
    description="Text translation"
)

# Chat REPL統合
async def chat_loop():
    print("Kagura Chat (with Auto-Routing)")

    while True:
        user_input = input("You: ")

        if user_input == "/exit":
            break

        # 自動ルーティング
        result = await router.route(user_input)

        print(f"AI: {result}\n")

# 実行
await chat_loop()

# 使用例:
# You: このコードをレビューして [コード]
# AI: [code_reviewerの結果]
#
# You: "Hello"を日本語に翻訳
# AI: [translatorの結果]
#
# You: 今日の天気は？
# AI: [general_assistantの結果]
```

#### 例2: Multi-Agent Data Pipeline

```python
from kagura import agent, AgentChain

@agent(model="gpt-4o-mini")
async def fetch_data(source: str) -> dict:
    """Fetch data from {{ source }}"""
    pass

@agent(model="gpt-4o-mini")
async def clean_data(raw_data: dict) -> dict:
    """Clean data: {{ raw_data }}"""
    pass

@agent(model="gpt-4o")
async def analyze_data(clean_data: dict) -> dict:
    """Analyze: {{ clean_data }}"""
    pass

@agent(model="gpt-4o-mini")
async def generate_report(analysis: dict) -> str:
    """Generate report from: {{ analysis }}"""
    pass

# チェーン構築
pipeline = AgentChain("data-analysis-pipeline")
pipeline.add(fetch_data, "Fetch raw data")
pipeline.add(clean_data, "Clean and validate")
pipeline.add(analyze_data, "Perform analysis")
pipeline.add(generate_report, "Generate final report")

# パイプライン実行
report = await pipeline.run(source="https://api.example.com/data")
print(report)
```

#### 例3: Semantic Routing with Fallback

```python
from kagura import SemanticRouter, agent

@agent(model="gpt-4o")
async def python_expert(question: str) -> str:
    """Python expert: {{ question }}"""
    pass

@agent(model="gpt-4o")
async def javascript_expert(question: str) -> str:
    """JavaScript expert: {{ question }}"""
    pass

@agent(model="gpt-4o")
async def general_dev(question: str) -> str:
    """General developer: {{ question }}"""
    pass

# セマンティックルーター
router = SemanticRouter(
    fallback_agent=general_dev,
    threshold=0.7
)

router.register(
    python_expert,
    samples=[
        "How do I use decorators in Python?",
        "What's the best way to handle async in Python?",
        "Explain Python list comprehensions"
    ]
)

router.register(
    javascript_expert,
    samples=[
        "How does async/await work in JavaScript?",
        "What's the difference between let and const?",
        "Explain JavaScript promises"
    ]
)

# 質問
result = await router.route("Pythonのジェネレータって何？")
# → python_expert が選択される

result = await router.route("What are React hooks?")
# → 閾値未満なので general_dev (fallback) が実行される
```

#### 例4: RFC-009 (Multi-Agent Orchestration) 統合

```python
from kagura import Team, AgentRouter, agent

# チーム作成
team = Team("research-team")

@agent(model="gpt-4o-mini")
async def searcher(query: str) -> list[dict]:
    """Search for: {{ query }}"""
    pass

@agent(model="gpt-4o")
async def analyzer(data: list[dict]) -> dict:
    """Analyze: {{ data }}"""
    pass

@agent(model="gpt-4o-mini")
async def summarizer(analysis: dict) -> str:
    """Summarize: {{ analysis }}"""
    pass

team.add_agent(searcher, name="searcher")
team.add_agent(analyzer, name="analyzer")
team.add_agent(summarizer, name="summarizer")

# チーム内ルーター
team_router = AgentRouter()
team_router.register(searcher, intents=["search", "find", "lookup"])
team_router.register(analyzer, intents=["analyze", "examine", "investigate"])
team_router.register(summarizer, intents=["summarize", "brief", "overview"])

# チームワークフローでルーティング使用
@team.workflow
async def research_workflow(user_request: str):
    # ルーティングで適切なエージェントを選択
    result = await team_router.route(user_request)
    return result

# 実行
result = await research_workflow("Find papers about machine learning")
# → searcher が自動選択される
```

## 実装計画

### Phase 1: Core Routing (v2.4.0)
- [ ] AgentRouter基本実装
- [ ] Intent-based routing（キーワードマッチ）
- [ ] Agent登録・管理API
- [ ] Fallback mechanism
- [ ] 基本的な信頼度スコアリング

### Phase 2: Semantic Routing (v2.4.0)
- [ ] Embedding-based semantic matching
- [ ] Vector similarity search
- [ ] Sample query管理
- [ ] Hybrid routing（Intent + Semantic）

### Phase 3: Chain & Conditional (v2.5.0)
- [ ] AgentChain実装
- [ ] ConditionalRouter
- [ ] Context-aware routing
- [ ] セッション管理

### Phase 4: Advanced Features (v2.5.0+)
- [ ] MultiAgentRouter（並列実行）
- [ ] 投票・アンサンブル戦略
- [ ] Dynamic routing（学習ベース）
- [ ] パフォーマンスモニタリング

### Phase 5: Integration (v2.6.0)
- [ ] RFC-006 Chat REPL統合
- [ ] RFC-009 Multi-Agent Orchestration統合
- [ ] RFC-012 Commands統合
- [ ] Web UI（RFC-015）でのルーティング可視化

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
routing = [
    "scikit-learn>=1.3.0",     # Similarity calculations
    "sentence-transformers>=2.2.0",  # Semantic embeddings
    "numpy>=1.24.0",           # Vector operations
    "faiss-cpu>=1.7.4",        # Fast vector search (optional)
]
```

### AgentRouter Implementation

```python
# src/kagura/routing/router.py
from typing import Callable, Optional, Any
import re
from dataclasses import dataclass

@dataclass
class RegisteredAgent:
    """Registered agent with routing metadata"""
    agent: Callable
    name: str
    intents: list[str]
    samples: list[str]
    description: str
    embedding: Optional[Any] = None

class AgentRouter:
    """Route user input to appropriate agents"""

    def __init__(
        self,
        strategy: str = "intent",
        fallback_agent: Optional[Callable] = None,
        confidence_threshold: float = 0.5
    ):
        self.strategy = strategy
        self.fallback_agent = fallback_agent
        self.threshold = confidence_threshold
        self.agents: dict[str, RegisteredAgent] = {}

    def register(
        self,
        agent: Callable,
        intents: list[str] = None,
        samples: list[str] = None,
        description: str = "",
        name: str = None
    ):
        """Register an agent"""
        agent_name = name or agent.__name__

        self.agents[agent_name] = RegisteredAgent(
            agent=agent,
            name=agent_name,
            intents=intents or [],
            samples=samples or [],
            description=description
        )

    async def route(
        self,
        user_input: str,
        context: dict[str, Any] = None,
        **kwargs
    ) -> Any:
        """Route user input to appropriate agent"""
        # Find best matching agent
        matched_agents = self.get_matched_agents(user_input)

        if not matched_agents:
            # Use fallback
            if self.fallback_agent:
                return await self.fallback_agent(user_input, **kwargs)
            raise NoAgentFoundError(f"No agent found for: {user_input}")

        # Get top match
        best_agent, confidence = matched_agents[0]

        if confidence < self.threshold:
            if self.fallback_agent:
                return await self.fallback_agent(user_input, **kwargs)
            raise NoAgentFoundError(
                f"Low confidence ({confidence:.2f}) for: {user_input}"
            )

        # Execute agent
        return await best_agent(user_input, **kwargs)

    def get_matched_agents(
        self,
        user_input: str,
        top_k: int = 3
    ) -> list[tuple[Callable, float]]:
        """Get top-k matched agents with confidence scores"""
        scores = []

        for agent_data in self.agents.values():
            score = self._calculate_score(user_input, agent_data)
            scores.append((agent_data.agent, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]

    def _calculate_score(
        self,
        user_input: str,
        agent_data: RegisteredAgent
    ) -> float:
        """Calculate matching score"""
        if self.strategy == "intent":
            return self._intent_score(user_input, agent_data.intents)
        elif self.strategy == "semantic":
            return self._semantic_score(user_input, agent_data.samples)
        elif self.strategy == "hybrid":
            intent_score = self._intent_score(user_input, agent_data.intents)
            semantic_score = self._semantic_score(user_input, agent_data.samples)
            return 0.6 * intent_score + 0.4 * semantic_score
        else:
            return 0.0

    def _intent_score(self, user_input: str, intents: list[str]) -> float:
        """Calculate intent-based score"""
        if not intents:
            return 0.0

        input_lower = user_input.lower()
        matches = sum(1 for intent in intents if intent.lower() in input_lower)

        return matches / len(intents)

    def _semantic_score(self, user_input: str, samples: list[str]) -> float:
        """Calculate semantic similarity score"""
        if not samples:
            return 0.0

        # TODO: Implement with sentence-transformers
        # For now, simple keyword overlap
        input_words = set(user_input.lower().split())

        max_score = 0.0
        for sample in samples:
            sample_words = set(sample.lower().split())
            overlap = len(input_words & sample_words)
            total = len(input_words | sample_words)

            if total > 0:
                score = overlap / total
                max_score = max(max_score, score)

        return max_score

class NoAgentFoundError(Exception):
    """Raised when no suitable agent found"""
    pass
```

### AgentChain Implementation

```python
# src/kagura/routing/chain.py
from typing import Callable, Optional, Any
from dataclasses import dataclass

@dataclass
class ChainStep:
    """Single step in agent chain"""
    agent: Callable
    name: str
    description: str
    condition: Optional[Callable]

class AgentChain:
    """Chain multiple agents for sequential execution"""

    def __init__(self, name: str):
        self.name = name
        self.steps: list[ChainStep] = []

    def add(
        self,
        agent: Callable,
        description: str = "",
        condition: Optional[Callable] = None
    ) -> "AgentChain":
        """Add agent to chain"""
        step = ChainStep(
            agent=agent,
            name=agent.__name__,
            description=description,
            condition=condition
        )
        self.steps.append(step)
        return self

    async def run(self, initial_input: Any, **kwargs) -> Any:
        """Execute entire chain"""
        current_output = initial_input

        for step in self.steps:
            # Check condition
            if step.condition and not step.condition(current_output):
                continue

            # Execute agent
            current_output = await step.agent(current_output, **kwargs)

        return current_output

    async def run_from(self, agent_name: str, input_data: Any) -> Any:
        """Execute chain from specific agent"""
        start_index = next(
            (i for i, s in enumerate(self.steps) if s.name == agent_name),
            None
        )

        if start_index is None:
            raise ValueError(f"Agent '{agent_name}' not found in chain")

        current_output = input_data

        for step in self.steps[start_index:]:
            current_output = await step.agent(current_output)

        return current_output
```

## テスト戦略

```python
# tests/routing/test_router.py
import pytest
from kagura import agent, AgentRouter

@agent(model="gpt-4o-mini")
async def code_reviewer(code: str) -> str:
    """Review code"""
    return f"Reviewed: {code}"

@agent(model="gpt-4o-mini")
async def translator(text: str) -> str:
    """Translate text"""
    return f"Translated: {text}"

@pytest.mark.asyncio
async def test_intent_routing():
    router = AgentRouter(strategy="intent")

    router.register(
        code_reviewer,
        intents=["review", "check", "analyze"]
    )
    router.register(
        translator,
        intents=["translate", "翻訳"]
    )

    # Test routing
    result = await router.route("Please review this code")
    assert "Reviewed" in result

    result = await router.route("Translate this text")
    assert "Translated" in result

@pytest.mark.asyncio
async def test_fallback():
    @agent(model="gpt-4o-mini")
    async def fallback(input: str) -> str:
        return f"Fallback: {input}"

    router = AgentRouter(fallback_agent=fallback)

    # No registered agents, should use fallback
    result = await router.route("Unknown request")
    assert "Fallback" in result

@pytest.mark.asyncio
async def test_chain():
    from kagura import AgentChain

    @agent
    async def step1(x: int) -> int:
        return x + 1

    @agent
    async def step2(x: int) -> int:
        return x * 2

    chain = AgentChain("test")
    chain.add(step1).add(step2)

    result = await chain.run(5)
    assert result == 12  # (5 + 1) * 2
```

## セキュリティ考慮事項

1. **エージェント実行権限**
   - ルーティングされたエージェントの実行権限チェック
   - allowed_tools検証（RFC-012統合）

2. **インジェクション防止**
   - ユーザー入力のサニタイゼーション
   - 悪意あるルーティングパターンのブロック

3. **レート制限**
   - ルーティングリクエストのレート制限
   - Fallbackエージェントの過剰実行防止

## パフォーマンス最適化

1. **キャッシング**
   - Embeddingのキャッシュ
   - ルーティング結果のキャッシュ

2. **並列処理**
   - 複数エージェントスコアリングの並列化
   - Semantic matchingの最適化

3. **インデックス**
   - FAISS等のベクトルインデックス活用
   - 大規模エージェント登録時の高速検索

## マイグレーション

既存のKaguraユーザーへの影響なし。新機能として追加：

```bash
# ルーティング機能のインストール
pip install kagura-ai[routing]

# 使用例
from kagura import AgentRouter
router = AgentRouter()
# ...
```

## ドキュメント

### 必要なドキュメント
1. Agent Routing Quick Start
2. Routing Strategies Comparison
3. Chain Building Tutorial
4. Best Practices for Agent Registration
5. Troubleshooting Guide

## RFC-009 との統合

RFC-009 (Multi-Agent Orchestration) との統合ポイント：

### Team内ルーティング

```python
from kagura import Team, AgentRouter

team = Team("support-team")

# チーム内エージェント
@agent
async def billing_agent(query: str) -> str:
    """Handle billing: {{ query }}"""
    pass

@agent
async def technical_agent(query: str) -> str:
    """Handle technical: {{ query }}"""
    pass

team.add_agent(billing_agent, name="billing")
team.add_agent(technical_agent, name="technical")

# チーム内ルーター
team_router = AgentRouter()
team_router.register(billing_agent, intents=["payment", "invoice", "billing"])
team_router.register(technical_agent, intents=["error", "bug", "technical"])

# Team workflowでルーティング
@team.workflow
async def support_workflow(customer_query: str):
    # 自動的に適切なエージェントにルーティング
    return await team_router.route(customer_query)
```

### Dynamic Team Formation

```python
# ルーティング結果に基づいてチーム構成を動的変更
router = AgentRouter()

async def handle_request(request: str):
    matched_agents = router.get_matched_agents(request, top_k=3)

    # マッチした上位エージェントでチーム構成
    dynamic_team = Team("dynamic")
    for agent, score in matched_agents:
        if score > 0.5:
            dynamic_team.add_agent(agent)

    # チームで並列実行
    results = await dynamic_team.parallel([
        agent(request) for agent, _ in matched_agents
    ])

    return results
```

## 参考資料

- [LangChain Routing](https://python.langchain.com/docs/expression_language/how_to/routing)
- [Semantic Router](https://github.com/aurelio-labs/semantic-router)
- [AutoGen Group Chat](https://microsoft.github.io/autogen/docs/Use-Cases/agent_chat)

## 改訂履歴

- 2025-10-06: 初版作成
