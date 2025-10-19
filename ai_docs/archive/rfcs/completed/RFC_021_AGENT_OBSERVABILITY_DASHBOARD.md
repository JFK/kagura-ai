# RFC-021: Agent Observability Dashboard - エージェント可観測性ダッシュボード

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-10
- **関連Issue**: #109
- **優先度**: Medium-High

## 概要

Agentの動作をリアルタイムで可視化・監視するための Observability Dashboard を提供します。

### 目標
- エージェント動作のリアルタイム可視化
- パフォーマンスメトリクスの収集
- デバッグとトラブルシューティングの簡易化
- コスト管理の支援

### 非目標
- 分散トレーシング（初期フェーズでは）
- プロダクション監視システムの置き換え

## モチベーション

### 現在の課題

```python
# 現状：エージェント内部で何が起こっているか不明
@agent
async def my_agent(query: str) -> str:
    '''Process {{ query }}'''
    pass

result = await my_agent("Hello")
# ❓ LLMが何回呼ばれた？
# ❓ どのツールが使われた？
# ❓ コストはいくら？
# ❓ どこで時間がかかっている？
```

**問題**:
1. エージェント動作のブラックボックス化
2. パフォーマンス問題の特定が困難
3. コスト管理ができない
4. デバッグに時間がかかる

### 解決するユースケース

**ケース1: パフォーマンス問題の特定**
```bash
kagura monitor --agent my_agent

[my_agent] Execution Timeline:
├─ LLM Call (gpt-4o) .......... 2.3s  [$0.0023]
├─ Tool: search_tool .......... 1.5s
├─ LLM Call (gpt-4o) .......... 2.1s  [$0.0021]
└─ Total ...................... 5.9s  [$0.0044]

⚠️ LLM calls taking 75% of time
💡 Consider caching or using faster model
```

**ケース2: コスト追跡**
```bash
kagura monitor --cost

Daily Cost Summary (2025-10-10):
├─ my_agent ................... $2.45 (145 calls)
├─ translation_agent .......... $0.89 (67 calls)
└─ code_review_agent .......... $1.23 (34 calls)

Total: $4.57
Projected monthly: ~$137
```

**ケース3: デバッグ**
```bash
kagura monitor --agent my_agent --trace

[17:45:23] my_agent started
[17:45:23]   ├─ Memory lookup: 3 messages retrieved
[17:45:24]   ├─ LLM call: gpt-4o (512 tokens)
[17:45:26]   │  └─ Response: "I need to search for..."
[17:45:26]   ├─ Tool: search_tool(query="...")
[17:45:28]   │  └─ Result: [10 results]
[17:45:28]   ├─ LLM call: gpt-4o (1024 tokens)
[17:45:30]   │  └─ Response: "Based on the search..."
[17:45:30]   └─ Completed (7.2s, $0.0044)
```

### なぜ今実装すべきか
- v2.1.0で機能が複雑化
- パフォーマンス最適化の必要性
- コスト意識の重要性
- エンタープライズ利用への準備

## 設計

### アーキテクチャ

```
┌──────────────────────────────────────┐
│         Agent Execution              │
│    (with instrumentation)            │
└───────────┬──────────────────────────┘
            │ Events
            ▼
┌──────────────────────────────────────┐
│      Telemetry Collector             │
│  - Intercept agent calls             │
│  - Collect metrics                   │
│  - Store events                      │
└───────────┬──────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│      Event Store                     │
│  - SQLite (local)                    │
│  - In-memory (dev)                   │
└───────────┬──────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│   Observability Dashboard            │
│  - CLI: kagura monitor               │
│  - TUI: Rich-based interface         │
│  - Web: Optional web UI              │
└──────────────────────────────────────┘
```

### CLI Design

#### リアルタイム監視

```bash
# Start monitoring
kagura monitor

┌─ Kagura Agent Monitor ────────────────────────────┐
│ Active Agents: 2                                   │
│ Total Calls: 145                                   │
│ Total Cost: $4.57                                  │
└────────────────────────────────────────────────────┘

┌─ Recent Activity ──────────────────────────────────┐
│ 17:45:30 my_agent       COMPLETED  7.2s   $0.0044 │
│ 17:45:28 translate      COMPLETED  2.1s   $0.0012 │
│ 17:45:25 my_agent       RUNNING    3.5s   -       │
│ 17:45:22 code_review    COMPLETED  4.8s   $0.0031 │
└────────────────────────────────────────────────────┘

┌─ Performance ──────────────────────────────────────┐
│ Avg Response Time: 4.2s                            │
│ P95 Response Time: 8.1s                            │
│ Success Rate: 98.5%                                │
└────────────────────────────────────────────────────┘

Press 'q' to quit, 'r' to refresh, 'd' for details
```

