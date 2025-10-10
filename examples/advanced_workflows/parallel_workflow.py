"""Parallel Workflow Example

This example demonstrates parallel execution of agents for improved
performance and efficiency in workflows.
"""

import asyncio
import time
from kagura import agent, workflow


# Define workflow agents
@agent(model="gpt-4o-mini")
async def translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}"""
    pass


@agent(model="gpt-4o-mini")
async def sentiment_analyzer(text: str) -> str:
    """Analyze sentiment: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def summarizer(text: str) -> str:
    """Summarize: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def keyword_extractor(text: str) -> str:
    """Extract keywords from: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def language_detector(text: str) -> str:
    """Detect language of: {{ text }}"""
    pass


async def main():
    """Demonstrate parallel workflows."""
    print("=== Parallel Workflow Examples ===\n")

    # Example 1: Basic parallel execution
    print("1. Basic Parallel Execution")
    print("-" * 50)

    @workflow
    async def parallel_analysis(text: str) -> dict:
        """Run multiple analyses in parallel."""
        # Run all analyses concurrently
        sentiment_task = sentiment_analyzer(text)
        keywords_task = keyword_extractor(text)
        summary_task = summarizer(text)

        # Wait for all to complete
        sentiment, keywords, summary = await asyncio.gather(
            sentiment_task,
            keywords_task,
            summary_task
        )

        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "summary": summary
        }

    text = "Python is an amazing programming language with great community support."
    start_time = time.time()

    result = await parallel_analysis(text)

    elapsed = time.time() - start_time

    print(f"Input: {text}")
    print(f"\nResults (completed in {elapsed:.2f}s):")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Keywords: {result['keywords']}")
    print(f"Summary: {result['summary']}\n")

    # Example 2: Parallel translations
    print("2. Parallel Multi-Language Translation")
    print("-" * 50)

    @workflow
    async def multi_language_translate(text: str) -> dict:
        """Translate to multiple languages in parallel."""
        tasks = {
            "french": translator(text, "French"),
            "spanish": translator(text, "Spanish"),
            "german": translator(text, "German"),
            "japanese": translator(text, "Japanese"),
        }

        # Execute all translations concurrently
        results = {}
        for lang, task in tasks.items():
            results[lang] = await task

        return results

    text = "Hello, how are you?"
    start_time = time.time()

    translations = await multi_language_translate(text)

    elapsed = time.time() - start_time

    print(f"Original: {text}")
    print(f"\nTranslations (completed in {elapsed:.2f}s):")
    for lang, translation in translations.items():
        print(f"  {lang.capitalize()}: {translation}")

    print()

    # Example 3: Parallel with asyncio.gather
    print("3. Using asyncio.gather")
    print("-" * 50)

    @workflow
    async def comprehensive_analysis(text: str) -> dict:
        """Comprehensive parallel analysis."""
        # Create all tasks
        tasks = [
            sentiment_analyzer(text),
            keyword_extractor(text),
            summarizer(text),
            language_detector(text),
        ]

        # Execute in parallel
        results = await asyncio.gather(*tasks)

        return {
            "sentiment": results[0],
            "keywords": results[1],
            "summary": results[2],
            "language": results[3],
        }

    text = "Artificial intelligence is transforming the world."
    result = await comprehensive_analysis(text)

    print("Comprehensive analysis results:")
    for key, value in result.items():
        print(f"  {key.capitalize()}: {value}")

    print()

    # Example 4: Parallel with error handling
    print("4. Parallel with Error Handling")
    print("-" * 50)

    @workflow
    async def safe_parallel_analysis(text: str) -> dict:
        """Parallel execution with individual error handling."""
        async def safe_sentiment():
            try:
                return await sentiment_analyzer(text)
            except Exception as e:
                return f"Error: {str(e)}"

        async def safe_keywords():
            try:
                return await keyword_extractor(text)
            except Exception as e:
                return f"Error: {str(e)}"

        async def safe_summary():
            try:
                return await summarizer(text)
            except Exception as e:
                return f"Error: {str(e)}"

        # Run in parallel with error protection
        sentiment, keywords, summary = await asyncio.gather(
            safe_sentiment(),
            safe_keywords(),
            safe_summary()
        )

        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "summary": summary
        }

    result = await safe_parallel_analysis("Test text")
    print("Safe parallel results:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print()

    # Example 5: Parallel batching
    print("5. Parallel Batch Processing")
    print("-" * 50)

    @workflow
    async def batch_translate(texts: list[str], target_lang: str) -> list[str]:
        """Translate multiple texts in parallel."""
        # Create tasks for all texts
        tasks = [translator(text, target_lang) for text in texts]

        # Execute all in parallel
        results = await asyncio.gather(*tasks)

        return results

    texts = [
        "Hello",
        "Goodbye",
        "Thank you",
        "Good morning",
    ]

    start_time = time.time()
    translations = await batch_translate(texts, "French")
    elapsed = time.time() - start_time

    print(f"Translated {len(texts)} texts to French in {elapsed:.2f}s:")
    for original, translated in zip(texts, translations):
        print(f"  {original} → {translated}")

    print()

    # Example 6: Mixed parallel and sequential
    print("6. Mixed Parallel and Sequential")
    print("-" * 50)

    @workflow
    async def hybrid_workflow(text: str) -> str:
        """Mix parallel and sequential operations."""
        # Phase 1: Parallel analysis
        sentiment_task = sentiment_analyzer(text)
        keywords_task = keyword_extractor(text)

        sentiment, keywords = await asyncio.gather(
            sentiment_task,
            keywords_task
        )

        # Phase 2: Sequential processing using results
        summary = await summarizer(
            f"Text with {sentiment} sentiment containing keywords: {keywords}"
        )

        return summary

    result = await hybrid_workflow("Python is great for ML")
    print(f"Hybrid workflow result: {result}\n")

    # Example 7: Parallel with timeouts
    print("7. Parallel with Timeout")
    print("-" * 50)

    @workflow
    async def timeout_workflow(text: str, timeout: float = 5.0) -> dict:
        """Parallel execution with timeout."""
        tasks = {
            "sentiment": sentiment_analyzer(text),
            "keywords": keyword_extractor(text),
            "summary": summarizer(text),
        }

        results = {}
        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(task, timeout=timeout)
                results[name] = result
            except asyncio.TimeoutError:
                results[name] = f"Timeout after {timeout}s"

        return results

    result = await timeout_workflow("Test", timeout=10.0)
    print("Timeout workflow results:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print()

    # Example 8: Dependent parallel tasks
    print("8. Dependent Parallel Tasks")
    print("-" * 50)

    @workflow
    async def dependent_parallel(text: str) -> dict:
        """Handle dependencies in parallel execution."""
        # Phase 1: Independent parallel tasks
        lang_task = language_detector(text)
        sentiment_task = sentiment_analyzer(text)

        language, sentiment = await asyncio.gather(lang_task, sentiment_task)

        # Phase 2: Parallel tasks dependent on Phase 1
        if "english" in language.lower():
            # English-specific parallel processing
            keywords_task = keyword_extractor(text)
            summary_task = summarizer(text)

            keywords, summary = await asyncio.gather(
                keywords_task,
                summary_task
            )

            return {
                "language": language,
                "sentiment": sentiment,
                "keywords": keywords,
                "summary": summary
            }
        else:
            # Non-English handling
            return {
                "language": language,
                "sentiment": sentiment,
                "note": "Additional processing skipped for non-English"
            }

    result = await dependent_parallel("Python is amazing")
    print("Dependent parallel results:")
    for key, value in result.items():
        print(f"  {key}: {value}")

    print()


async def performance_comparison():
    """Compare sequential vs parallel performance."""
    print("\n" + "=" * 60)
    print("=== Performance Comparison ===\n")

    text = "Python is a versatile programming language."

    # Sequential execution
    print("Sequential Execution:")
    print("-" * 50)

    @workflow
    async def sequential_workflow(text: str) -> dict:
        """Sequential execution."""
        sentiment = await sentiment_analyzer(text)
        keywords = await keyword_extractor(text)
        summary = await summarizer(text)

        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "summary": summary
        }

    start_time = time.time()
    result = await sequential_workflow(text)
    sequential_time = time.time() - start_time

    print(f"Completed in {sequential_time:.2f}s\n")

    # Parallel execution
    print("Parallel Execution:")
    print("-" * 50)

    @workflow
    async def parallel_workflow(text: str) -> dict:
        """Parallel execution."""
        sentiment, keywords, summary = await asyncio.gather(
            sentiment_analyzer(text),
            keyword_extractor(text),
            summarizer(text)
        )

        return {
            "sentiment": sentiment,
            "keywords": keywords,
            "summary": summary
        }

    start_time = time.time()
    result = await parallel_workflow(text)
    parallel_time = time.time() - start_time

    print(f"Completed in {parallel_time:.2f}s\n")

    # Comparison
    print("Performance Comparison:")
    print("-" * 50)
    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    if sequential_time > 0:
        speedup = sequential_time / parallel_time
        print(f"Speedup: {speedup:.2f}x faster\n")


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Run performance comparison
    asyncio.run(performance_comparison())

    print("=" * 60)
    print("Parallel workflow examples complete! 🎉")
