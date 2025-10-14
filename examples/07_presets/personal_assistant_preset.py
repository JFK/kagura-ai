"""PersonalAssistantPreset - Personal productivity assistant

This example demonstrates:
- Using PersonalAssistantPreset
- Task management
- Scheduling assistance
- Productivity tips
"""

import asyncio
from kagura.presets import PersonalAssistantPreset


async def main():
    print("PersonalAssistantPreset Demo")
    print("-" * 50)

    # Create personal assistant
    assistant = (
        PersonalAssistantPreset("my_assistant")
        .with_model("gpt-4o-mini")
        .with_context(
            user_preferences="prefers morning work, likes concise summaries"
        )
        .build()
    )

    # Various assistant tasks
    tasks = [
        "Help me plan my day. I have a meeting at 2pm and need to finish a report.",
        "Give me 3 quick tips for staying focused while working from home",
        "I need to prepare for a presentation tomorrow. What should I prioritize?",
        "Suggest a daily routine for better productivity",
        "How should I organize my tasks for the week?"
    ]

    for task in tasks:
        print(f"\n{'=' * 50}")
        print(f"Request: {task}")
        print(f"{'=' * 50}")

        response = await assistant(task)
        print(f"\nAssistant:")
        print(response)

    print("\n" + "=" * 50)
    print("PersonalAssistantPreset Features:")
    print("- Task organization")
    print("- Schedule planning")
    print("- Productivity advice")
    print("- Context-aware suggestions")


if __name__ == "__main__":
    asyncio.run(main())