#### 特定エージェントの監視

```bash
kagura monitor --agent my_agent

┌─ my_agent ─────────────────────────────────────────┐
│ Status: RUNNING                                    │
│ Calls Today: 145                                   │
│ Avg Duration: 5.2s                                 │
│ Total Cost: $2.45                                  │
└────────────────────────────────────────────────────┘

┌─ LLM Usage ────────────────────────────────────────┐
│ Model: gpt-4o                                      │
│ Total Calls: 290 (2 per agent call)                │
│ Avg Tokens: 768 prompt, 512 completion            │
│ Cost: $2.45                                        │
└────────────────────────────────────────────────────┘

┌─ Tools Used ───────────────────────────────────────┐
│ search_tool .................. 87 calls (60%)     │
│ calculate_tool ............... 45 calls (31%)     │
│ file_read .................... 13 calls (9%)      │
└────────────────────────────────────────────────────┘

┌─ Slow Requests ────────────────────────────────────┐
│ 17:42:15  12.3s  Complex search query             │
│ 17:38:42  11.8s  Large file processing            │
│ 17:35:11  10.9s  Multiple tool calls              │
└────────────────────────────────────────────────────┘
```

#### トレース詳細

```bash
kagura monitor --trace [execution_id]

Execution Trace: my_agent (exec_abc123)
Started: 2025-10-10 17:45:23
Duration: 7.2s
Cost: $0.0044

Timeline:
 0.0s ┌─ Agent Started
 0.1s │  ├─ Memory Lookup (3 messages)
 1.2s │  ├─ LLM Call #1 [gpt-4o]
      │  │    Prompt: 512 tokens ($0.0010)
      │  │    Completion: 128 tokens ($0.0013)
      │  │    Duration: 2.1s
      │  │    Response: "I need to search..."
 3.3s │  ├─ Tool Call: search_tool
      │  │    Args: {query: "..."}
      │  │    Duration: 1.5s
      │  │    Result: [10 results]
 4.8s │  ├─ LLM Call #2 [gpt-4o]
      │  │    Prompt: 1024 tokens ($0.0020)
      │  │    Completion: 256 tokens ($0.0026)
      │  │    Duration: 2.2s
      │  │    Response: "Based on the search..."
 7.0s │  ├─ Memory Store
 7.2s └─ Agent Completed

Summary:
- LLM Calls: 2 (4.3s, $0.0044)
- Tool Calls: 1 (1.5s)
- Memory Ops: 2 (0.1s)
```

### API設計

#### Instrumentation Decorator

```python
# src/kagura/observability/instrumentation.py
from kagura.observability import telemetry

@agent
@telemetry.instrument()  # Add instrumentation
async def my_agent(query: str) -> str:
    '''Process {{ query }}'''
    pass

# Automatic instrumentation (no decorator needed)
# All @agent decorated functions are auto-instrumented if enabled
```

#### Manual Event Tracking

```python
from kagura.observability import tracker

@agent
async def my_agent(query: str) -> str:
    # Track custom events
    with tracker.span("data_processing"):
        # ... process data ...
        pass

    tracker.record_metric("items_processed", 42)
    tracker.add_tag("category", "research")

    return result
```

#### Querying Telemetry Data

```python
from kagura.observability import telemetry_db

# Get execution history
executions = telemetry_db.get_executions(
    agent_name="my_agent",
    since="2025-10-10",
    status="completed"
)

# Get metrics
metrics = telemetry_db.get_metrics(
    agent_name="my_agent",
    metric_type="duration",
    aggregation="p95"
)

# Get cost summary
cost = telemetry_db.get_cost_summary(
    date="2025-10-10"
)
```

### コンポーネント設計

#### 1. Telemetry Collector

```python
# src/kagura/observability/collector.py
import time
from typing import Any, Optional
from contextlib import asynccontextmanager

class TelemetryCollector:
    """Collect telemetry data from agent executions"""

    def __init__(self, store: "EventStore"):
        self.store = store
        self._current_execution: Optional[dict] = None

    @asynccontextmanager
    async def track_execution(self, agent_name: str, **kwargs):
        """Track agent execution"""
        execution_id = self._generate_id()
        execution = {
            "id": execution_id,
            "agent_name": agent_name,
            "started_at": time.time(),
            "kwargs": kwargs,
            "events": [],
            "metrics": {},
        }

        self._current_execution = execution

        try:
            yield execution_id
        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)
            raise
        else:
            execution["status"] = "completed"
        finally:
            execution["ended_at"] = time.time()
            execution["duration"] = execution["ended_at"] - execution["started_at"]
            await self.store.save_execution(execution)
            self._current_execution = None

    def record_event(self, event_type: str, **data):
        """Record an event in current execution"""
        if not self._current_execution:
            return

        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        self._current_execution["events"].append(event)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration: float,
        cost: float,
    ):
        """Record LLM call"""
        self.record_event(
            "llm_call",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            duration=duration,
            cost=cost,
        )

    def record_tool_call(self, tool_name: str, duration: float, **kwargs):
        """Record tool call"""
        self.record_event(
            "tool_call",
            tool_name=tool_name,
            duration=duration,
            kwargs=kwargs,
        )
```

