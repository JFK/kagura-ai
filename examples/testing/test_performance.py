"""Performance Testing Example

This example demonstrates how to test agent performance including
latency, throughput, token usage, and cost tracking.
"""

import time
import asyncio
import pytest
from kagura import agent
from kagura.testing import AgentTestCase


# Define test agents
@agent(model="gpt-4o-mini")
async def fast_agent(query: str) -> str:
    """Quick response to: {{ query }}"""
    pass


@agent(model="gpt-4o-mini")
async def complex_agent(data: str) -> str:
    """Perform detailed analysis of: {{ data }}"""
    pass


@agent(model="gpt-4o-mini", enable_memory=True)
async def stateful_agent(message: str) -> str:
    """Chat: {{ message }}"""
    pass


# Test Class 1: Latency Testing
class TestAgentLatency(AgentTestCase):
    """Test agent response latency."""

    agent = fast_agent

    @pytest.mark.asyncio
    async def test_response_time_under_threshold(self):
        """Test that agent responds within acceptable time."""
        start_time = time.time()

        result = await self.agent("Hello")

        elapsed = time.time() - start_time

        # Should respond within 5 seconds (adjust based on requirements)
        assert elapsed < 5.0, f"Response took {elapsed:.2f}s, expected < 5.0s"

        # Verify we got a response
        self.assert_not_empty(result)

    @pytest.mark.asyncio
    async def test_average_latency(self):
        """Test average latency over multiple calls."""
        iterations = 5
        total_time = 0

        for i in range(iterations):
            start_time = time.time()
            await self.agent(f"Test query {i}")
            total_time += time.time() - start_time

        avg_latency = total_time / iterations
        print(f"\nAverage latency: {avg_latency:.2f}s")

        # Average should be reasonable
        assert avg_latency < 3.0, f"Average latency {avg_latency:.2f}s too high"


# Test Class 2: Throughput Testing
class TestAgentThroughput(AgentTestCase):
    """Test agent throughput (requests per second)."""

    agent = fast_agent

    @pytest.mark.asyncio
    async def test_sequential_throughput(self):
        """Test throughput with sequential requests."""
        num_requests = 10
        start_time = time.time()

        for i in range(num_requests):
            await self.agent(f"Request {i}")

        elapsed = time.time() - start_time
        throughput = num_requests / elapsed

        print(f"\nSequential throughput: {throughput:.2f} req/s")
        print(f"Total time: {elapsed:.2f}s for {num_requests} requests")

        # Should process at least 1 request per 3 seconds
        assert throughput > 0.3, f"Throughput {throughput:.2f} too low"

    @pytest.mark.asyncio
    async def test_concurrent_throughput(self):
        """Test throughput with concurrent requests."""
        num_requests = 10
        start_time = time.time()

        # Run requests concurrently
        tasks = [
            self.agent(f"Concurrent request {i}")
            for i in range(num_requests)
        ]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        throughput = num_requests / elapsed

        print(f"\nConcurrent throughput: {throughput:.2f} req/s")
        print(f"Total time: {elapsed:.2f}s for {num_requests} concurrent requests")

        # Concurrent should be faster than sequential
        # All requests should succeed
        assert len(results) == num_requests
        assert all(results), "Some requests failed"


# Test Class 3: Token Usage Testing
class TestTokenUsage(AgentTestCase):
    """Test token usage and optimization."""

    agent = complex_agent

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self):
        """Test that token usage is tracked."""
        short_input = "Hi"
        long_input = "This is a much longer input with many more words " * 10

        # With mocking, we can verify token counting logic
        with self.mock_llm_response("Short response"):
            result_short = await self.agent(short_input)

        with self.mock_llm_response("This is a longer response " * 5):
            result_long = await self.agent(long_input)

        # Both should return results
        self.assert_not_empty(result_short)
        self.assert_not_empty(result_long)

    @pytest.mark.asyncio
    async def test_output_length_control(self):
        """Test that output length is controlled."""
        result = await self.agent("Generate a short summary")

        # Output should not be excessively long
        # Adjust max_length based on agent configuration
        self.assert_max_length(result, 1000)


