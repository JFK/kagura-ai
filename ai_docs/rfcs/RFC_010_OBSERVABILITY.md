# RFC-010: Observability & Monitoring - エージェント可視化システム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: TBD
- **優先度**: Medium

## 概要

Kaguraエージェントの動作を可視化・監視するObservabilityシステムを実装します。コスト追跡、パフォーマンス測定、デバッグトレース、ダッシュボードにより、エージェントの運用を最適化します。

### 目標
- LLM APIコスト追跡（トークン数、料金）
- パフォーマンスメトリクス（レイテンシ、スループット）
- デバッグトレース（実行ログ、エラー）
- リアルタイムダッシュボード
- アラート・通知機能

### 非目標
- 分散トレーシング（単一マシン内に注力）
- カスタムメトリクスストレージ（既存ツール統合優先）

## モチベーション

### 現在の課題
1. エージェント実行のブラックボックス化
2. LLM APIコストが不透明
3. パフォーマンスボトルネックの特定困難
4. デバッグが難しい

### 解決するユースケース
- **コスト管理**: LLM API使用量・料金をリアルタイム追跡
- **パフォーマンス最適化**: 遅いエージェントを特定・改善
- **デバッグ**: エラーの原因を迅速に特定
- **運用監視**: 本番環境でのエージェント健全性チェック

### なぜ今実装すべきか
- 本番運用が増えると可視性が必須
- コスト管理の需要増加
- OpenTelemetry等の標準ツールが利用可能

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Kagura Agents                       │
│                                             │
│  @agent(model="gpt-4o")                     │
│  @observe(track_cost=True)                  │
│  async def my_agent(...):                   │
│      ...                                    │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Instrumentation Layer               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Metrics Collector                  │   │
│  │  - Token count                      │   │
│  │  - Latency                          │   │
│  │  - Success/error rate               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Trace Collector                    │   │
│  │  - Execution trace                  │   │
│  │  - Prompt/response logging          │   │
│  │  - Error stack trace                │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Cost Calculator                    │   │
│  │  - Model pricing                    │   │
│  │  - Token × price                    │   │
│  │  - Aggregation                      │   │
│  └─────────────────────────────────────┘   │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Storage & Export                    │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ SQLite   │  │Prometheus│  │  JSON    │  │
│  │  (local) │  │(metrics) │  │  (logs)  │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Visualization                       │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Web Dashboard                      │   │
│  │  - Cost breakdown                   │   │
│  │  - Performance charts               │   │
│  │  - Error logs                       │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  CLI Tools                          │   │
│  │  - kagura stats                     │   │
│  │  - kagura cost                      │   │
│  │  - kagura trace                     │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Observability Decorator

エージェントに可視性を追加：

```python
from kagura import agent, observe

@agent(model="gpt-4o")
@observe(
    track_cost=True,
    track_latency=True,
    log_prompts=True,
    log_responses=True
)
async def my_agent(query: str) -> str:
    """{{ query }}"""
    pass

# 自動的に以下を記録:
# - 実行時間
# - トークン数（入力/出力）
# - コスト
# - プロンプト・レスポンス
# - エラー（あれば）
```

#### 2. Cost Tracking

リアルタイムコスト追跡：

```python
from kagura.observability import CostTracker

tracker = CostTracker()

# エージェント実行
result = await my_agent(query="What is AI?")

# コスト確認
cost = tracker.get_cost(agent_name="my_agent")
print(f"Total cost: ${cost.total:.4f}")
print(f"  Input tokens: {cost.input_tokens} (${cost.input_cost:.4f})")
print(f"  Output tokens: {cost.output_tokens} (${cost.output_cost:.4f})")

# 期間別コスト
daily_cost = tracker.get_cost_by_period("today")
monthly_cost = tracker.get_cost_by_period("this_month")
```

#### 3. Performance Metrics

パフォーマンス測定：

```python
from kagura.observability import metrics

# メトリクス自動収集
@agent(model="gpt-4o-mini")
@observe
async def search_agent(query: str) -> list[str]:
    """Search for {{ query }}"""
    pass

# メトリクス確認
stats = metrics.get_stats("search_agent")
print(f"Average latency: {stats.avg_latency_ms}ms")
print(f"P95 latency: {stats.p95_latency_ms}ms")
print(f"Success rate: {stats.success_rate * 100}%")
print(f"Total calls: {stats.total_calls}")
```

