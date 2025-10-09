# RFC-009: Multi-Agent Orchestration - 複数エージェント協調システム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #69
- **優先度**: Medium-High

## 概要

複数のKaguraエージェントを協調動作させるオーケストレーションシステムを実装します。エージェント間通信、タスク分散、並列実行により、複雑なワークフローを効率的に実行します。

### 目標
- 複数エージェントの協調動作（チーム）
- エージェント間通信プロトコル
- タスク分散と並列実行
- ステートフル・ワークフロー管理
- エージェントの役割分担（ロールベース）

### 非目標
- 完全自律型マルチエージェントシステム（将来的に検討）
- 分散システム（単一マシン内での協調に注力）

## モチベーション

### 現在の課題
1. 1つのエージェントで全てを処理すると複雑化
2. タスクの並列実行ができない
3. エージェント間の連携が手動

### 解決するユースケース
- **複雑なワークフロー**: データ収集→分析→レポート生成を複数エージェントで分担
- **並列処理**: 複数のデータソースを同時処理
- **専門化**: 各エージェントが特定の役割に特化
- **スケーラビリティ**: タスクを複数エージェントに分散

### なぜ今実装すべきか
- Kagura v2.0の基盤が安定
- RFC-001のワークフロー機能との統合
- AutoGen、CrewAI等の先行事例から学べる

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Orchestrator                        │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Team Manager                       │   │
│  │  - Agent lifecycle                  │   │
│  │  - Role assignment                  │   │
│  │  - Communication routing            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Task Scheduler                     │   │
│  │  - Task queue                       │   │
│  │  - Dependency resolution            │   │
│  │  - Parallel execution               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  State Manager                      │   │
│  │  - Shared state                     │   │
│  │  - Message bus                      │   │
│  │  - Event system                     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Agent A    │ │  Agent B    │ │  Agent C    │
│  (Collector)│ │  (Analyzer) │ │  (Reporter) │
└─────────────┘ └─────────────┘ └─────────────┘
```

### コンポーネント設計

#### 1. Agent Team

複数のエージェントをチームとして管理：

```python
from kagura import agent, Team

# エージェント定義
@agent(model="gpt-4o-mini", role="collector")
async def data_collector(source: str) -> dict:
    """Collect data from {{ source }}"""
    pass

@agent(model="gpt-4o", role="analyzer")
async def data_analyzer(data: dict) -> dict:
    """Analyze data: {{ data }}"""
    pass

@agent(model="gpt-4o-mini", role="reporter")
async def report_generator(analysis: dict) -> str:
    """Generate report from {{ analysis }}"""
    pass

# チーム作成
team = Team("data-pipeline")
team.add_agent(data_collector, name="collector")
team.add_agent(data_analyzer, name="analyzer")
team.add_agent(report_generator, name="reporter")

# ワークフロー定義
@team.workflow
async def run_pipeline(sources: list[str]) -> str:
    """Run complete data pipeline"""

    # 並列データ収集
    data_list = await team.parallel(
        [team.collector(source=s) for s in sources]
    )

    # データ統合
    combined_data = merge_data(data_list)

    # 分析
    analysis = await team.analyzer(data=combined_data)

    # レポート生成
    report = await team.reporter(analysis=analysis)

    return report

# 実行
result = await team.run_pipeline(["source1", "source2", "source3"])
```

#### 2. Agent Communication

エージェント間通信：

```python
from kagura import agent, Team

team = Team("research-team")

@agent(model="gpt-4o-mini", role="researcher")
async def researcher(topic: str, team_context) -> str:
    """Research {{ topic }}"""
    # 他のエージェントに質問
    clarification = await team_context.ask(
        "validator",
        f"Is this topic valid: {topic}?"
    )

    if "yes" in clarification.lower():
        result = f"Research result for {topic}"

        # 結果をブロードキャスト
        await team_context.broadcast({
            "type": "research_complete",
            "topic": topic,
            "result": result
        })

        return result
    else:
        return "Topic rejected"

