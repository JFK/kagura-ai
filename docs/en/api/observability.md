# Observability API

Telemetry tracking and monitoring for agent execution.

## Overview

The `kagura.observability` module provides tools for monitoring agent behavior:
- **EventStore**: SQLite-based telemetry storage
- **Dashboard**: Rich TUI for visualization
- **CLI Commands**: `kagura monitor` commands

Telemetry is automatically tracked for all agent executions.

---

## Class: EventStore

Store and query telemetry events in SQLite database.

```python
from kagura.observability import EventStore

store = EventStore()  # Uses ~/.kagura/telemetry.db
```

### Constructor

```python
def __init__(self, db_path: Optional[Path | str] = None) -> None
```

**Parameters:**
- **db_path** (`Optional[Path | str]`, default: `None`): Database path
  - `None`: Uses `~/.kagura/telemetry.db`
  - `":memory:"`: In-memory database (testing)
  - `Path` or `str`: Custom file path

**Example:**
```python
# Default location
store = EventStore()

# Custom location
store = EventStore(Path.home() / "my_telemetry.db")

# In-memory (testing)
store = EventStore(":memory:")
```

---

### save_execution()

Save execution record.

```python
async def save_execution(self, execution: dict[str, Any]) -> None
```

**Parameters:**
- **execution** (`dict[str, Any]`): Execution data containing:
  - `id` (`str`, required): Execution ID
  - `agent_name` (`str`, required): Agent name
  - `started_at` (`float`, required): Start timestamp
  - `ended_at` (`float`, optional): End timestamp
  - `duration` (`float`, optional): Duration in seconds
  - `status` (`str`, optional): Status (`"completed"`, `"failed"`)
  - `error` (`str`, optional): Error message if failed
  - `kwargs` (`dict`, optional): Agent arguments
  - `events` (`list`, optional): List of events
  - `metrics` (`dict`, optional): Metrics dictionary

**Example:**
```python
import time

await store.save_execution({
    "id": "exec_123",
    "agent_name": "translator",
    "started_at": time.time(),
    "ended_at": time.time() + 0.5,
    "duration": 0.5,
    "status": "completed",
    "metrics": {
        "total_cost": 0.0003,
        "total_tokens": 85,
        "llm_calls": 1
    }
})
```

---

### get_execution()

Get execution by ID.

```python
def get_execution(self, execution_id: str) -> Optional[dict[str, Any]]
```

**Parameters:**
- **execution_id** (`str`): Execution ID

**Returns:** Execution dict or `None` if not found

**Example:**
```python
execution = store.get_execution("exec_123")
if execution:
    print(f"Status: {execution['status']}")
    print(f"Duration: {execution['duration']:.2f}s")
```

---

### get_executions()

Query execution records.

```python
def get_executions(
    self,
    agent_name: Optional[str] = None,
    status: Optional[str] = None,
    since: Optional[float] = None,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Parameters:**
- **agent_name** (`Optional[str]`): Filter by agent name
- **status** (`Optional[str]`): Filter by status (`"completed"`, `"failed"`)
- **since** (`Optional[float]`): Filter by start time (timestamp)
- **limit** (`int`, default: `100`): Maximum number of records

**Returns:** List of execution dictionaries (sorted by most recent first)

**Example:**
```python
import time

# Get all executions
all_execs = store.get_executions(limit=1000)

# Get translator executions
translator_execs = store.get_executions(agent_name="translator")

# Get failed executions
failed = store.get_executions(status="failed")

# Get last 24 hours
since = time.time() - 86400
recent = store.get_executions(since=since)

