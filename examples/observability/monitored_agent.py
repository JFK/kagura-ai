"""Monitored Agent Example

This example demonstrates how to monitor agent execution using
Kagura's built-in telemetry and observability features.
"""

import asyncio
import time
from kagura import agent
from kagura.observability import EventStore, Dashboard


# Define monitored agents
@agent(model="gpt-4o-mini")
async def translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}"""
    pass


@agent(model="gpt-4o-mini", enable_memory=True)
async def chatbot(message: str) -> str:
    """Respond to: {{ message }}"""
    pass


@agent(model="gpt-4o-mini")
async def summarizer(text: str) -> str:
    """Summarize: {{ text }}"""
    pass


async def main():
    """Demonstrate agent monitoring and telemetry."""
    print("=== Monitored Agent Example ===\n")

    # Example 1: Run agents and collect telemetry
    print("1. Running Agents (Telemetry Auto-Collected)")
    print("-" * 50)

    # Run translator
    result1 = await translator("Hello", target_lang="French")
    print(f"Translation: {result1}")

    # Run chatbot
    result2 = await chatbot("What is machine learning?")
    print(f"Chatbot: {result2}")

    # Run summarizer
    long_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines,
    in contrast to the natural intelligence displayed by humans and animals.
    Leading AI textbooks define the field as the study of "intelligent agents":
    any device that perceives its environment and takes actions that maximize
    its chance of successfully achieving its goals.
    """
    result3 = await summarizer(long_text)
    print(f"Summary: {result3}\n")

    # Example 2: Query telemetry data
    print("2. Querying Telemetry Data")
    print("-" * 50)

    # Initialize event store
    store = EventStore()

    # Get all recent executions
    recent_executions = store.get_executions(limit=10)
    print(f"Found {len(recent_executions)} recent executions\n")

    # Display execution details
    for i, execution in enumerate(recent_executions[:5], 1):
        print(f"{i}. Agent: {execution['agent_name']}")
        print(f"   Status: {execution['status']}")
        print(f"   Duration: {execution.get('duration', 0):.2f}s")
        if 'metrics' in execution:
            metrics = execution['metrics']
            print(f"   Tokens: {metrics.get('total_tokens', 'N/A')}")
            print(f"   Cost: ${metrics.get('total_cost', 0):.4f}")
        print()

    # Example 3: Filter by agent name
    print("3. Filtering by Agent Name")
    print("-" * 50)

    translator_execs = store.get_executions(agent_name="translator", limit=5)
    print(f"Translator executions: {len(translator_execs)}")

    for execution in translator_execs:
        print(f"  - {execution['started_at']}: {execution['status']}")

    print()

    # Example 4: Get summary statistics
    print("4. Summary Statistics")
    print("-" * 50)

    # Overall stats
    overall_stats = store.get_summary_stats()
    print("Overall Statistics:")
    print(f"  Total executions: {overall_stats['total_executions']}")
    print(f"  Completed: {overall_stats['completed']}")
    print(f"  Failed: {overall_stats['failed']}")
    print(f"  Average duration: {overall_stats['avg_duration']:.2f}s")

    success_rate = (overall_stats['completed'] / overall_stats['total_executions'] * 100
                   if overall_stats['total_executions'] > 0 else 0)
    print(f"  Success rate: {success_rate:.1f}%\n")

    # Agent-specific stats
    translator_stats = store.get_summary_stats(agent_name="translator")
    if translator_stats['total_executions'] > 0:
        print("Translator Statistics:")
        print(f"  Total executions: {translator_stats['total_executions']}")
        print(f"  Average duration: {translator_stats['avg_duration']:.2f}s\n")

    # Example 5: Time-based filtering
    print("5. Time-Based Filtering")
    print("-" * 50)

    # Get executions from last 1 hour
    one_hour_ago = time.time() - 3600
    recent = store.get_executions(since=one_hour_ago, limit=100)
    print(f"Executions in last hour: {len(recent)}\n")

    # Example 6: Status filtering
    print("6. Status Filtering")
    print("-" * 50)

    completed = store.get_executions(status="completed", limit=10)
    failed = store.get_executions(status="failed", limit=10)

    print(f"Completed executions: {len(completed)}")
    print(f"Failed executions: {len(failed)}\n")

    # Example 7: Execution trace
    print("7. Detailed Execution Trace")
    print("-" * 50)

    if recent_executions:
        execution_id = recent_executions[0]['id']
        execution = store.get_execution(execution_id)

        if execution:
            print(f"Execution ID: {execution['id']}")
            print(f"Agent: {execution['agent_name']}")
            print(f"Status: {execution['status']}")
            print(f"Duration: {execution.get('duration', 0):.2f}s")

            if 'metrics' in execution:
                print("\nMetrics:")
                for key, value in execution['metrics'].items():
                    print(f"  {key}: {value}")

            if 'events' in execution:
                print(f"\nEvents: {len(execution['events'])} total")

    print()

    # Example 8: Dashboard views
    print("8. Dashboard Visualization")
    print("-" * 50)

    dashboard = Dashboard(store)

    print("\n--- Execution List ---")
    dashboard.show_list(limit=5)

    print("\n--- Summary Statistics ---")
    dashboard.show_stats()

    # Example 9: Agent comparison
    print("\n9. Comparing Agent Performance")
    print("-" * 50)

    agents = ["translator", "chatbot", "summarizer"]
    for agent_name in agents:
        stats = store.get_summary_stats(agent_name=agent_name)
        if stats['total_executions'] > 0:
            print(f"{agent_name}:")
            print(f"  Executions: {stats['total_executions']}")
            print(f"  Avg duration: {stats['avg_duration']:.2f}s")
            print(f"  Success rate: {stats['completed']/stats['total_executions']*100:.1f}%")

    print()

    # Example 10: Cleanup old data
    print("10. Data Management")
    print("-" * 50)

    # Count total records
    all_executions = store.get_executions(limit=10000)
    print(f"Total execution records: {len(all_executions)}")

    # Delete old records (older than 90 days)
    thirty_days_ago = time.time() - (30 * 86400)
    deleted = store.delete_old_executions(older_than=thirty_days_ago)
    print(f"Deleted {deleted} old records (>30 days)\n")


async def monitor_live():
    """Demonstrate live monitoring (run in separate terminal)."""
    print("=== Live Monitoring ===")
    print("This would show a live-updating dashboard.")
    print("Run this command in a separate terminal:")
    print("\n  kagura monitor\n")
    print("Or for specific agent:")
    print("\n  kagura monitor --agent translator\n")


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Show live monitoring info
    print("\n" + "=" * 60)
    asyncio.run(monitor_live())