@agent(model="gpt-4o-mini", role="validator")
async def validator(question: str) -> str:
    """Validate: {{ question }}"""
    pass

team.add_agent(researcher, name="researcher")
team.add_agent(validator, name="validator")

# イベントハンドラー
@team.on("research_complete")
async def on_research_complete(event):
    print(f"Research completed: {event['topic']}")
```

#### 3. Parallel Execution

並列タスク実行：

```python
from kagura import agent, parallel, sequential

@agent(model="gpt-4o-mini")
async def process_item(item: str) -> dict:
    """Process {{ item }}"""
    pass

# 並列実行
items = ["item1", "item2", "item3", "item4", "item5"]
results = await parallel([
    process_item(item=item) for item in items
])

# 逐次実行（依存関係あり）
result = await sequential([
    fetch_data(source="api"),
    lambda data: transform_data(data=data),
    lambda transformed: save_data(data=transformed)
])
```

#### 4. Stateful Workflow

状態を持つワークフロー：

```python
from kagura import agent, StatefulWorkflow
from pydantic import BaseModel

class PipelineState(BaseModel):
    raw_data: dict = {}
    processed_data: dict = {}
    analysis: dict = {}
    report: str = ""

workflow = StatefulWorkflow(PipelineState)

@workflow.step("collect")
async def collect_step(state: PipelineState, sources: list[str]) -> PipelineState:
    """Collect data from sources"""
    data = await fetch_data(sources)
    state.raw_data = data
    return state

@workflow.step("process")
async def process_step(state: PipelineState) -> PipelineState:
    """Process collected data"""
    state.processed_data = process(state.raw_data)
    return state

@workflow.step("analyze")
async def analyze_step(state: PipelineState) -> PipelineState:
    """Analyze processed data"""
    state.analysis = analyze(state.processed_data)
    return state

@workflow.step("report")
async def report_step(state: PipelineState) -> PipelineState:
    """Generate final report"""
    state.report = generate_report(state.analysis)
    return state

# ワークフロー実行
final_state = await workflow.run(
    steps=["collect", "process", "analyze", "report"],
    sources=["source1", "source2"]
)

print(final_state.report)
```

### 統合例

#### 例1: データ処理パイプライン

```python
from kagura import agent, Team

team = Team("data-pipeline")

@agent(model="gpt-4o-mini", role="collector")
async def collect_data(source: str) -> dict:
    """Collect data from {{ source }}"""
    pass

@agent(model="gpt-4o", role="cleaner")
async def clean_data(data: dict) -> dict:
    """Clean and validate: {{ data }}"""
    pass

@agent(model="gpt-4o", role="analyzer")
async def analyze_data(data: dict) -> dict:
    """Analyze: {{ data }}"""
    pass

@agent(model="gpt-4o-mini", role="reporter")
async def generate_report(analysis: dict) -> str:
    """Generate report from: {{ analysis }}"""
    pass

team.add_agent(collect_data, name="collector")
team.add_agent(clean_data, name="cleaner")
team.add_agent(analyze_data, name="analyzer")
team.add_agent(generate_report, name="reporter")

@team.workflow
async def pipeline(sources: list[str]) -> str:
    # 並列収集
    raw_data = await team.parallel([
        team.collector(source=s) for s in sources
    ])

    # 並列クリーニング
    clean_data_list = await team.parallel([
        team.cleaner(data=d) for d in raw_data
    ])

    # 統合して分析
    combined = merge(clean_data_list)
    analysis = await team.analyzer(data=combined)

    # レポート生成
    report = await team.reporter(analysis=analysis)

    return report

# 実行
result = await pipeline(["api1", "api2", "db1"])
```

#### 例2: コードレビューチーム

```python
from kagura import agent, Team

team = Team("code-review")

@agent(model="gpt-4o", role="security-reviewer")
async def security_review(code: str) -> dict:
    """Review security issues in: {{ code }}"""
    pass

@agent(model="gpt-4o", role="performance-reviewer")
async def performance_review(code: str) -> dict:
    """Review performance issues in: {{ code }}"""
    pass

