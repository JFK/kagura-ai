"""Parallel Execution - Speed up with concurrent LLM calls

This example demonstrates:
- parallel_gather for concurrent operations
- parallel_map for batch processing
- Performance improvements
- Real-world use cases
"""

import asyncio
import time

from kagura import LLMConfig, agent
from kagura.core.parallel import parallel_gather, parallel_map

config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_cache=False  # Disable for fair benchmark
)


@agent(config=config)
async def translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}."""
    pass


@agent(config=config)
async def sentiment_analyzer(text: str) -> str:
    """Analyze sentiment of: "{{ text }}"
    Return: positive, negative, or neutral with brief reasoning."""
    pass


@agent(config=config)
async def summarizer(text: str) -> str:
    """Summarize this text in one sentence: {{ text }}"""
    pass


async def demo_parallel_gather():
    """Demonstrate parallel_gather for independent operations"""
    print("=== Demo 1: Parallel Gather ===")
    print("Translating one text to 3 languages...\n")

    text = "Hello, welcome to Kagura AI!"

    # Serial execution
    print("Serial execution:")
    start = time.time()
    spanish = await translator(text, "Spanish")
    french = await translator(text, "French")
    japanese = await translator(text, "Japanese")
    serial_time = time.time() - start
    print(f"  Spanish: {spanish}")
    print(f"  French: {french}")
    print(f"  Japanese: {japanese}")
    print(f"  Time: {serial_time:.2f}s")

    # Parallel execution
    print("\nParallel execution (parallel_gather):")
    start = time.time()
    spanish, french, japanese = await parallel_gather(
        translator(text, "Spanish"),
        translator(text, "French"),
        translator(text, "Japanese")
    )
    parallel_time = time.time() - start
    print(f"  Spanish: {spanish}")
    print(f"  French: {french}")
    print(f"  Japanese: {japanese}")
    print(f"  Time: {parallel_time:.2f}s")

    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print(f"\n  ⚡ Speedup: {speedup:.1f}x faster!")


async def demo_parallel_map():
    """Demonstrate parallel_map for batch processing"""
    print("\n\n=== Demo 2: Parallel Map ===")
    print("Analyzing sentiment of 10 reviews...\n")

    reviews = [
        "This product is amazing!",
        "Terrible experience, very disappointed.",
        "It's okay, nothing special.",
        "Absolutely love it, highly recommend!",
        "Worst purchase ever.",
        "Pretty good, met my expectations.",
        "Fantastic quality and service!",
        "Not worth the money.",
        "Decent product for the price.",
        "Exceptional! Beyond my expectations!"
    ]

    # Serial processing
    print("Serial processing:")
    start = time.time()
    serial_results = []
    for review in reviews:
        result = await sentiment_analyzer(review)
        serial_results.append(result)
    serial_time = time.time() - start
    print(f"  Processed {len(reviews)} reviews")
    print(f"  Time: {serial_time:.2f}s")

    # Parallel processing with parallel_map
    print("\nParallel processing (parallel_map):")
    start = time.time()
    parallel_results = await parallel_map(
        lambda review: sentiment_analyzer(review),
        reviews,
        max_concurrent=5  # Process 5 at a time
    )
    parallel_time = time.time() - start
    print(f"  Processed {len(reviews)} reviews")
    print(f"  Time: {parallel_time:.2f}s")

    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print(f"\n  ⚡ Speedup: {speedup:.1f}x faster!")

    # Show some results
    print("\n  Sample results:")
    for i in range(3):
        print(f"    '{reviews[i][:30]}...' -> {parallel_results[i]}")


async def demo_multi_agent_pipeline():
    """Demonstrate parallel pipeline with multiple agents"""
    print("\n\n=== Demo 3: Multi-Agent Pipeline ===")
    print("Processing article: translate, summarize, analyze...\n")

    article = """
    Artificial Intelligence is transforming industries worldwide.
    Machine learning models can now perform complex tasks with high accuracy.
    The future of AI looks incredibly promising.
    """

    # Serial pipeline
    print("Serial pipeline:")
    start = time.time()
    translated = await translator(article, "Spanish")
    summarized = await summarizer(article)
    sentiment = await sentiment_analyzer(article)
    serial_time = time.time() - start
    print(f"  Time: {serial_time:.2f}s")

    # Parallel pipeline (all independent)
    print("\nParallel pipeline:")
    start = time.time()
    translated, summarized, sentiment = await parallel_gather(
        translator(article, "Spanish"),
        summarizer(article),
        sentiment_analyzer(article)
    )
    parallel_time = time.time() - start
    print(f"  Translation: {translated[:60]}...")
    print(f"  Summary: {summarized}")
    print(f"  Sentiment: {sentiment}")
    print(f"  Time: {parallel_time:.2f}s")

    speedup = serial_time / parallel_time if parallel_time > 0 else 0
    print(f"\n  ⚡ Speedup: {speedup:.1f}x faster!")


async def main():
    print("Parallel Execution Demo (RFC-025)")
    print("=" * 60)

    await demo_parallel_gather()
    await demo_parallel_map()
    await demo_multi_agent_pipeline()

    print("\n" + "=" * 60)
    print("Summary: Parallel execution provides significant speedups")
    print("for independent LLM operations!")


if __name__ == "__main__":
    asyncio.run(main())
