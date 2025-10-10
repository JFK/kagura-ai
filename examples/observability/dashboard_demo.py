"""Dashboard Demo Example

This example demonstrates Kagura's Rich TUI dashboard for visualizing
agent telemetry, execution traces, and performance metrics.
"""

import asyncio
import time
from kagura import agent
from kagura.observability import EventStore, Dashboard


# Define demo agents
@agent(model="gpt-4o-mini")
async def quick_task(task: str) -> str:
    """Complete quickly: {{ task }}"""
    pass


@agent(model="gpt-4o")
async def detailed_task(task: str) -> str:
    """Detailed analysis: {{ task }}"""
    pass


@agent(model="gpt-4o-mini", enable_memory=True)
async def conversational_task(message: str) -> str:
    """Chat: {{ message }}"""
    pass


async def generate_demo_data():
    """Generate sample telemetry data for dashboard demo."""
    print("Generating demo data...")

    tasks = [
        # Quick tasks
        ("quick_task", "Translate hello to French"),
        ("quick_task", "What is 2+2?"),
        ("quick_task", "Summarize Python"),

        # Detailed tasks
        ("detailed_task", "Explain quantum computing"),
        ("detailed_task", "Analyze market trends"),

        # Conversational
        ("conversational_task", "Hi there!"),
        ("conversational_task", "Tell me about AI"),
        ("conversational_task", "What about machine learning?"),
    ]

    for agent_type, task_input in tasks:
        if agent_type == "quick_task":
            await quick_task(task_input)
        elif agent_type == "detailed_task":
            await detailed_task(task_input)
        elif agent_type == "conversational_task":
            await conversational_task(task_input)

        await asyncio.sleep(0.5)  # Small delay between tasks

    print("✓ Demo data generated\n")


async def main():
    """Demonstrate dashboard features."""
    print("=== Dashboard Demo ===\n")

    # Generate sample data
    await generate_demo_data()

    # Initialize dashboard
    store = EventStore()
    dashboard = Dashboard(store)

    # Example 1: Execution List
    print("1. Execution List View")
    print("-" * 60)
    print("Shows recent executions with status, duration, and cost\n")

    dashboard.show_list(limit=10)

    input("\nPress Enter to continue...")

    # Example 2: Filtered Execution List
    print("\n2. Filtered Execution List (Quick Tasks Only)")
    print("-" * 60)

    dashboard.show_list(agent_name="quick_task", limit=5)

    input("\nPress Enter to continue...")

    # Example 3: Summary Statistics
    print("\n3. Summary Statistics")
    print("-" * 60)
    print("Overall performance metrics and aggregated data\n")

    dashboard.show_stats()

    input("\nPress Enter to continue...")

    # Example 4: Agent-Specific Statistics
    print("\n4. Agent-Specific Statistics")
    print("-" * 60)

    for agent_name in ["quick_task", "detailed_task", "conversational_task"]:
        print(f"\n{agent_name.upper()}:")
        dashboard.show_stats(agent_name=agent_name)

    input("\nPress Enter to continue...")

    # Example 5: Cost Summary
    print("\n5. Cost Summary")
    print("-" * 60)
    print("Cost breakdown by agent with projections\n")

    dashboard.show_cost_summary()

    input("\nPress Enter to continue...")

    # Example 6: Cost by Date
    print("\n6. Cost by Date")
    print("-" * 60)

    dashboard.show_cost_summary(group_by="date")

    input("\nPress Enter to continue...")

    # Example 7: Detailed Execution Trace
    print("\n7. Detailed Execution Trace")
    print("-" * 60)
    print("Deep dive into a specific execution\n")

    # Get a recent execution
    executions = store.get_executions(limit=1)
    if executions:
        execution_id = executions[0]['id']
        print(f"Showing trace for execution: {execution_id}\n")
        dashboard.show_trace(execution_id)
    else:
        print("No executions found")

    input("\nPress Enter to continue...")

    # Example 8: Failed Executions (if any)
    print("\n8. Failed Executions")
    print("-" * 60)

    failed_executions = store.get_executions(status="failed", limit=10)
    if failed_executions:
        print(f"Found {len(failed_executions)} failed executions:\n")
        dashboard.show_list(status="failed", limit=5)
    else:
        print("✓ No failed executions found (great!)\n")

    input("\nPress Enter to continue...")

    # Example 9: Time-Based Analysis
    print("\n9. Time-Based Analysis")
    print("-" * 60)

    # Last hour stats
    one_hour_ago = time.time() - 3600
    print("Statistics for last hour:\n")
    dashboard.show_stats(since=one_hour_ago)

    input("\nPress Enter to continue...")

    # Example 10: Live Monitoring Demo
    print("\n10. Live Monitoring (Demo)")
    print("-" * 60)
    print("""
The live monitoring dashboard auto-refreshes and shows:
- Real-time execution status
- Live performance metrics
- Cost tracking
- Recent activity timeline

To run live monitoring, use:
    kagura monitor

Or for specific agent:
    kagura monitor --agent quick_task

Or with custom refresh rate:
    kagura monitor --refresh 2.0
    """)

    # Simulate a few live updates
    print("\nSimulating live updates (5 iterations)...\n")

    for i in range(5):
        print(f"Update {i+1}/5:")
        dashboard.show_list(limit=3)
        print()

        # Run a new task to show live update
        await quick_task(f"Live update task {i}")

        if i < 4:
            await asyncio.sleep(2)

    print("✓ Live monitoring demo complete\n")


