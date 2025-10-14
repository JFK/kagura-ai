"""ResearchPreset - Research and analysis agent

This example demonstrates:
- Using ResearchPreset for investigations
- Structured research outputs
- Citation and source tracking
"""

import asyncio
from kagura.presets import ResearchPreset


async def main():
    print("ResearchPreset Demo")
    print("-" * 50)

    # Create research agent
    researcher = (
        ResearchPreset("researcher")
        .with_model("gpt-4o-mini")
        .build()
    )

    # Research topics
    topics = [
        "What are the latest developments in quantum computing?",
        "Compare Python and Rust for systems programming",
        "What are the ethical implications of AI?"
    ]

    for topic in topics:
        print(f"\n{'=' * 50}")
        print(f"Research Topic: {topic}")
        print(f"{'=' * 50}")

        research = await researcher(topic)
        print(f"\nResearch Report:")
        print(research)

    print("\n" + "=" * 50)
    print("ResearchPreset Features:")
    print("- Comprehensive analysis")
    print("- Structured findings")
    print("- Citation tracking")
    print("- Multi-perspective views")


if __name__ == "__main__":
    asyncio.run(main())
