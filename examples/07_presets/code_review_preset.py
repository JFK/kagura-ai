"""CodeReviewPreset - Automated code review agent

This example demonstrates:
- Using CodeReviewPreset for code analysis
- Finding bugs and issues
- Suggesting improvements
"""

import asyncio
from kagura.presets import CodeReviewPreset


async def main():
    print("CodeReviewPreset Demo")
    print("-" * 50)

    # Create code reviewer
    reviewer = (
        CodeReviewPreset("code_reviewer")
        .with_model("gpt-4o-mini")
        .build()
    )

    # Code samples to review
    code_samples = [
        """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)
""",
        """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
""",
        """
class User:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_info(self):
        return f"{self.name} is {self.age} years old"
"""
    ]

    for i, code in enumerate(code_samples, 1):
        print(f"\n{'=' * 50}")
        print(f"Code Sample {i}:")
        print(code)
        print(f"{'=' * 50}")

        review = await reviewer(code)
        print(f"\nReview:")
        print(review)

    print("\n" + "=" * 50)
    print("CodeReviewPreset Features:")
    print("- Bug detection")
    print("- Performance suggestions")
    print("- Best practices")
    print("- Code quality analysis")


if __name__ == "__main__":
    asyncio.run(main())
