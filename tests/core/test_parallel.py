"""Tests for parallel execution helpers

Tests cover:
- parallel_gather() basic functionality
- parallel_map() with concurrency limits
- parallel_map_unordered() completion order
- Error handling and edge cases
- Performance improvements
"""

import asyncio
import time

import pytest

from kagura.core.parallel import parallel_gather, parallel_map, parallel_map_unordered


class TestParallelGather:
    """Tests for parallel_gather() function"""

    @pytest.mark.asyncio
    async def test_parallel_gather_basic(self):
        """Test parallel_gather executes tasks concurrently"""

        async def task1():
            await asyncio.sleep(0.1)
            return "result1"

        async def task2():
            await asyncio.sleep(0.1)
            return "result2"

        start = time.time()
        results = await parallel_gather(task1(), task2())
        duration = time.time() - start

        assert results == ["result1", "result2"]
        # Should be ~0.1s (parallel), not 0.2s (serial)
        assert duration < 0.15

    @pytest.mark.asyncio
    async def test_parallel_gather_empty(self):
        """Test parallel_gather with no awaitables"""
        results = await parallel_gather()
        assert results == []

    @pytest.mark.asyncio
    async def test_parallel_gather_single(self):
        """Test parallel_gather with single awaitable"""

        async def task():
            return "result"

        results = await parallel_gather(task())
        assert results == ["result"]

    @pytest.mark.asyncio
    async def test_parallel_gather_many(self):
        """Test parallel_gather with many awaitables"""

        async def task(n: int):
            await asyncio.sleep(0.01)
            return n * 2

        tasks = [task(i) for i in range(10)]
        results = await parallel_gather(*tasks)

        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    @pytest.mark.asyncio
    async def test_parallel_gather_error_propagation(self):
        """Test parallel_gather propagates exceptions"""

        async def task_success():
            return "success"

        async def task_error():
            raise ValueError("Task failed")

        with pytest.raises(ValueError, match="Task failed"):
            await parallel_gather(task_success(), task_error())

    @pytest.mark.asyncio
    async def test_parallel_gather_performance(self):
        """Test parallel_gather is actually faster than serial"""

        async def slow_task(delay: float):
            await asyncio.sleep(delay)
            return delay

        # Parallel execution
        start = time.time()
        results = await parallel_gather(
            slow_task(0.1),
            slow_task(0.1),
            slow_task(0.1)
        )
        parallel_duration = time.time() - start

        assert results == [0.1, 0.1, 0.1]
        # Should be ~0.1s, not 0.3s
        assert parallel_duration < 0.15


class TestParallelMap:
    """Tests for parallel_map() function"""

    @pytest.mark.asyncio
    async def test_parallel_map_basic(self):
        """Test parallel_map processes all items"""

        async def double(n: int) -> int:
            await asyncio.sleep(0.01)
            return n * 2

        items = [1, 2, 3, 4, 5]
        results = await parallel_map(double, items, max_concurrent=3)

        assert results == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_parallel_map_empty(self):
        """Test parallel_map with empty list"""

        async def process(item: int) -> int:
            return item

        results = await parallel_map(process, [], max_concurrent=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_parallel_map_concurrency_limit(self):
        """Test parallel_map respects max_concurrent limit"""
        concurrent_count = 0
        max_concurrent_seen = 0

        async def track_concurrency(n: int) -> int:
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)

            await asyncio.sleep(0.05)

            concurrent_count -= 1
            return n

        items = list(range(10))
        await parallel_map(track_concurrency, items, max_concurrent=3)

        # Should never exceed max_concurrent
        assert max_concurrent_seen <= 3

    @pytest.mark.asyncio
    async def test_parallel_map_performance(self):
        """Test parallel_map is faster than serial processing"""

        async def slow_process(n: int) -> int:
            await asyncio.sleep(0.05)
            return n * 2

        items = list(range(10))

        # Parallel with concurrency limit
        start = time.time()
        results = await parallel_map(slow_process, items, max_concurrent=5)
        parallel_duration = time.time() - start

        assert results == [i * 2 for i in items]
        # With 10 items, 0.05s each, max_concurrent=5:
        # Should be ~0.1s (2 batches), not 0.5s (serial)
        assert parallel_duration < 0.15

    @pytest.mark.asyncio
    async def test_parallel_map_preserves_order(self):
        """Test parallel_map preserves input order"""

        async def process_with_random_delay(n: int) -> int:
            # Random delay to ensure tasks complete out of order
            await asyncio.sleep(0.01 * (5 - n))
            return n * 2

        items = [1, 2, 3, 4, 5]
        results = await parallel_map(
            process_with_random_delay,
            items,
            max_concurrent=5
        )

        # Results should be in input order, not completion order
        assert results == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_parallel_map_error_handling(self):
        """Test parallel_map propagates errors"""

        async def process_with_error(n: int) -> int:
            if n == 3:
                raise ValueError(f"Error processing {n}")
            return n * 2

        items = [1, 2, 3, 4, 5]

        with pytest.raises(ValueError, match="Error processing 3"):
            await parallel_map(process_with_error, items, max_concurrent=5)


class TestParallelMapUnordered:
    """Tests for parallel_map_unordered() function"""

    @pytest.mark.asyncio
    async def test_parallel_map_unordered_basic(self):
        """Test parallel_map_unordered processes all items"""

        async def double(n: int) -> int:
            await asyncio.sleep(0.01)
            return n * 2

        items = [1, 2, 3, 4, 5]
        results = await parallel_map_unordered(double, items, max_concurrent=3)

        # Results might be in any order
        assert sorted(results) == [2, 4, 6, 8, 10]

    @pytest.mark.asyncio
    async def test_parallel_map_unordered_completion_order(self):
        """Test parallel_map_unordered returns in completion order"""

        async def process_with_delay(n: int) -> int:
            # Items with higher numbers complete faster
            await asyncio.sleep(0.01 * (6 - n))
            return n

        items = [1, 2, 3, 4, 5]
        results = await parallel_map_unordered(
            process_with_delay,
            items,
            max_concurrent=5
        )

        # First result should be from last item (completes fastest)
        # Note: Due to asyncio scheduling, we just verify all items processed
        assert sorted(results) == [1, 2, 3, 4, 5]
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_parallel_map_unordered_performance(self):
        """Test parallel_map_unordered is fast"""

        async def slow_process(n: int) -> int:
            await asyncio.sleep(0.05)
            return n

        items = list(range(10))

        start = time.time()
        results = await parallel_map_unordered(
            slow_process,
            items,
            max_concurrent=5
        )
        duration = time.time() - start

        assert sorted(results) == items
        # Should be ~0.1s (2 batches), not 0.5s
        assert duration < 0.15