@agent(model="gpt-4o-mini", role="style-reviewer")
async def style_review(code: str) -> dict:
    """Review code style in: {{ code }}"""
    pass

@agent(model="gpt-4o", role="coordinator")
async def coordinate_reviews(reviews: list[dict]) -> str:
    """Summarize reviews: {{ reviews }}"""
    pass

team.add_agent(security_review, name="security")
team.add_agent(performance_review, name="performance")
team.add_agent(style_review, name="style")
team.add_agent(coordinate_reviews, name="coordinator")

@team.workflow
async def review_code(code: str) -> str:
    # 並列レビュー
    reviews = await team.parallel([
        team.security(code=code),
        team.performance(code=code),
        team.style(code=code)
    ])

    # 総合評価
    summary = await team.coordinator(reviews=reviews)

    return summary
```

#### 例3: 研究アシスタントチーム

```python
from kagura import agent, Team

team = Team("research-assistants")

@agent(model="gpt-4o-mini", role="searcher")
async def search_papers(query: str) -> list[dict]:
    """Search academic papers for: {{ query }}"""
    pass

@agent(model="gpt-4o", role="reader")
async def read_paper(paper: dict) -> dict:
    """Read and extract key points from: {{ paper }}"""
    pass

@agent(model="gpt-4o", role="synthesizer")
async def synthesize(summaries: list[dict]) -> str:
    """Synthesize findings from: {{ summaries }}"""
    pass

team.add_agent(search_papers, name="searcher")
team.add_agent(read_paper, name="reader")
team.add_agent(synthesize, name="synthesizer")

@team.workflow
async def research(topic: str) -> str:
    # 論文検索
    papers = await team.searcher(query=topic)

    # 並列読解（最大5本）
    summaries = await team.parallel([
        team.reader(paper=p) for p in papers[:5]
    ])

    # 統合
    synthesis = await team.synthesizer(summaries=summaries)

    return synthesis
```

## 実装計画

### Phase 1: Core Orchestration (v2.3.0)
- [ ] Team API実装
- [ ] エージェント登録・管理
- [ ] 基本的なワークフロー実行
- [ ] 並列実行（parallel）

### Phase 2: Communication (v2.4.0)
- [ ] エージェント間通信プロトコル
- [ ] メッセージバス実装
- [ ] イベントシステム
- [ ] ask/broadcast API

### Phase 3: Stateful Workflows (v2.5.0)
- [ ] StatefulWorkflow実装
- [ ] Pydantic state management
- [ ] ステップ定義・実行
- [ ] エラーハンドリング・リトライ

### Phase 4: Advanced Features (v2.6.0)
- [ ] ダイナミックエージェント生成
- [ ] タスクスケジューリング最適化
- [ ] 負荷分散
- [ ] モニタリング・可視化

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
orchestration = [
    "asyncio>=3.11",           # Async support
    "networkx>=3.1",           # Workflow DAG
    "redis>=5.0.0",            # Optional: Message bus
]
```

### Team Implementation

```python
# src/kagura/orchestration/team.py
from typing import Callable, Any
import asyncio

class Team:
    """Manage multiple agents as a team"""

    def __init__(self, name: str):
        self.name = name
        self._agents: dict[str, Callable] = {}
        self._message_bus = MessageBus()

    def add_agent(self, agent: Callable, name: str):
        """Add agent to team"""
        self._agents[name] = agent

        # Inject team context
        agent._team_context = TeamContext(self, name)

    async def parallel(self, tasks: list[Callable]) -> list[Any]:
        """Execute tasks in parallel"""
        return await asyncio.gather(*tasks)

    async def sequential(self, tasks: list[Callable]) -> Any:
        """Execute tasks sequentially"""
        result = None
        for task in tasks:
            if callable(task):
                result = await task(result) if result else await task()
        return result

    def workflow(self, func: Callable) -> Callable:
        """Decorator for team workflows"""
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
```

## テスト戦略

