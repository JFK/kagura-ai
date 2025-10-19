"""Caching Demo - Performance benefits of LLM caching

This example demonstrates:
- Cache hits vs misses
- Performance improvements
- Cost savings
- Cache management
"""

import asyncio
import time
from kagura import agent, LLMConfig, get_llm_cache


# Config with caching enabled
cached_config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)


@agent(config=cached_config)
async def translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}."""
    pass


@agent(config=cached_config)
async def explainer(concept: str) -> str:
    """Explain {{ concept }} in simple terms."""
    pass


async def benchmark_translation():
    """Benchmark translation with caching"""
    print("=== Translation Benchmark ===")

    text = "Hello, how are you today?"
    target = "Spanish"

    # First call (cache miss)
    print("\n1. First call (cache miss):")
    start = time.time()
    result1 = await translator(text, target)
    time1 = time.time() - start
    print(f"   Time: {time1:.3f}s")
    print(f"   Result: {str(result1)}")

    # Second call (cache hit)
    print("\n2. Second call (cache hit):")
    start = time.time()
    result2 = await translator(text, target)
    time2 = time.time() - start
    print(f"   Time: {time2:.3f}s")
    print(f"   Result: {result2}")

    speedup = time1 / time2 if time2 > 0 else 0
    print(f"\n   ⚡ Speedup: {speedup:.1f}x faster!")

    # Third call (still cached)
    print("\n3. Third call (still cached):")
    start = time.time()
    result3 = await translator(text, target)
    time3 = time.time() - start
    print(f"   Time: {time3:.3f}s")


async def demonstrate_cache_stats():
    """Show cache statistics"""
    print("\n\n=== Cache Statistics ===")

    # Get cache instance
    cache = get_llm_cache()

    # Make some calls
    await explainer("quantum computing")
    await explainer("quantum computing")  # Cache hit
    await explainer("machine learning")  # Cache miss

    # Get stats
    stats = cache.stats()

    print(f"\nCache Performance:")
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Cache hits: {stats.get('hits', 0)}")
    print(f"  Cache misses: {stats.get('misses', 0)}")
    print(f"  Hit rate: {stats.get('hit_rate', 0):.1%}")


async def demonstrate_cache_invalidation():
    """Show cache invalidation"""
    print("\n\n=== Cache Invalidation ===")

    cache = get_llm_cache()
    concept = "neural networks"

    # First call
    print("\n1. First call:")
    result1 = await explainer(concept)
    print(f"   Result: {str(result1)[:50]}...")

    # Second call (cached)
    print("\n2. Second call (cached):")
    start = time.time()
    result2 = await explainer(concept)
    cached_time = time.time() - start
    print(f"   Time: {cached_time:.3f}s (fast!)")

    # Invalidate cache
    print("\n3. Invalidating cache...")
    await cache.invalidate()

    # Third call (cache miss after invalidation)
    print("\n4. Third call (after invalidation):")
    start = time.time()
    result3 = await explainer(concept)
    uncached_time = time.time() - start
    print(f"   Time: {uncached_time:.3f}s (slower)")


async def demonstrate_cost_savings():
    """Estimate cost savings from caching"""
    print("\n\n=== Cost Savings Estimation ===")

    # Simulate 100 repeated queries
    queries = [
        ("What is Python?", "general"),
        ("Explain JavaScript", "general"),
        ("What is Python?", "general"),  # Duplicate
        ("Explain JavaScript", "general"),  # Duplicate
    ] * 25  # 100 total queries

    cache_hits = 0
    start = time.time()

    for query, _ in queries:
        await explainer(query)
        # Check if this would be a cache hit (simplified)
        cache_hits += 1 if queries.count((query, _)) > 1 else 0

    total_time = time.time() - start

    # Rough cost estimation (example rates)
    cost_per_call = 0.0001  # $0.0001 per call
    total_calls = len(queries)
    unique_calls = len(set(q for q, _ in queries))

    uncached_cost = total_calls * cost_per_call
    cached_cost = unique_calls * cost_per_call

    print(f"\nSimulated 100 queries:")
    print(f"  Unique queries: {unique_calls}")
    print(f"  Cache hits: {total_calls - unique_calls}")
    print(f"  Time: {total_time:.2f}s")
    print(f"\nCost comparison:")
    print(f"  Without caching: ${uncached_cost:.4f}")
    print(f"  With caching: ${cached_cost:.4f}")
    print(f"  Savings: ${uncached_cost - cached_cost:.4f} ({(1 - cached_cost/uncached_cost)*100:.1f}%)")


async def main():
    print("LLM Caching Performance Demo")
    print("=" * 60)

    await benchmark_translation()
    await demonstrate_cache_stats()
    await demonstrate_cache_invalidation()
    await demonstrate_cost_savings()

    print("\n" + "=" * 60)
    print("Summary: Caching provides significant speedups and cost savings!")


if __name__ == "__main__":
    asyncio.run(main())
