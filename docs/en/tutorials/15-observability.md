# Tutorial 15: Observability & Monitoring

Learn how to monitor agent execution telemetry, track performance, analyze costs, and debug issues using Kagura's observability tools.

## Prerequisites

- Python 3.11 or higher
- Kagura AI installed (`pip install kagura-ai`)
- Completion of [Tutorial 1: Basic Agent](01-basic-agent.md)
- Rich library (included with Kagura)

## Goal

By the end of this tutorial, you will:
- Understand agent telemetry and observability
- Use the monitor CLI for live tracking
- Analyze execution history and traces
- Track performance metrics and costs
- Build custom monitoring dashboards

## What is Observability?

Observability means understanding what your agents are doing:
- **When** did they run?
- **How long** did they take?
- **What** did they call (LLM, tools)?
- **How much** did they cost?
- **Did** they succeed or fail?

Kagura automatically tracks telemetry for all agent executions.

## Step 1: Enable Telemetry

Telemetry is enabled by default. All agent executions are automatically recorded to:

```
~/.kagura/telemetry.db
```

No configuration needed!

## Step 2: Live Monitoring

The simplest way to monitor agents is the `kagura monitor` command:

```bash
# Start live monitoring
kagura monitor
```

**Output:**
```
📊 Kagura Agent Monitor
Total: 42 | Completed: 40 | Failed: 2

┌─ Recent Activity ─────────────────────────────────────┐
│ Time     Agent         Status      Duration  Cost     │
│ 14:32:15 translator    ✓ COMPLETED 0.52s    $0.0003  │
│ 14:31:58 chatbot       ✓ COMPLETED 1.23s    $0.0012  │
│ 14:30:41 researcher    ✗ FAILED    2.11s    $0.0008  │
└───────────────────────────────────────────────────────┘
```

### Monitor Specific Agent

```bash
# Monitor only "translator" agent
kagura monitor --agent translator
```

### Custom Refresh Rate

```bash
# Update every 2 seconds
kagura monitor --refresh 2.0
```

## Step 3: Execution History

View past executions:

```bash
# List recent executions
kagura monitor list

# Filter by agent
kagura monitor list --agent my_agent

# Filter by status (completed/failed)
kagura monitor list --status failed

# Limit results
kagura monitor list --limit 50
```

**Output:**
```
┌─ Execution History ───────────────────────────────────┐
│ Time     Agent         Status      Duration  Cost     │
│ 14:32:15 translator    ✓ COMPLETED 0.52s    $0.0003  │
│ 14:31:58 chatbot       ✓ COMPLETED 1.23s    $0.0012  │
│ 14:30:41 researcher    ✗ FAILED    2.11s    $0.0008  │
└───────────────────────────────────────────────────────┘
```

## Step 4: Statistics

Get aggregate statistics:

```bash
# Overall statistics
kagura monitor stats

# Agent-specific stats
kagura monitor stats --agent translator
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

## Step 5: Detailed Traces

View detailed execution traces:

```bash
# Get execution ID from list
kagura monitor list

# View detailed trace
kagura monitor trace exec_abc123
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

## Step 6: Cost Analysis

Track costs across agents:

```bash
# Cost by agent
kagura monitor cost

# Cost by date
kagura monitor cost --group-by date
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

## Step 7: Programmatic Access

Use EventStore and Dashboard in your Python code:

```python
from pathlib import Path
from kagura.observability import EventStore, Dashboard

# Load event store
store = EventStore(Path.home() / ".kagura" / "telemetry.db")

# Get recent executions
executions = store.get_executions(agent_name="translator", limit=10)

for exec in executions:
    print(f"{exec['agent_name']}: {exec['status']} - {exec['duration']:.2f}s")

# Get statistics
stats = store.get_summary_stats(agent_name="translator")
print(f"Total: {stats['total_executions']}")
print(f"Avg Duration: {stats['avg_duration']:.2f}s")
```

## Step 8: Custom Dashboard

Create a custom monitoring dashboard:

```python
from kagura.observability import EventStore, Dashboard

# Initialize
store = EventStore()
dashboard = Dashboard(store)

# Show live dashboard (refreshes every 1 second)
dashboard.show_live(agent_name="my_agent", refresh_rate=1.0)

# Show execution list
dashboard.show_list(agent_name="my_agent", limit=20)

# Show statistics
dashboard.show_stats(agent_name="my_agent")

# Show specific trace
dashboard.show_trace(execution_id="exec_abc123")

# Show cost summary
dashboard.show_cost_summary(group_by="agent")
```

## Step 9: Filtering and Querying

Filter executions programmatically:

```python
import time
from kagura.observability import EventStore

