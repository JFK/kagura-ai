"""LearningTutorPreset - Educational tutor agent

This example demonstrates:
- Using LearningTutorPreset for teaching
- Adaptive explanations
- Practice problems
- Learning path guidance
"""

import asyncio
from kagura.presets import LearningTutorPreset


async def main():
    print("LearningTutorPreset Demo")
    print("-" * 50)

    # Create tutor
    tutor = (
        LearningTutorPreset("python_tutor")
        .with_model("gpt-4o-mini")
        .with_context(
            subject="Python programming",
            student_level="beginner"
        )
        .build()
    )

    # Learning interactions
    interactions = [
        "Explain what a variable is in Python",
        "Can you show me examples of different data types?",
        "I don't understand how functions work",
        "Give me a practice problem about loops",
        "What's the difference between a list and a tuple?"
    ]

    for interaction in interactions:
        print(f"\n{'=' * 50}")
        print(f"Student: {interaction}")
        print(f"{'=' * 50}")

        response = await tutor(interaction)
        print(f"\nTutor:")
        print(response)

    # Demonstrate adaptive difficulty
    print("\n\n" + "=" * 50)
    print("Requesting practice problems at different levels:")
    print("=" * 50)

    levels = ["beginner", "intermediate", "advanced"]
    for level in levels:
        tutor_level = (
            LearningTutorPreset(f"tutor_{level}")
            .with_model("gpt-4o-mini")
            .with_context(
                subject="Python programming",
                student_level=level
            )
            .build()
        )

        response = await tutor_level(
            "Give me a coding challenge appropriate for my level"
        )
        print(f"\n{level.title()} Level:")
        print(response)

    print("\n" + "=" * 50)
    print("LearningTutorPreset Features:")
    print("- Adaptive explanations")
    print("- Practice problems")
    print("- Concept breakdowns")
    print("- Patient teaching style")


if __name__ == "__main__":
    asyncio.run(main())