#### 4. Debug Tracing

詳細なトレース情報：

```python
from kagura.observability import Tracer

tracer = Tracer()

@agent(model="gpt-4o")
@tracer.trace
async def complex_agent(input: str) -> str:
    """Process {{ input }}"""
    # サブタスク
    with tracer.span("fetch_data"):
        data = fetch_data(input)

    with tracer.span("process_data"):
        processed = process(data)

    with tracer.span("generate_output"):
        output = generate(processed)

    return output

# トレース確認
trace = tracer.get_trace("complex_agent", trace_id="...")
for span in trace.spans:
    print(f"{span.name}: {span.duration_ms}ms")
```

#### 5. Dashboard

Webダッシュボード：

```bash
# ダッシュボード起動
kagura dashboard

# ブラウザで http://localhost:8080 にアクセス

# 表示内容:
# - リアルタイムコストグラフ
# - エージェント別実行回数
# - レイテンシ分布
# - エラーログ
# - トークン使用量
```

### 統合例

#### 例1: コスト追跡

```python
from kagura import agent, observe
from kagura.observability import CostTracker

tracker = CostTracker()

@agent(model="gpt-4o")
@observe(track_cost=True)
async def expensive_agent(task: str) -> str:
    """{{ task }}"""
    pass

# 月次コスト上限設定
tracker.set_budget("monthly", limit_usd=100.0)

# エージェント実行
for i in range(100):
    try:
        result = await expensive_agent(task=f"Task {i}")
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e}")
        break

# コストレポート
report = tracker.generate_report("this_month")
print(report)

# 出力:
# Monthly Cost Report (2025-10)
# ================================
# Total: $85.42
#
# By Agent:
#   expensive_agent: $85.42 (100%)
#
# By Model:
#   gpt-4o: $85.42 (100%)
#
# By Day:
#   2025-10-04: $85.42
#
# Budget: $100.00
# Remaining: $14.58
```

#### 例2: パフォーマンス監視

```python
from kagura import agent, observe
from kagura.observability import metrics, alerts

@agent(model="gpt-4o-mini")
@observe(track_latency=True)
async def api_agent(endpoint: str) -> dict:
    """Call API: {{ endpoint }}"""
    pass

# アラート設定
alerts.add_rule(
    metric="latency_p95",
    agent="api_agent",
    threshold_ms=1000,
    action="notify",
    notification="slack"
)

# エージェント実行
for endpoint in endpoints:
    result = await api_agent(endpoint=endpoint)

# パフォーマンスレポート
stats = metrics.get_stats("api_agent")
if stats.p95_latency_ms > 1000:
    print("⚠️ High latency detected!")
    print(f"P95: {stats.p95_latency_ms}ms")

    # 詳細分析
    slow_calls = metrics.get_slow_calls("api_agent", threshold_ms=1000)
    for call in slow_calls:
        print(f"  {call.timestamp}: {call.latency_ms}ms - {call.args}")
```

#### 例3: デバッグトレース

```python
from kagura import agent, observe
from kagura.observability import Tracer

tracer = Tracer()

@agent(model="gpt-4o")
@tracer.trace(log_prompts=True, log_responses=True)
async def debug_agent(input: str) -> str:
    """Process {{ input }}"""
    with tracer.span("step1"):
        step1_result = await sub_task1(input)

    with tracer.span("step2"):
        step2_result = await sub_task2(step1_result)

    return step2_result

# エージェント実行
result = await debug_agent(input="test")

# トレース確認
trace = tracer.get_last_trace("debug_agent")
print(f"Total duration: {trace.duration_ms}ms")

for span in trace.spans:
    print(f"  {span.name}: {span.duration_ms}ms")

# プロンプト確認
print(f"\nPrompt:\n{trace.prompt}")
print(f"\nResponse:\n{trace.response}")

# エラーがあれば
if trace.error:
    print(f"\nError: {trace.error}")
    print(f"Stack trace:\n{trace.stack_trace}")
```