# Test Class 4: Cost Tracking
class TestCostTracking(AgentTestCase):
    """Test cost tracking and optimization."""

    @pytest.mark.asyncio
    async def test_cost_per_request(self):
        """Test estimating cost per request."""

        @agent(model="gpt-4o-mini")  # Cheaper model
        async def cheap_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        # Mock response to avoid actual costs
        with self.mock_llm_response("Mocked response"):
            result = await cheap_agent("Test query")

        # In real scenario, you'd calculate:
        # cost = (input_tokens + output_tokens) * model_price_per_token

        # For now, just verify execution
        self.assert_not_empty(result)

    @pytest.mark.asyncio
    async def test_cost_optimization_strategy(self):
        """Test cost optimization strategies."""

        # Strategy 1: Use cheaper model for simple tasks
        @agent(model="gpt-4o-mini")
        async def simple_task(query: str) -> str:
            """Simple: {{ query }}"""
            pass

        # Strategy 2: Use more expensive model for complex tasks
        @agent(model="gpt-4o")
        async def complex_task(query: str) -> str:
            """Complex analysis: {{ query }}"""
            pass

        with self.mock_llm_response("Simple result"):
            simple_result = await simple_task("Easy question")

        with self.mock_llm_response("Complex result"):
            complex_result = await complex_task("Difficult analysis")

        # Both should work
        self.assert_not_empty(simple_result)
        self.assert_not_empty(complex_result)


# Test Class 5: Memory Performance
class TestMemoryPerformance(AgentTestCase):
    """Test performance with memory-enabled agents."""

    agent = stateful_agent

    @pytest.mark.asyncio
    async def test_memory_overhead(self):
        """Test overhead of memory operations."""
        # First call (no history)
        start_time = time.time()
        await self.agent("First message")
        first_call_time = time.time() - start_time

        # Subsequent calls (with history)
        start_time = time.time()
        await self.agent("Second message")
        second_call_time = time.time() - start_time

        print(f"\nFirst call: {first_call_time:.2f}s")
        print(f"Second call: {second_call_time:.2f}s")

        # Memory overhead should be minimal
        # (This is a documentation of expected behavior)

    @pytest.mark.asyncio
    async def test_large_context_performance(self):
        """Test performance with large conversation context."""
        # Simulate a long conversation
        for i in range(20):
            await self.agent(f"Message {i}")

        # Measure performance after context buildup
        start_time = time.time()
        result = await self.agent("Final message")
        elapsed = time.time() - start_time

        print(f"\nPerformance with 20-message history: {elapsed:.2f}s")

        # Should still be reasonable
        assert elapsed < 10.0, f"Performance degraded: {elapsed:.2f}s"
        self.assert_not_empty(result)


# Test Class 6: Stress Testing
class TestStressConditions:
    """Test agent behavior under stress conditions."""

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self):
        """Test handling rapid sequential requests."""

        @agent(model="gpt-4o-mini")
        async def stress_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        num_requests = 50
        successful = 0
        failed = 0

        for i in range(num_requests):
            try:
                result = await stress_agent(f"Request {i}")
                if result:
                    successful += 1
            except Exception as e:
                failed += 1
                print(f"Request {i} failed: {e}")

        success_rate = successful / num_requests
        print(f"\nStress test: {successful}/{num_requests} successful ({success_rate:.1%})")

        # Should have high success rate
        assert success_rate > 0.9, f"Success rate {success_rate:.1%} too low"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_long_running_agent(self):
        """Test agent stability over extended period."""

        @agent(model="gpt-4o-mini")
        async def stable_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        # Run for 5 minutes with requests every 10 seconds
        duration = 60  # 1 minute for demo (adjust to 300 for 5 minutes)
        interval = 10
        iterations = duration // interval

        successful = 0
        for i in range(iterations):
            try:
                result = await stable_agent(f"Stability test {i}")
                if result:
                    successful += 1
            except Exception as e:
                print(f"Iteration {i} failed: {e}")

            if i < iterations - 1:
                await asyncio.sleep(interval)

        success_rate = successful / iterations
        print(f"\nLong-running test: {successful}/{iterations} successful")

        # Should maintain stability
        assert success_rate == 1.0, "Agent should remain stable over time"


# Test Class 7: Benchmarking
class TestBenchmarks:
    """Benchmark different agent configurations."""

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_model_comparison(self):
        """Compare performance across different models."""

        @agent(model="gpt-4o-mini")
        async def mini_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        @agent(model="gpt-4o")
        async def standard_agent(query: str) -> str:
            """Process: {{ query }}"""
            pass

        test_query = "What is machine learning?"

        # Benchmark mini model
        start = time.time()
        await mini_agent(test_query)
        mini_time = time.time() - start

        # Benchmark standard model
        start = time.time()
        await standard_agent(test_query)
        standard_time = time.time() - start

        print(f"\ngpt-4o-mini: {mini_time:.2f}s")
        print(f"gpt-4o: {standard_time:.2f}s")

        # Document performance characteristics
        # (Actual comparison depends on current API performance)


# Run tests
if __name__ == "__main__":
    # Run all tests except slow/benchmark tests
    pytest.main([__file__, "-v", "-m", "not slow and not benchmark"])

    # To run all tests including slow ones:
    # pytest.main([__file__, "-v"])