# Combined filters
recent_failed = store.get_executions(
    agent_name="translator",
    status="failed",
    since=since,
    limit=50
)
```

---

### get_summary_stats()

Get summary statistics.

```python
def get_summary_stats(
    self, agent_name: Optional[str] = None, since: Optional[float] = None
) -> dict[str, Any]
```

**Parameters:**
- **agent_name** (`Optional[str]`): Filter by agent name
- **since** (`Optional[float]`): Filter by start time (timestamp)

**Returns:** Dictionary containing:
- `total_executions` (`int`): Total number of executions
- `completed` (`int`): Number of completed executions
- `failed` (`int`): Number of failed executions
- `avg_duration` (`float`): Average duration in seconds

**Example:**
```python
# Overall stats
stats = store.get_summary_stats()
print(f"Total: {stats['total_executions']}")
print(f"Success rate: {stats['completed'] / stats['total_executions'] * 100:.1f}%")

# Agent-specific stats
translator_stats = store.get_summary_stats(agent_name="translator")
print(f"Avg duration: {translator_stats['avg_duration']:.2f}s")
```

---

### delete_old_executions()

Delete executions older than timestamp.

```python
def delete_old_executions(self, older_than: float) -> int
```

**Parameters:**
- **older_than** (`float`): Timestamp threshold

**Returns:** Number of deleted records

**Example:**
```python
import time

# Delete executions older than 30 days
thirty_days_ago = time.time() - (30 * 86400)
deleted = store.delete_old_executions(older_than=thirty_days_ago)
print(f"Deleted {deleted} old executions")
```

---

### clear_all()

Clear all execution records.

```python
def clear_all(self) -> None
```

**Example:**
```python
# Use with caution!
store.clear_all()
```

---

## Class: Dashboard

Rich TUI dashboard for visualizing telemetry data.

```python
from kagura.observability import Dashboard

dashboard = Dashboard(store)
```

### Constructor

```python
def __init__(self, store: EventStore) -> None
```

**Parameters:**
- **store** (`EventStore`): Event store to query data from

**Example:**
```python
from kagura.observability import EventStore, Dashboard

store = EventStore()
dashboard = Dashboard(store)
```

---

### show_live()

Show live monitoring dashboard (auto-refreshing).

```python
def show_live(
    self, agent_name: Optional[str] = None, refresh_rate: float = 1.0
) -> None
```

**Parameters:**
- **agent_name** (`Optional[str]`): Filter by agent name
- **refresh_rate** (`float`, default: `1.0`): Refresh interval in seconds

**Example:**
```python
# Monitor all agents (refresh every 1 second)
dashboard.show_live()

# Monitor specific agent
dashboard.show_live(agent_name="translator")

# Custom refresh rate
dashboard.show_live(refresh_rate=2.0)
```

**Output:**
```
📊 Kagura Agent Monitor
Total: 42 | Completed: 40 | Failed: 2

┌─ Recent Activity ─────────────────────────────────────┐
│ Time     Agent         Status      Duration  Cost     │
│ 14:32:15 translator    ✓ COMPLETED 0.52s    $0.0003  │
│ 14:31:58 chatbot       ✓ COMPLETED 1.23s    $0.0012  │
└───────────────────────────────────────────────────────┘
```

---

### show_list()

Show execution list.

```python
def show_list(
    self,
    agent_name: Optional[str] = None,
    limit: int = 20,
    status: Optional[str] = None,
) -> None
```

**Parameters:**
- **agent_name** (`Optional[str]`): Filter by agent name
- **limit** (`int`, default: `20`): Maximum number of executions
- **status** (`Optional[str]`): Filter by status

**Example:**
```python
# Show last 20 executions
dashboard.show_list()

# Show translator executions
dashboard.show_list(agent_name="translator", limit=50)

# Show failed executions
dashboard.show_list(status="failed")
```

---

### show_stats()

Show statistics summary.

```python
def show_stats(
    self, agent_name: Optional[str] = None, since: Optional[float] = None
) -> None
```

**Parameters:**
- **agent_name** (`Optional[str]`): Filter by agent name
- **since** (`Optional[float]`): Filter by start time (timestamp)

**Example:**
```python
import time

