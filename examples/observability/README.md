# Observability Examples

This directory contains examples demonstrating Kagura's observability features for monitoring, cost tracking, and performance analysis of AI agents.

## Overview

Kagura provides comprehensive observability tools:
- **Automatic Telemetry**: All agent executions are automatically tracked
- **EventStore**: SQLite-based storage for execution data
- **Dashboard**: Rich TUI for visualization
- **CLI Commands**: Quick access to monitoring features
- **Cost Tracking**: Token usage and cost analysis

## Examples

### 1. Monitored Agent (`monitored_agent.py`)

Demonstrates basic monitoring and telemetry collection:
- Automatic telemetry collection
- Querying execution history
- Filtering by agent name, status, time
- Summary statistics
- Execution traces
- Data management

**Run:**
```bash
python examples/observability/monitored_agent.py
```

**Key Concepts:**
```python
from kagura.observability import EventStore

store = EventStore()

# Get recent executions
executions = store.get_executions(limit=10)

# Filter by agent
translator_execs = store.get_executions(agent_name="translator")

# Get statistics
stats = store.get_summary_stats()
print(f"Success rate: {stats['completed']/stats['total_executions']:.1%}")
```

---

### 2. Cost Tracking (`cost_tracking.py`)

Shows how to track and optimize costs:
- Cost analysis by agent
- Token usage tracking
- Cost trends over time
- Monthly cost projections
- Cost optimization recommendations
- ROI calculations

**Run:**
```bash
python examples/observability/cost_tracking.py
```

**Key Patterns:**
```python
# Calculate total cost
executions = store.get_executions(agent_name="translator")
total_cost = sum(
    exec.get('metrics', {}).get('total_cost', 0)
    for exec in executions
)

# Cost per call
avg_cost = total_cost / len(executions)

# Monthly projection
daily_cost = get_daily_cost()
estimated_monthly = daily_cost * 30
```

---

### 3. Dashboard Demo (`dashboard_demo.py`)

Interactive demonstration of the Rich TUI dashboard:
- Execution list views
- Summary statistics
- Cost summaries
- Detailed execution traces
- Live monitoring simulation
- CLI commands

**Run:**
```bash
python examples/observability/dashboard_demo.py
```

**Dashboard Views:**
```python
from kagura.observability import Dashboard

dashboard = Dashboard(store)

# Show execution list
dashboard.show_list(limit=20)

# Show statistics
dashboard.show_stats(agent_name="translator")

# Show cost summary
dashboard.show_cost_summary()

# Show detailed trace
dashboard.show_trace(execution_id)
```

---

## CLI Commands

Kagura provides CLI commands for quick access to monitoring features:

### Live Monitoring

```bash
# Monitor all agents (auto-refresh)
kagura monitor

# Monitor specific agent
kagura monitor --agent translator

# Custom refresh rate
kagura monitor --refresh 2.0
```

### Execution List

```bash
# List recent executions
kagura monitor list

# Filter by agent
kagura monitor list --agent translator

# Filter by status
kagura monitor list --status failed

# Show more results
kagura monitor list --limit 50
```

### Statistics

```bash
# Overall statistics
kagura monitor stats

# Agent-specific stats
kagura monitor stats --agent translator

# Stats for time period
kagura monitor stats --since 2025-01-01
```

### Cost Analysis

```bash
# Cost summary by agent
kagura monitor cost

# Cost by date
kagura monitor cost --group-by date

# Cost for time period
kagura monitor cost --since 2025-01-01
```

### Execution Trace

```bash
# Detailed trace for specific execution
kagura monitor trace <execution_id>
```

---

## EventStore API

### Querying Executions

```python
from kagura.observability import EventStore

store = EventStore()

# Get all recent executions
all_execs = store.get_executions(limit=100)

# Filter by agent name
translator_execs = store.get_executions(agent_name="translator")

# Filter by status
failed = store.get_executions(status="failed")
completed = store.get_executions(status="completed")

# Filter by time
import time
one_hour_ago = time.time() - 3600
recent = store.get_executions(since=one_hour_ago)

# Combine filters
recent_failed = store.get_executions(
    agent_name="translator",
    status="failed",
    since=one_hour_ago,
    limit=50
)
```

### Getting Statistics

```python
# Overall stats
stats = store.get_summary_stats()
print(f"Total: {stats['total_executions']}")
print(f"Completed: {stats['completed']}")
print(f"Failed: {stats['failed']}")
print(f"Avg duration: {stats['avg_duration']:.2f}s")

# Agent-specific stats
translator_stats = store.get_summary_stats(agent_name="translator")

# Time-filtered stats
recent_stats = store.get_summary_stats(since=one_hour_ago)
```

### Execution Details

```python
# Get specific execution
execution = store.get_execution(execution_id)

print(f"Agent: {execution['agent_name']}")
print(f"Status: {execution['status']}")
print(f"Duration: {execution['duration']:.2f}s")

# Access metrics
metrics = execution.get('metrics', {})
print(f"Tokens: {metrics.get('total_tokens')}")
print(f"Cost: ${metrics.get('total_cost', 0):.4f}")

# Access events
events = execution.get('events', [])
for event in events:
    print(f"Event: {event['type']} at {event['timestamp']}")
```

### Data Management

```python
import time

# Delete old executions
thirty_days_ago = time.time() - (30 * 86400)
deleted = store.delete_old_executions(older_than=thirty_days_ago)
print(f"Deleted {deleted} old records")

# Clear all data (use with caution!)
store.clear_all()
```

---

## Dashboard API

### Showing Views

