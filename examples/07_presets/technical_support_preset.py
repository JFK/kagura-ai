"""TechnicalSupportPreset - Tech support assistant

This example demonstrates:
- Using TechnicalSupportPreset
- Troubleshooting assistance
- Step-by-step solutions
- Technical explanations
"""

import asyncio
from kagura.presets import TechnicalSupportPreset


async def main():
    print("TechnicalSupportPreset Demo")
    print("-" * 50)

    # Create tech support agent
    support = (
        TechnicalSupportPreset("tech_support")
        .with_model("gpt-4o-mini")
        .with_context(
            product="Kagura AI Framework",
            expertise_level="intermediate"
        )
        .build()
    )

    # Support tickets
    tickets = [
        "I'm getting an ImportError when trying to use @agent decorator",
        "How do I enable memory for my agent?",
        "My agent is running slowly, how can I improve performance?",
        "I want to use a custom LLM model, how do I configure that?",
        "What's the difference between WorkingMemory and PersistentMemory?"
    ]

    for i, ticket in enumerate(tickets, 1):
        print(f"\n{'=' * 50}")
        print(f"Ticket #{i}: {ticket}")
        print(f"{'=' * 50}")

        response = await support(ticket)
        print(f"\nSupport Response:")
        print(response)

    print("\n" + "=" * 50)
    print("TechnicalSupportPreset Features:")
    print("- Step-by-step troubleshooting")
    print("- Code examples")
    print("- Clear explanations")
    print("- Solution-focused responses")


if __name__ == "__main__":
    asyncio.run(main())
