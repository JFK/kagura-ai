"""LLM Configuration - Using LLMConfig with caching

This example demonstrates:
- Creating custom LLMConfig
- Enabling/disabling caching
- Configuring model parameters
- Performance benefits of caching
"""

import asyncio
import time

from kagura import LLMConfig, agent

# Create config with caching enabled (default)
cached_config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=200,
    enable_cache=True,  # Cache responses for faster repeat calls
    cache_ttl=3600      # Cache for 1 hour
)

# Create config with caching disabled
no_cache_config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=200,
    enable_cache=False  # Disable caching
)


@agent(config=cached_config)
async def cached_translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}."""
    pass


@agent(config=no_cache_config)
async def no_cache_translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}."""
    pass


async def benchmark_caching():
    """Demonstrate caching performance benefits"""
    text = "Hello, how are you?"
    target = "Japanese"

    # First call (cache miss)
    print("With caching enabled:")
    start = time.time()
    result1 = await cached_translator(text, target)
    first_call_time = time.time() - start
    print(f"  First call: {first_call_time:.2f}s - {result1}")

    # Second call (cache hit - should be much faster)
    start = time.time()
    result2 = await cached_translator(text, target)
    second_call_time = time.time() - start
    print(f"  Second call: {second_call_time:.2f}s - {result2}")
    print(f"  Speedup: {first_call_time/second_call_time:.1f}x faster!")
    print()

    # Without caching (both calls take full time)
    print("Without caching:")
    start = time.time()
    result3 = await no_cache_translator(text, target)
    first_time = time.time() - start
    print(f"  First call: {first_time:.2f}s - {result3}")

    start = time.time()
    result4 = await no_cache_translator(text, target)
    second_time = time.time() - start
    print(f"  Second call: {second_time:.2f}s - {result4}")


async def main():
    await benchmark_caching()


if __name__ == "__main__":
    asyncio.run(main())
