"""Parallel execution helpers for LLM operations

This module provides utilities for executing multiple async operations in parallel,
improving performance for independent LLM calls and file processing.

Example:
    >>> from kagura.core.parallel import parallel_gather
    >>>
    >>> results = await parallel_gather(
    ...     call_llm("prompt1", config),
    ...     call_llm("prompt2", config),
    ...     call_llm("prompt3", config)
    ... )
    >>> # All 3 calls execute concurrently (~1.5s instead of ~4.5s)
"""

import asyncio
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")


async def parallel_gather(*awaitables: Coroutine[Any, Any, T]) -> list[T]:
    """Execute multiple async operations in parallel

    This is a thin wrapper around asyncio.gather() with better type hints
    and error handling for Kagura use cases.

    Args:
        *awaitables: Coroutines to execute in parallel

    Returns:
        List of results in same order as input awaitables

    Raises:
        Exception: If any awaitable raises an exception (fail-fast)

    Example:
        >>> # Execute 3 LLM calls in parallel
        >>> from kagura.core.llm import call_llm, LLMConfig
        >>>
        >>> config = LLMConfig(model="gpt-5-mini")
        >>> results = await parallel_gather(
        ...     call_llm("Translate 'hello' to Japanese", config),
        ...     call_llm("Translate 'hello' to French", config),
        ...     call_llm("Translate 'hello' to Spanish", config)
        ... )
        >>> print(results)
        ['こんにちは', 'bonjour', 'hola']

    Performance:
        - Serial: 3 * 1.5s = 4.5s
        - Parallel: ~1.5s (3x speedup)
    """
    return list(await asyncio.gather(*awaitables))


async def parallel_map(
    func: Callable[[T], Coroutine[Any, Any, Any]],
    items: list[T],
    max_concurrent: int = 5,
) -> list[Any]:
    """Apply async function to items in parallel with concurrency limit

    Processes multiple items concurrently while limiting the number of
    concurrent operations to prevent resource exhaustion.

    Args:
        func: Async function to apply to each item
        items: List of items to process
        max_concurrent: Maximum concurrent executions (default: 5)

    Returns:
        List of results in same order as items

    Raises:
        Exception: If any function call raises an exception (fail-fast)

    Example:
        >>> from pathlib import Path
        >>>
        >>> async def load_file(path: Path) -> str:
        ...     # Expensive file loading operation
        ...     return await async_read(path)
        >>>
        >>> files = [Path(f"file{i}.txt") for i in range(50)]
        >>>
        >>> # Process 50 files with max 5 concurrent
        >>> results = await parallel_map(
        ...     load_file,
        ...     files,
        ...     max_concurrent=5
        ... )

    Performance:
        - Serial (50 files, 0.5s each): 25s
        - Parallel (max_concurrent=5): ~5s (5x speedup)

    Note:
        Uses asyncio.Semaphore to limit concurrency and prevent overwhelming
        system resources or API rate limits.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_func(item: T) -> Any:
        """Execute func with semaphore-based concurrency control"""
        async with semaphore:
            return await func(item)

    return list(await asyncio.gather(*[bounded_func(item) for item in items]))


async def parallel_map_unordered(
    func: Callable[[T], Coroutine[Any, Any, Any]],
    items: list[T],
    max_concurrent: int = 5,
) -> list[Any]:
    """Apply async function to items in parallel, returning as they complete

    Similar to parallel_map() but returns results in completion order
    rather than input order. Useful when order doesn't matter and you
    want to process results as soon as available.

    Args:
        func: Async function to apply to each item
        items: List of items to process
        max_concurrent: Maximum concurrent executions (default: 5)

    Returns:
        List of results in completion order (not input order)

    Example:
        >>> async def process_item(item: int) -> int:
        ...     await asyncio.sleep(random.random())
        ...     return item * 2
        >>>
        >>> results = await parallel_map_unordered(
        ...     process_item,
        ...     [1, 2, 3, 4, 5],
        ...     max_concurrent=3
        ... )
        >>> # results might be: [6, 2, 8, 4, 10] (completion order)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[Any] = []

    async def bounded_func(item: T) -> None:
        """Execute func and append result"""
        async with semaphore:
            result = await func(item)
            results.append(result)

    await asyncio.gather(*[bounded_func(item) for item in items])
    return results