```python
# tests/orchestration/test_team.py
import pytest
from kagura import agent, Team

@pytest.mark.asyncio
async def test_parallel_execution():
    team = Team("test-team")

    @agent
    async def task(x: int) -> int:
        return x * 2

    team.add_agent(task, name="task")

    results = await team.parallel([
        team.task(x=1),
        team.task(x=2),
        team.task(x=3)
    ])

    assert results == [2, 4, 6]
```

## 参考資料

- [AutoGen](https://microsoft.github.io/autogen/)
- [CrewAI](https://www.crewai.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)

## RFC-016統合: Agent Routing

RFC-016 (Agent Routing System) と統合することで、チーム内でのエージェント選択を自動化できます。

### Team内自動ルーティング

```python
from kagura import Team, AgentRouter

team = Team("support-team")

# チーム内エージェント
@agent(model="gpt-4o-mini", role="billing")
async def billing_agent(query: str) -> str:
    """Handle billing: {{ query }}"""
    pass

@agent(model="gpt-4o-mini", role="technical")
async def technical_agent(query: str) -> str:
    """Handle technical: {{ query }}"""
    pass

team.add_agent(billing_agent, name="billing")
team.add_agent(technical_agent, name="technical")

# チーム内ルーター設定
team_router = AgentRouter()
team_router.register(billing_agent, intents=["payment", "invoice", "billing"])
team_router.register(technical_agent, intents=["error", "bug", "technical"])

# Teamワークフローで自動ルーティング
@team.workflow
async def support_workflow(customer_query: str):
    # ユーザー入力に基づいて自動的に適切なエージェントを選択
    return await team_router.route(customer_query)

# 使用例
result = await support_workflow("請求書が届かない")
# → billing_agent が自動選択される

result = await support_workflow("アプリがクラッシュする")
# → technical_agent が自動選択される
```

### 動的チーム構成

ルーティング結果に基づいてチーム構成を動的に変更：

```python
from kagura import Team, AgentRouter

router = AgentRouter()

# 複数の専門エージェント登録
router.register(data_collector, intents=["collect", "fetch", "gather"])
router.register(data_analyzer, intents=["analyze", "examine", "investigate"])
router.register(visualizer, intents=["visualize", "chart", "graph"])
router.register(reporter, intents=["report", "summarize", "document"])

async def handle_complex_request(request: str):
    # マッチした上位3つのエージェントを取得
    matched_agents = router.get_matched_agents(request, top_k=3)

    # マッチしたエージェントで動的チーム構成
    dynamic_team = Team("dynamic")

    for agent, confidence in matched_agents:
        if confidence > 0.5:
            dynamic_team.add_agent(agent)

    # チームで並列実行
    results = await dynamic_team.parallel([
        agent(request) for agent, _ in matched_agents
    ])

    return results

# 使用例
results = await handle_complex_request("データを収集して分析しグラフ化")
# → data_collector, data_analyzer, visualizer が自動選択・並列実行
```

### Semantic Routing統合

意味ベースルーティングでより柔軟なエージェント選択：

```python
from kagura import Team, SemanticRouter

team = Team("research-team")

# セマンティックルーター（埋め込みベクトルベース）
semantic_router = SemanticRouter(threshold=0.7)

semantic_router.register(
    paper_searcher,
    samples=[
        "Find research papers about AI",
        "論文を検索して",
        "Search academic articles"
    ]
)

semantic_router.register(
    paper_summarizer,
    samples=[
        "Summarize this paper",
        "論文を要約して",
        "Give me the key points"
    ]
)

@team.workflow
async def research_workflow(query: str):
    # 意味的に類似したエージェントを自動選択
    return await semantic_router.route(query)

# 使用例
result = await research_workflow("機械学習の最新論文を探したい")
# → paper_searcher が選択される（"Find research papers"と意味的に類似）
```

詳細は [RFC-016: Agent Routing System](./RFC_016_AGENT_ROUTING.md) を参照。

## 改訂履歴

- 2025-10-04: 初版作成
- 2025-10-06: RFC-016統合セクション追加