async def cli_commands_demo():
    """Demonstrate CLI commands for dashboard access."""
    print("\n" + "=" * 60)
    print("=== Dashboard CLI Commands ===\n")

    commands = [
        ("kagura monitor", "Live monitoring dashboard (auto-refresh)"),
        ("kagura monitor list", "List recent executions"),
        ("kagura monitor stats", "Show summary statistics"),
        ("kagura monitor cost", "Show cost summary"),
        ("kagura monitor trace <execution_id>", "Show detailed execution trace"),
        ("", ""),
        ("kagura monitor --agent translator", "Monitor specific agent"),
        ("kagura monitor list --limit 50", "Show more executions"),
        ("kagura monitor list --status failed", "Show only failed"),
        ("kagura monitor cost --group-by date", "Cost breakdown by date"),
        ("kagura monitor --refresh 2.0", "Custom refresh rate (seconds)"),
    ]

    for cmd, description in commands:
        if cmd:
            print(f"  {cmd}")
            if description:
                print(f"    → {description}")
        print()


async def dashboard_features_summary():
    """Summarize dashboard features."""
    print("\n" + "=" * 60)
    print("=== Dashboard Features Summary ===\n")

    features = {
        "Execution List": [
            "Recent executions with timestamps",
            "Status indicators (✓ completed, ✗ failed)",
            "Duration and cost per execution",
            "Filter by agent name, status, time",
        ],
        "Summary Statistics": [
            "Total/completed/failed execution counts",
            "Average duration",
            "Success rate percentage",
            "Total cost and token usage",
        ],
        "Cost Analysis": [
            "Cost breakdown by agent or date",
            "Average cost per call",
            "Monthly cost projections",
            "Token usage statistics",
        ],
        "Execution Trace": [
            "Detailed execution timeline",
            "Event sequence visualization",
            "Metrics breakdown",
            "Error details (if failed)",
        ],
        "Live Monitoring": [
            "Auto-refreshing dashboard",
            "Real-time activity feed",
            "Configurable refresh rate",
            "Filter by agent name",
        ],
    }

    for feature, capabilities in features.items():
        print(f"📊 {feature}")
        for capability in capabilities:
            print(f"   • {capability}")
        print()


async def integration_examples():
    """Show integration with other tools."""
    print("\n" + "=" * 60)
    print("=== Integration Examples ===\n")

    print("1. CI/CD Integration:")
    print("""
    # In your CI pipeline
    - name: Check Agent Performance
      run: |
        kagura monitor stats
        # Parse output to check success rate
    """)

    print("2. Alerting Integration:")
    print("""
    # Python script for alerts
    from kagura.observability import EventStore

    store = EventStore()
    stats = store.get_summary_stats()

    failure_rate = stats['failed'] / stats['total_executions']
    if failure_rate > 0.1:  # 10% threshold
        send_alert(f"High failure rate: {failure_rate:.1%}")
    """)

    print("3. Grafana/Prometheus Integration:")
    print("""
    # Export metrics to Prometheus format
    from kagura.observability import EventStore

    store = EventStore()
    executions = store.get_executions(limit=1000)

    # Convert to Prometheus metrics
    # ... (custom exporter implementation)
    """)

    print("4. Logging Integration:")
    print("""
    # Log execution events
    import logging
    from kagura.observability import EventStore

    store = EventStore()
    for execution in store.get_executions(status="failed"):
        logging.error(f"Agent {execution['agent_name']} failed: {execution.get('error')}")
    """)


if __name__ == "__main__":
    # Run main demo
    asyncio.run(main())

    # Show CLI commands
    asyncio.run(cli_commands_demo())

    # Show features summary
    asyncio.run(dashboard_features_summary())

    # Show integration examples
    asyncio.run(integration_examples())

    print("\n" + "=" * 60)
    print("Dashboard demo complete! 🎉")
    print("\nTry running: kagura monitor")
    print("=" * 60)