#### 2. Event Store

```python
# src/kagura/observability/store.py
import sqlite3
from pathlib import Path
from typing import Optional, List
import json

class EventStore:
    """Store telemetry events"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".kagura" / "telemetry.db"

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                agent_name TEXT,
                started_at REAL,
                ended_at REAL,
                duration REAL,
                status TEXT,
                error TEXT,
                kwargs TEXT,
                events TEXT,
                metrics TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_started
            ON executions(agent_name, started_at)
        """)
        conn.commit()
        conn.close()

    async def save_execution(self, execution: dict):
        """Save execution record"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            INSERT INTO executions
            (id, agent_name, started_at, ended_at, duration, status, error, kwargs, events, metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution["id"],
                execution["agent_name"],
                execution["started_at"],
                execution.get("ended_at"),
                execution.get("duration"),
                execution.get("status"),
                execution.get("error"),
                json.dumps(execution.get("kwargs", {})),
                json.dumps(execution.get("events", [])),
                json.dumps(execution.get("metrics", {})),
            ),
        )
        conn.commit()
        conn.close()

    def get_executions(
        self,
        agent_name: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Query execution records"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM executions WHERE 1=1"
        params = []

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if since:
            query += " AND started_at >= ?"
            params.append(since)

        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
```

#### 3. Dashboard CLI

```python
# src/kagura/cli/monitor.py
import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from kagura.observability import telemetry_db

@click.command()
@click.option("--agent", help="Filter by agent name")
@click.option("--trace", help="Show trace for execution ID")
@click.option("--cost", is_flag=True, help="Show cost summary")
def monitor(agent: Optional[str], trace: Optional[str], cost: bool):
    """Monitor agent execution"""
    if trace:
        show_trace(trace)
    elif cost:
        show_cost_summary()
    else:
        show_live_monitor(agent)

def show_live_monitor(agent_name: Optional[str]):
    """Show live monitoring dashboard"""
    console = Console()

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            table = create_monitor_table(agent_name)
            live.update(table)
            time.sleep(1)

def create_monitor_table(agent_name: Optional[str]) -> Table:
    """Create monitoring table"""
    executions = telemetry_db.get_executions(agent_name=agent_name, limit=10)

    table = Table(title="Recent Activity")
    table.add_column("Time")
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Duration")
    table.add_column("Cost")

    for exec in executions:
        table.add_row(
            format_time(exec["started_at"]),
            exec["agent_name"],
            exec["status"],
            f"{exec['duration']:.1f}s",
            f"${exec.get('cost', 0):.4f}",
        )

    return table
```

## 実装計画

### Phase 1: Core Telemetry (v2.2.0) - 1週間
- [ ] TelemetryCollector実装
- [ ] EventStore (SQLite)実装
- [ ] 基本的なメトリクス収集
- [ ] `@telemetry.instrument()`デコレータ

### Phase 2: CLI Dashboard (v2.2.0) - 1週間
- [ ] `kagura monitor`コマンド
- [ ] リアルタイム表示（Rich）
- [ ] トレース詳細表示
- [ ] コストサマリー

### Phase 3: Advanced Features (v2.3.0)
- [ ] Web UI (optional)
- [ ] アラート機能
- [ ] エクスポート機能（CSV, JSON）
- [ ] 分散トレーシング

## 技術的詳細

### 依存関係

```toml
[project.dependencies]
rich = ">=13.0"  # CLI UI (already dependency)

[project.optional-dependencies]
observability = [
    "sqlite3",      # Built-in
]
```

### パフォーマンス考慮

- 非同期ストレージで実行をブロックしない
- バッチ書き込みでI/O削減
- オプトインで有効化

## テスト戦略

```python
@pytest.mark.asyncio
async def test_telemetry_collection():
    collector = TelemetryCollector(EventStore(":memory:"))

    async with collector.track_execution("test_agent") as exec_id:
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.001)

    execution = collector.store.get_execution(exec_id)
    assert execution["status"] == "completed"
    assert len(execution["events"]) == 1
```

## ドキュメント

- Observability クイックスタート
- CLI Reference
- カスタムメトリクス追加方法

## 参考資料

- [OpenTelemetry](https://opentelemetry.io/)
- [Rich Documentation](https://rich.readthedocs.io/)

## 改訂履歴

- 2025-10-10: 初版作成