store = EventStore()

# Get executions from last 24 hours
since = time.time() - 86400  # 24 hours ago
recent = store.get_executions(since=since)

# Get failed executions only
failed = store.get_executions(status="failed")

# Get specific agent's executions
agent_execs = store.get_executions(agent_name="translator", limit=50)

# Get single execution
execution = store.get_execution("exec_abc123")
if execution:
    print(f"Duration: {execution['duration']:.2f}s")
    print(f"Status: {execution['status']}")
    print(f"Error: {execution.get('error')}")
```

## Step 10: Cleanup Old Data

Manage telemetry database size:

```python
import time
from kagura.observability import EventStore

store = EventStore()

# Delete executions older than 30 days
thirty_days_ago = time.time() - (30 * 86400)
deleted = store.delete_old_executions(older_than=thirty_days_ago)
print(f"Deleted {deleted} old executions")

# Clear all data (use with caution!)
# store.clear_all()
```

## Complete Example: Monitoring Integration

```python
import asyncio
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

    # Analyze telemetry
    store = EventStore()
    dashboard = Dashboard(store)

    print("\n" + "=" * 50)
    print("TELEMETRY ANALYSIS")
    print("=" * 50 + "\n")

    # Show statistics
    dashboard.show_stats(agent_name="translator")

    # Show execution list
    dashboard.show_list(agent_name="translator", limit=10)


if __name__ == "__main__":
    asyncio.run(main())
```

## Use Cases

### Use Case 1: Performance Monitoring

Track agent performance over time:

```python
store = EventStore()

# Get last 100 executions
executions = store.get_executions(limit=100)

# Calculate average duration per agent
from collections import defaultdict

agent_durations = defaultdict(list)
for exec in executions:
    agent_durations[exec['agent_name']].append(exec['duration'])

for agent, durations in agent_durations.items():
    avg = sum(durations) / len(durations)
    print(f"{agent}: {avg:.2f}s average")
```

### Use Case 2: Cost Budget Alerts

Monitor costs and alert when budget exceeded:

```python
store = EventStore()

# Get today's executions
import time
today_start = time.time() - 86400
executions = store.get_executions(since=today_start)

# Calculate total cost
total_cost = sum(
    exec.get('metrics', {}).get('total_cost', 0.0)
    for exec in executions
)

# Alert if over budget
DAILY_BUDGET = 1.0  # $1.00
if total_cost > DAILY_BUDGET:
    print(f"⚠️  ALERT: Daily cost ${total_cost:.2f} exceeds budget ${DAILY_BUDGET:.2f}")
else:
    print(f"✓ Cost ${total_cost:.2f} within budget ${DAILY_BUDGET:.2f}")
```

### Use Case 3: Error Tracking

Track and analyze failures:

```python
store = EventStore()

# Get all failed executions
failed = store.get_executions(status="failed", limit=100)

# Group by error type
from collections import Counter

error_types = Counter(
    exec.get('error', 'Unknown error')
    for exec in failed
)

print("Top 5 Error Types:")
for error, count in error_types.most_common(5):
    print(f"  {count}x: {error}")
```

### Use Case 4: Custom Metrics Dashboard

Build a real-time metrics dashboard:

```python
import time
from rich.console import Console
from rich.table import Table
from kagura.observability import EventStore

def show_realtime_metrics():
    """Display real-time metrics dashboard."""
    store = EventStore()
    console = Console()

    while True:
        # Get recent executions
        recent = store.get_executions(limit=50)

        # Calculate metrics
        total = len(recent)
        completed = sum(1 for e in recent if e['status'] == 'completed')
        failed = total - completed
        avg_duration = sum(e['duration'] for e in recent) / total if total > 0 else 0

        # Create table
        table = Table(title="Real-Time Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Total Executions", str(total))
        table.add_row("Completed", str(completed))
        table.add_row("Failed", str(failed))
        table.add_row("Avg Duration", f"{avg_duration:.2f}s")

        # Display
        console.clear()
        console.print(table)

        time.sleep(2)  # Refresh every 2 seconds

# show_realtime_metrics()
```

## Best Practices

### 1. Regular Monitoring

Check your agents regularly:

```bash
# Daily health check
kagura monitor stats

# Weekly cost review
kagura monitor cost
```

### 2. Set Up Alerts

Create scripts to alert on issues:

```bash
#!/bin/bash
# daily_check.sh

# Check for failed executions
failed_count=$(kagura monitor stats | grep "Failed:" | awk '{print $3}')