```python
from kagura.observability import Dashboard

dashboard = Dashboard(store)

# Execution list
dashboard.show_list(
    agent_name="translator",  # Optional filter
    limit=20,                 # Number of results
    status="completed"        # Optional filter
)

# Statistics
dashboard.show_stats(
    agent_name="translator",  # Optional filter
    since=one_hour_ago        # Optional time filter
)

# Cost summary
dashboard.show_cost_summary(
    since=one_hour_ago,       # Optional time filter
    group_by="agent"          # "agent" or "date"
)

# Execution trace
dashboard.show_trace(execution_id)
```

### Live Monitoring

```python
# Live monitoring (auto-refresh)
dashboard.show_live(
    agent_name="translator",  # Optional filter
    refresh_rate=1.0          # Refresh interval in seconds
)
```

---

## Cost Tracking Patterns

### Pattern 1: Cost per Agent

```python
def get_agent_cost(agent_name: str) -> float:
    """Calculate total cost for an agent."""
    executions = store.get_executions(agent_name=agent_name, limit=10000)
    return sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in executions
    )

translator_cost = get_agent_cost("translator")
print(f"Translator cost: ${translator_cost:.4f}")
```

### Pattern 2: Cost Alerts

```python
def check_cost_threshold(threshold: float = 1.0) -> None:
    """Alert if daily cost exceeds threshold."""
    one_day_ago = time.time() - 86400
    executions = store.get_executions(since=one_day_ago, limit=10000)

    daily_cost = sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in executions
    )

    if daily_cost > threshold:
        print(f"⚠️  Daily cost ${daily_cost:.2f} exceeds threshold ${threshold:.2f}")
        # Send alert (email, Slack, etc.)
```

### Pattern 3: Monthly Projections

```python
def estimate_monthly_cost() -> float:
    """Estimate monthly cost based on recent usage."""
    one_day_ago = time.time() - 86400
    executions = store.get_executions(since=one_day_ago, limit=10000)

    daily_cost = sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in executions
    )

    return daily_cost * 30

estimated = estimate_monthly_cost()
print(f"Estimated monthly cost: ${estimated:.2f}")
```

### Pattern 4: ROI Calculation

```python
def calculate_roi(manual_cost_per_task: float) -> dict:
    """Calculate ROI of agent automation."""
    executions = store.get_executions(limit=10000)

    total_calls = len(executions)
    total_agent_cost = sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in executions
    )

    total_manual_cost = total_calls * manual_cost_per_task
    savings = total_manual_cost - total_agent_cost
    roi_percentage = (savings / total_agent_cost * 100) if total_agent_cost > 0 else 0

    return {
        "total_calls": total_calls,
        "agent_cost": total_agent_cost,
        "manual_cost": total_manual_cost,
        "savings": savings,
        "roi_percentage": roi_percentage
    }
```

---

## Performance Monitoring

### Latency Tracking

```python
# Get average latency by agent
stats = store.get_summary_stats(agent_name="translator")
print(f"Avg latency: {stats['avg_duration']:.2f}s")

# Detect performance regression
def check_performance_regression(agent_name: str, threshold: float = 1.5) -> bool:
    """Check if agent has slowed down."""
    # Baseline (last 100 executions)
    baseline = store.get_executions(agent_name=agent_name, limit=100)
    baseline_avg = sum(e['duration'] for e in baseline) / len(baseline)

    # Recent (last 10 executions)
    recent = store.get_executions(agent_name=agent_name, limit=10)
    recent_avg = sum(e['duration'] for e in recent) / len(recent)

    return recent_avg > baseline_avg * threshold
```

### Failure Rate Monitoring

```python
def check_failure_rate(agent_name: str, threshold: float = 0.1) -> None:
    """Alert if failure rate exceeds threshold."""
    stats = store.get_summary_stats(agent_name=agent_name)

    if stats['total_executions'] == 0:
        return

    failure_rate = stats['failed'] / stats['total_executions']

    if failure_rate > threshold:
        print(f"⚠️  {agent_name} failure rate: {failure_rate:.1%}")
```

---

## Integration Examples

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Check Agent Performance
  run: |
    kagura monitor stats
    # Parse output and fail if metrics are poor
```

### Alerting Integration

```python
# alert_script.py
from kagura.observability import EventStore

store = EventStore()
stats = store.get_summary_stats()

if stats['failed'] / stats['total_executions'] > 0.1:
    send_slack_alert("High agent failure rate!")
```

### Prometheus/Grafana Export

```python
# prometheus_exporter.py
from kagura.observability import EventStore

store = EventStore()
stats = store.get_summary_stats()

# Export to Prometheus format
print(f"agent_executions_total {stats['total_executions']}")
print(f"agent_failures_total {stats['failed']}")
print(f"agent_duration_avg {stats['avg_duration']}")
```

---

## Best Practices

### 1. Regular Monitoring
```bash
# Daily health check
kagura monitor stats

# Weekly cost review
kagura monitor cost
```

### 2. Set Up Alerts
```python
# Check daily
check_cost_threshold(threshold=10.0)
check_failure_rate(agent_name="critical_agent", threshold=0.05)
```

### 3. Regular Cleanup
```python
# Monthly cleanup
thirty_days_ago = time.time() - (30 * 86400)
store.delete_old_executions(older_than=thirty_days_ago)
```

### 4. Performance Baselines
```python
# Establish and track baselines
baseline_latency = get_avg_latency("translator")
# Alert if latency increases by 50%
```

---

## API Reference

For complete API documentation, see:
- [Observability API Reference](../../docs/en/api/observability.md)

## Related Examples

- [AgentBuilder Examples](../agent_builder/) - Creating monitored agents
- [Testing Examples](../testing/) - Testing with performance metrics

---

**Note:** Telemetry data is stored in `~/.kagura/telemetry.db` by default. You can customize the location using the `EventStore` constructor.
