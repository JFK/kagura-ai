"""Image Analysis - Analyze images with multimodal LLMs

This example demonstrates:
- Using Gemini for image understanding
- Passing images to AI agents
- Vision-based analysis
"""

import asyncio
from pathlib import Path

from kagura import LLMConfig, agent

# Configure Gemini for multimodal
config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    temperature=0.7
)


@agent(config=config)
async def image_analyzer(image_path: str, question: str) -> str:
    """
    Analyze this image: {{ image_path }}

    Question: {{ question }}

    Describe what you see and answer the question.
    """
    pass


@agent(config=config)
async def image_describer(image_path: str) -> str:
    """
    Describe this image in detail: {{ image_path }}

    Include:
    - Main subjects and objects
    - Colors and composition
    - Mood and atmosphere
    - Any text visible
    """
    pass


@agent(config=config)
async def image_comparator(image1: str, image2: str) -> str:
    """
    Compare these two images:
    1. {{ image1 }}
    2. {{ image2 }}

    Describe similarities and differences.
    """
    pass


async def main():
    print("Image Analysis Demo (Gemini Vision)")
    print("-" * 50)
    print("Note: This example requires actual image files")
    print("Place test images in ./test_images/ directory")
    print()

    # Example image paths (replace with actual images)
    test_image = "./test_images/sample.jpg"

    # Check if image exists
    if not Path(test_image).exists():
        print(f"⚠️  Image not found: {test_image}")
        print("Please add test images to run this example")
        return

    # Analyze image
    print("=== Image Description ===")
    description = await image_describer(test_image)
    print(f"Description: {description}\n")

    # Ask specific questions
    print("=== Specific Analysis ===")
    questions = [
        "What colors are dominant in this image?",
        "Are there any people in the image?",
        "What's the mood or atmosphere?"
    ]

    for question in questions:
        answer = await image_analyzer(test_image, question)
        print(f"Q: {question}")
        print(f"A: {answer}\n")

    # Compare images (if multiple available)
    image2 = "./test_images/sample2.jpg"
    if Path(image2).exists():
        print("=== Image Comparison ===")
        comparison = await image_comparator(test_image, image2)
        print(f"Comparison: {comparison}")


if __name__ == "__main__":
    asyncio.run(main())