if [ "$failed_count" -gt 10 ]; then
  echo "⚠️  Alert: $failed_count failed executions"
  # Send notification (email, Slack, etc.)
fi
```

### 3. Cost Tracking

Track costs by project:

```python
# Tag agents by project
@agent(model="gpt-4o-mini")
async def project_a_agent(query: str) -> str:
    '''...'''
    pass

# Query costs by agent name prefix
project_a_execs = store.get_executions(agent_name="project_a_")
```

### 4. Performance Baselines

Establish performance baselines:

```python
# Record baseline
baseline_duration = 2.0  # seconds

# Check if performance degraded
recent = store.get_executions(agent_name="my_agent", limit=10)
avg_recent = sum(e['duration'] for e in recent) / len(recent)

if avg_recent > baseline_duration * 1.5:
    print(f"⚠️  Performance degraded: {avg_recent:.2f}s (baseline: {baseline_duration:.2f}s)")
```

## Common Monitoring Patterns

### Pattern 1: Health Check

```python
def health_check(agent_name: str) -> dict:
    """Check agent health."""
    store = EventStore()
    recent = store.get_executions(agent_name=agent_name, limit=20)

    if not recent:
        return {"status": "unknown", "reason": "no executions"}

    failed = sum(1 for e in recent if e['status'] == 'failed')
    failure_rate = failed / len(recent)

    if failure_rate > 0.5:
        return {"status": "unhealthy", "failure_rate": failure_rate}
    elif failure_rate > 0.2:
        return {"status": "degraded", "failure_rate": failure_rate}
    else:
        return {"status": "healthy", "failure_rate": failure_rate}
```

### Pattern 2: Performance Regression Detection

```python
def detect_regression(agent_name: str, threshold: float = 1.5) -> bool:
    """Detect performance regression."""
    store = EventStore()

    # Get baseline (last 100 executions)
    baseline = store.get_executions(agent_name=agent_name, limit=100)
    baseline_avg = sum(e['duration'] for e in baseline) / len(baseline)

    # Get recent (last 10 executions)
    recent = store.get_executions(agent_name=agent_name, limit=10)
    recent_avg = sum(e['duration'] for e in recent) / len(recent)

    # Check if recent is significantly slower
    return recent_avg > baseline_avg * threshold
```

### Pattern 3: Cost Tracking

```python
def get_cost_breakdown(since: float) -> dict:
    """Get cost breakdown by agent."""
    store = EventStore()
    executions = store.get_executions(since=since, limit=10000)

    breakdown = {}
    for exec in executions:
        agent = exec['agent_name']
        cost = exec.get('metrics', {}).get('total_cost', 0.0)

        if agent not in breakdown:
            breakdown[agent] = {"cost": 0.0, "calls": 0}

        breakdown[agent]["cost"] += cost
        breakdown[agent]["calls"] += 1

    return breakdown
```

## Troubleshooting

### Issue: No telemetry data

**Solution:** Check database location:
```bash
ls ~/.kagura/telemetry.db
```

If missing, run an agent to initialize it.

### Issue: Old data filling disk

**Solution:** Regularly clean old data:
```python
import time
from kagura.observability import EventStore

store = EventStore()
thirty_days_ago = time.time() - (30 * 86400)
store.delete_old_executions(older_than=thirty_days_ago)
```

### Issue: Slow queries

**Solution:** Use indexes and filters:
```python
# Efficient - uses indexes
store.get_executions(agent_name="my_agent", limit=100)

# Less efficient - scans all data
all_execs = store.get_executions(limit=100000)
```

## Key Concepts Learned

### 1. Automatic Telemetry

All executions are tracked automatically:
```python
# Just use agents - telemetry is automatic
result = await my_agent("query")
```

### 2. CLI Monitoring

Quick monitoring via CLI:
```bash
kagura monitor        # Live view
kagura monitor list   # History
kagura monitor stats  # Statistics
kagura monitor trace  # Detailed trace
```

### 3. Programmatic Access

Build custom monitoring:
```python
store = EventStore()
executions = store.get_executions(...)
```

### 4. Cost Tracking

Monitor spending:
```bash
kagura monitor cost
```

## Next Steps

- [API Reference: Observability](../api/observability.md) - Complete observability API
- [Tutorial 13: Agent Builder](13-agent-builder.md) - Build advanced agents
- [Tutorial 14: Testing](14-testing.md) - Test your agents

## Summary

You learned:
- ✓ How to monitor agents with CLI commands
- ✓ How to access telemetry programmatically
- ✓ How to track performance and costs
- ✓ How to build custom dashboards
- ✓ Best practices for observability

You now have the tools to monitor, debug, and optimize your AI agents!