#### 例4: CLI統計表示

```bash
# エージェント統計
$ kagura stats

Agent Statistics
================
my_agent:
  Total calls: 1,234
  Success rate: 98.5%
  Avg latency: 245ms
  P95 latency: 520ms
  Total cost: $12.45

expensive_agent:
  Total calls: 56
  Success rate: 100%
  Avg latency: 1,200ms
  P95 latency: 2,100ms
  Total cost: $85.42

# コスト詳細
$ kagura cost --period this_month

Cost Report (2025-10)
=====================
Total: $97.87

By Agent:
  expensive_agent: $85.42 (87.3%)
  my_agent:        $12.45 (12.7%)

By Model:
  gpt-4o:      $85.42 (87.3%)
  gpt-4o-mini: $12.45 (12.7%)

Budget: $100.00
Remaining: $2.13 ⚠️

# トレース表示
$ kagura trace my_agent --last

Trace: my_agent (2025-10-04 10:30:15)
=====================================
Duration: 245ms
Status: Success
Cost: $0.0012

Timeline:
  0ms    → Start
  15ms   → LLM call start
  230ms  → LLM call end
  245ms  → End

Prompt (120 tokens):
  What is AI?

Response (85 tokens):
  AI stands for Artificial Intelligence...
```

## 実装計画

### Phase 1: Core Metrics (v2.3.0)
- [ ] `@observe` デコレータ実装
- [ ] コスト追跡（トークン × 価格）
- [ ] レイテンシ測定
- [ ] SQLiteストレージ

### Phase 2: Advanced Tracking (v2.4.0)
- [ ] トレース機能
- [ ] プロンプト/レスポンスロギング
- [ ] エラー追跡
- [ ] アラートシステム

### Phase 3: Visualization (v2.5.0)
- [ ] Webダッシュボード
- [ ] CLIツール（stats, cost, trace）
- [ ] グラフ・チャート
- [ ] エクスポート機能

### Phase 4: Integrations (v2.6.0)
- [ ] Prometheus統合
- [ ] Grafana連携
- [ ] OpenTelemetry対応
- [ ] Slack通知

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
observability = [
    "prometheus-client>=0.19.0",  # Metrics export
    "opentelemetry-api>=1.21.0",  # Tracing
    "sqlalchemy>=2.0.0",          # Storage
    "fastapi>=0.104.0",           # Dashboard backend
    "plotly>=5.17.0",             # Charts
]
```

### Cost Calculation

```python
# src/kagura/observability/cost.py

MODEL_PRICING = {
    "gpt-4o": {
        "input": 0.005 / 1000,   # $0.005 per 1K tokens
        "output": 0.015 / 1000,  # $0.015 per 1K tokens
    },
    "gpt-4o-mini": {
        "input": 0.00015 / 1000,
        "output": 0.0006 / 1000,
    },
    # ... other models
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate LLM API cost"""
    pricing = MODEL_PRICING.get(model, {"input": 0, "output": 0})

    input_cost = input_tokens * pricing["input"]
    output_cost = output_tokens * pricing["output"]

    return input_cost + output_cost
```

### Metrics Storage Schema

```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    status TEXT NOT NULL,  -- success, error
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    prompt TEXT,
    response TEXT,
    error TEXT
);

CREATE INDEX idx_agent_timestamp ON metrics(agent_name, timestamp);
CREATE INDEX idx_timestamp ON metrics(timestamp);
```

## テスト戦略

```python
# tests/observability/test_cost_tracker.py
import pytest
from kagura.observability import CostTracker

def test_cost_calculation():
    tracker = CostTracker()

    cost = tracker.calculate_cost(
        model="gpt-4o",
        input_tokens=100,
        output_tokens=50
    )

    expected = (100 * 0.005 / 1000) + (50 * 0.015 / 1000)
    assert abs(cost - expected) < 0.0001
```

## 参考資料

- [OpenTelemetry](https://opentelemetry.io/)
- [Prometheus](https://prometheus.io/)
- [LangSmith](https://www.langchain.com/langsmith)

## 改訂履歴

- 2025-10-04: 初版作成