# Overall statistics
dashboard.show_stats()

# Agent-specific stats
dashboard.show_stats(agent_name="translator")

# Last 24 hours
since = time.time() - 86400
dashboard.show_stats(since=since)
```

**Output:**
```
📊 Summary Statistics

Total Executions: 42
  • Completed: 40
  • Failed: 2
Avg Duration: 1.34s
Total Cost: $0.0512
Total Tokens: 12,450
LLM Calls: 45
Tool Calls: 12

Success Rate: 95.2%
```

---

### show_trace()

Show detailed trace for specific execution.

```python
def show_trace(self, execution_id: str) -> None
```

**Parameters:**
- **execution_id** (`str`): Execution ID

**Example:**
```python
dashboard.show_trace("exec_abc123")
```

**Output:**
```
📍 Execution Trace: translator (exec_abc123)

Execution Info
├── Started: 14:32:15
├── Status: ✓ COMPLETED
├── Duration: 0.52s

Metrics
├── total_cost: $0.0003
├── total_tokens: 85
├── llm_calls: 1
└── tool_calls: 0

Events Timeline (3 events)
├── [0.00s] LLM Call (gpt-4o-mini) - 85 tokens, $0.0003, 0.48s
├── [0.48s] Memory Op (store) - 0.02s
└── [0.50s] Completion
```

---

### show_cost_summary()

Show cost summary.

```python
def show_cost_summary(
    self, since: Optional[float] = None, group_by: str = "agent"
) -> None
```

**Parameters:**
- **since** (`Optional[float]`): Filter by start time (timestamp)
- **group_by** (`str`, default: `"agent"`): Group by `"agent"` or `"date"`

**Example:**
```python
# Cost by agent
dashboard.show_cost_summary(group_by="agent")

# Cost by date
dashboard.show_cost_summary(group_by="date")

# Last 7 days
import time
since = time.time() - (7 * 86400)
dashboard.show_cost_summary(since=since)
```

**Output (by agent):**
```
┌─ Cost by Agent ──────────────────────────┐
│ Agent          Calls  Tokens    Cost     │
│ translator     23     5,123     $0.0234  │
│ chatbot        15     4,892     $0.0189  │
│ researcher     4      2,435     $0.0089  │
│ ────────────────────────────────────────  │
│ Total          42     12,450    $0.0512  │
└──────────────────────────────────────────┘

Estimated monthly cost: $1.54
```

---

## CLI Commands

The `kagura monitor` command provides quick access to observability features.

### Live Monitoring

```bash
# Monitor all agents
kagura monitor

# Monitor specific agent
kagura monitor --agent translator

# Custom refresh rate
kagura monitor --refresh 2.0

# Custom database
kagura monitor --db /path/to/telemetry.db
```

### Execution List

```bash
# List recent executions
kagura monitor list

# Filter by agent
kagura monitor list --agent translator

# Filter by status
kagura monitor list --status failed

# Limit results
kagura monitor list --limit 50
```

### Statistics

```bash
# Overall statistics
kagura monitor stats

# Agent-specific stats
kagura monitor stats --agent translator
```

### Detailed Trace

```bash
# Show trace for specific execution
kagura monitor trace exec_abc123
```

### Cost Analysis

```bash
# Cost by agent
kagura monitor cost

# Cost by date
kagura monitor cost --group-by date
```

---

## Complete Example

```python
import asyncio
import time
from pathlib import Path
from kagura import agent
from kagura.observability import EventStore, Dashboard


@agent(model="gpt-4o-mini")
async def translator(text: str, target_lang: str) -> str:
    '''Translate "{{ text }}" to {{ target_lang }}'''
    pass


