"""ProjectManagerPreset - Project management assistant

This example demonstrates:
- Using ProjectManagerPreset
- Task breakdown and planning
- Timeline estimation
- Resource allocation
"""

import asyncio
from kagura.presets import ProjectManagerPreset


async def main():
    print("ProjectManagerPreset Demo")
    print("-" * 50)

    # Create project manager
    pm = (
        ProjectManagerPreset("project_manager")
        .with_model("gpt-4o-mini")
        .with_context(
            methodology="Agile",
            team_size="5 developers"
        )
        .build()
    )

    # Project management scenarios
    scenarios = [
        "We need to build a new mobile app. Help me break down the project into phases.",
        "How should we prioritize these features: user authentication, payment system, notifications, and analytics?",
        "Our sprint is not going well. We're behind schedule. What should we do?",
        "Help me create a timeline for launching a new website in 3 months",
        "What are the key risks in implementing a microservices architecture?"
    ]

    for scenario in scenarios:
        print(f"\n{'=' * 50}")
        print(f"Scenario: {scenario}")
        print(f"{'=' * 50}")

        response = await pm(scenario)
        print(f"\nProject Manager:")
        print(response)

    # Demonstrate task breakdown
    print("\n\n" + "=" * 50)
    print("Detailed Task Breakdown Example:")
    print("=" * 50)

    detailed_request = """
    Break down the task 'Implement user authentication system' into:
    - Subtasks
    - Estimated time for each
    - Dependencies
    - Required skills
    """

    breakdown = await pm(detailed_request)
    print(f"\nRequest: {detailed_request.strip()}")
    print(f"\nBreakdown:")
    print(breakdown)

    print("\n" + "=" * 50)
    print("ProjectManagerPreset Features:")
    print("- Task breakdown")
    print("- Timeline estimation")
    print("- Risk assessment")
    print("- Resource planning")


if __name__ == "__main__":
    asyncio.run(main())
