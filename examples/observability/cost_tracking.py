"""Cost Tracking Example

This example demonstrates how to track and analyze costs for agent operations
using Kagura's observability features.
"""

import asyncio
import time
from kagura import agent
from kagura.observability import EventStore, Dashboard


# Define agents with different cost profiles
@agent(model="gpt-4o-mini")  # Low cost
async def cheap_agent(query: str) -> str:
    """Quick answer: {{ query }}"""
    pass


@agent(model="gpt-4o")  # Higher cost
async def premium_agent(query: str) -> str:
    """Detailed analysis: {{ query }}"""
    pass


@agent(model="gpt-4o-mini", enable_memory=True)  # Low cost with memory
async def efficient_chatbot(message: str) -> str:
    """Chat: {{ message }}"""
    pass


async def main():
    """Demonstrate cost tracking and analysis."""
    print("=== Cost Tracking Example ===\n")

    # Example 1: Run agents with different cost profiles
    print("1. Running Agents with Different Cost Profiles")
    print("-" * 50)

    # Run cheap agent multiple times
    print("Running cheap agent (gpt-4o-mini)...")
    for i in range(5):
        await cheap_agent(f"Quick question {i}")
    print("✓ Completed 5 cheap agent calls\n")

    # Run premium agent fewer times
    print("Running premium agent (gpt-4o)...")
    for i in range(2):
        await premium_agent(f"Complex analysis {i}")
    print("✓ Completed 2 premium agent calls\n")

    # Run efficient chatbot
    print("Running efficient chatbot (gpt-4o-mini with memory)...")
    for i in range(3):
        await efficient_chatbot(f"Message {i}")
    print("✓ Completed 3 chatbot calls\n")

    # Example 2: Analyze total costs
    print("2. Total Cost Analysis")
    print("-" * 50)

    store = EventStore()
    dashboard = Dashboard(store)

    # Show cost summary
    dashboard.show_cost_summary()
    print()

    # Example 3: Cost by agent
    print("3. Cost Breakdown by Agent")
    print("-" * 50)

    agents = ["cheap_agent", "premium_agent", "efficient_chatbot"]
    total_cost = 0.0

    for agent_name in agents:
        executions = store.get_executions(agent_name=agent_name, limit=100)

        if executions:
            agent_cost = sum(
                exec.get('metrics', {}).get('total_cost', 0)
                for exec in executions
            )
            call_count = len(executions)

            print(f"{agent_name}:")
            print(f"  Calls: {call_count}")
            print(f"  Total cost: ${agent_cost:.4f}")
            print(f"  Avg cost/call: ${agent_cost/call_count:.4f}")

            total_cost += agent_cost

    print(f"\nOverall total cost: ${total_cost:.4f}\n")

    # Example 4: Cost over time
    print("4. Cost Trends Over Time")
    print("-" * 50)

    # Last hour
    one_hour_ago = time.time() - 3600
    hour_executions = store.get_executions(since=one_hour_ago, limit=1000)
    hour_cost = sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in hour_executions
    )

    # Last day
    one_day_ago = time.time() - 86400
    day_executions = store.get_executions(since=one_day_ago, limit=10000)
    day_cost = sum(
        exec.get('metrics', {}).get('total_cost', 0)
        for exec in day_executions
    )

    print(f"Cost in last hour: ${hour_cost:.4f}")
    print(f"Cost in last day: ${day_cost:.4f}")

    # Estimate monthly cost
    if day_cost > 0:
        estimated_monthly = day_cost * 30
        print(f"Estimated monthly cost: ${estimated_monthly:.2f}\n")

    # Example 5: Token usage analysis
    print("5. Token Usage Analysis")
    print("-" * 50)

    for agent_name in agents:
        executions = store.get_executions(agent_name=agent_name, limit=100)

        if executions:
            total_tokens = sum(
                exec.get('metrics', {}).get('total_tokens', 0)
                for exec in executions
            )
            avg_tokens = total_tokens / len(executions) if executions else 0

            print(f"{agent_name}:")
            print(f"  Total tokens: {total_tokens:,}")
            print(f"  Avg tokens/call: {avg_tokens:.0f}")

    print()

    # Example 6: Cost optimization recommendations
    print("6. Cost Optimization Recommendations")
    print("-" * 50)

    print("Analysis:")

    # Check for expensive model usage
    premium_executions = store.get_executions(agent_name="premium_agent", limit=100)
    if premium_executions:
        premium_cost = sum(
            exec.get('metrics', {}).get('total_cost', 0)
            for exec in premium_executions
        )
        print(f"✓ Premium agent (gpt-4o) cost: ${premium_cost:.4f}")
        print("  → Consider using gpt-4o-mini for simpler tasks")

    # Check cheap agent efficiency
    cheap_executions = store.get_executions(agent_name="cheap_agent", limit=100)
    if cheap_executions:
        cheap_cost = sum(
            exec.get('metrics', {}).get('total_cost', 0)
            for exec in cheap_executions
        )
        print(f"✓ Cheap agent (gpt-4o-mini) cost: ${cheap_cost:.4f}")
        print("  → Good: Using cost-effective model")

    # Check memory usage efficiency
    chatbot_executions = store.get_executions(agent_name="efficient_chatbot", limit=100)
    if chatbot_executions:
        chatbot_cost = sum(
            exec.get('metrics', {}).get('total_cost', 0)
            for exec in chatbot_executions
        )
        avg_cost = chatbot_cost / len(chatbot_executions)
        print(f"✓ Chatbot with memory cost: ${chatbot_cost:.4f}")
        print(f"  → Avg cost per message: ${avg_cost:.4f}")

    print()

    # Example 7: Cost alerts
    print("7. Cost Alert Simulation")
    print("-" * 50)

    # Set cost thresholds
    DAILY_THRESHOLD = 1.0  # $1.00 per day
    HOURLY_THRESHOLD = 0.1  # $0.10 per hour

    if hour_cost > HOURLY_THRESHOLD:
        print(f"⚠️  ALERT: Hourly cost ${hour_cost:.4f} exceeds threshold ${HOURLY_THRESHOLD:.2f}")
    else:
        print(f"✓ Hourly cost ${hour_cost:.4f} within threshold")

    if day_cost > DAILY_THRESHOLD:
        print(f"⚠️  ALERT: Daily cost ${day_cost:.4f} exceeds threshold ${DAILY_THRESHOLD:.2f}")
    else:
        print(f"✓ Daily cost ${day_cost:.4f} within threshold")

    print()

    # Example 8: Cost per feature/use case
    print("8. Cost by Use Case")
    print("-" * 50)

    # Simulate different use cases
    use_cases = {
        "translation": ["cheap_agent"],  # Translation tasks
        "analysis": ["premium_agent"],   # Deep analysis tasks
        "chat": ["efficient_chatbot"],   # Conversational tasks
    }

    for use_case, agent_names in use_cases.items():
        use_case_cost = 0.0
        use_case_calls = 0

        for agent_name in agent_names:
            executions = store.get_executions(agent_name=agent_name, limit=100)
            use_case_cost += sum(
                exec.get('metrics', {}).get('total_cost', 0)
                for exec in executions
            )
            use_case_calls += len(executions)

        if use_case_calls > 0:
            print(f"{use_case}:")
            print(f"  Total calls: {use_case_calls}")
            print(f"  Total cost: ${use_case_cost:.4f}")
            print(f"  Avg cost/call: ${use_case_cost/use_case_calls:.4f}")

    print()

    # Example 9: ROI calculation
    print("9. Return on Investment (ROI)")
    print("-" * 50)

    # Simulate ROI calculation
    total_agent_cost = total_cost
    total_calls = len(store.get_executions(limit=10000))

    # Assumptions for ROI calculation
    manual_cost_per_task = 5.0  # $5 if done manually
    time_saved_per_call = 10  # 10 minutes saved per call

    total_manual_cost = total_calls * manual_cost_per_task
    cost_savings = total_manual_cost - total_agent_cost
    roi_percentage = (cost_savings / total_agent_cost * 100) if total_agent_cost > 0 else 0

    print(f"Total agent calls: {total_calls}")
    print(f"Total agent cost: ${total_agent_cost:.4f}")
    print(f"Manual cost (${manual_cost_per_task}/task): ${total_manual_cost:.2f}")
    print(f"Cost savings: ${cost_savings:.2f}")
    print(f"ROI: {roi_percentage:.0f}%")
    print(f"Time saved: {total_calls * time_saved_per_call} minutes\n")

    # Example 10: Cost optimization strategies
    print("10. Cost Optimization Strategies")
    print("-" * 50)

    print("Strategies to reduce costs:")
    print("1. Use gpt-4o-mini for simple tasks (90% cheaper than gpt-4o)")
    print("2. Implement caching for repeated queries")
    print("3. Enable memory to maintain context without re-processing")
    print("4. Use shorter prompts when possible")
    print("5. Set max_tokens limits appropriately")
    print("6. Batch similar requests together")
    print("7. Monitor and alert on cost thresholds")
    print("8. Regularly review and optimize agent prompts")
    print("9. Use async/concurrent execution to improve efficiency")
    print("10. Archive old telemetry data to reduce storage costs\n")


async def cost_monitoring_cli():
    """Show CLI commands for cost monitoring."""
    print("=== Cost Monitoring CLI Commands ===\n")

    print("Monitor costs in real-time:")
    print("  kagura monitor cost\n")

    print("View cost by agent:")
    print("  kagura monitor cost --group-by agent\n")

    print("View cost by date:")
    print("  kagura monitor cost --group-by date\n")

    print("View cost for specific period:")
    print("  kagura monitor stats --since 2025-01-01\n")


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Show CLI commands
    print("\n" + "=" * 60)
    asyncio.run(cost_monitoring_cli())