async def main():
    # Run agent multiple times
    translations = [
        ("Hello", "French"),
        ("Goodbye", "Japanese"),
        ("Thank you", "Spanish"),
    ]

    for text, lang in translations:
        result = await translator(text, target_lang=lang)
        print(f"{text} → {lang}: {result}")

    # === Analyze Telemetry ===

    # Initialize
    store = EventStore()
    dashboard = Dashboard(store)

    # Get executions
    executions = store.get_executions(agent_name="translator", limit=10)
    print(f"\n{len(executions)} executions found")

    # Show statistics
    stats = store.get_summary_stats(agent_name="translator")
    print(f"Avg duration: {stats['avg_duration']:.2f}s")

    # Show dashboard views
    print("\n" + "=" * 50)
    print("EXECUTION LIST")
    print("=" * 50)
    dashboard.show_list(agent_name="translator")

    print("\n" + "=" * 50)
    print("STATISTICS")
    print("=" * 50)
    dashboard.show_stats(agent_name="translator")

    print("\n" + "=" * 50)
    print("COST SUMMARY")
    print("=" * 50)
    dashboard.show_cost_summary()

    # === Cleanup old data ===
    thirty_days_ago = time.time() - (30 * 86400)
    deleted = store.delete_old_executions(older_than=thirty_days_ago)
    print(f"\nDeleted {deleted} old executions")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Best Practices

### 1. Regular Monitoring

Check your agents regularly:

```bash
# Daily health check
kagura monitor stats

# Weekly cost review
kagura monitor cost
```

### 2. Automated Alerts

Create scripts to alert on issues:

```python
def check_failure_rate(agent_name: str, threshold: float = 0.2) -> None:
    """Alert if failure rate exceeds threshold."""
    store = EventStore()
    stats = store.get_summary_stats(agent_name=agent_name)

    if stats['total_executions'] == 0:
        return

    failure_rate = stats['failed'] / stats['total_executions']

    if failure_rate > threshold:
        print(f"⚠️  ALERT: {agent_name} failure rate: {failure_rate:.1%}")
        # Send notification (email, Slack, etc.)
```

### 3. Cost Tracking

Monitor spending by project:

```python
def get_project_cost(project_prefix: str) -> float:
    """Get total cost for project."""
    store = EventStore()
    executions = store.get_executions(limit=10000)

    total_cost = 0.0
    for exec in executions:
        if exec['agent_name'].startswith(project_prefix):
            total_cost += exec.get('metrics', {}).get('total_cost', 0.0)

    return total_cost

# Example
cost = get_project_cost("project_a_")
print(f"Project A cost: ${cost:.2f}")
```

### 4. Performance Baselines

Track performance trends:

```python
def detect_performance_regression(
    agent_name: str, threshold: float = 1.5
) -> bool:
    """Detect if agent has slowed down."""
    store = EventStore()

    # Baseline (last 100 executions)
    baseline = store.get_executions(agent_name=agent_name, limit=100)
    baseline_avg = sum(e['duration'] for e in baseline) / len(baseline)

    # Recent (last 10 executions)
    recent = store.get_executions(agent_name=agent_name, limit=10)
    recent_avg = sum(e['duration'] for e in recent) / len(recent)

    return recent_avg > baseline_avg * threshold
```

---

## Error Handling

```python
from pathlib import Path
from kagura.observability import EventStore

try:
    # Access database
    store = EventStore()
    executions = store.get_executions()
except Exception as e:
    print(f"Database error: {e}")

try:
    # Get specific execution
    execution = store.get_execution("exec_123")
    if execution is None:
        print("Execution not found")
except Exception as e:
    print(f"Query error: {e}")
```

---

## Related

- [Tutorial: Observability](../tutorials/15-observability.md) - Step-by-step guide
- [@agent Decorator](agent.md) - Core agent decorator
- [Testing API](testing.md) - Agent testing

---

## See Also

- [Quick Start](../quickstart.md) - Getting started
- [Tutorial: Agent Builder](../tutorials/13-agent-builder.md) - Building agents
- [Tutorial: Testing](../tutorials/14-testing.md) - Testing agents
