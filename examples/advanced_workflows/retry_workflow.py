"""Retry Workflow Example

This example demonstrates retry logic, error handling, and fallback
strategies in workflows for robust agent execution.
"""

import asyncio
import random
from kagura import agent, workflow


# Define agents (some may simulate failures)
@agent(model="gpt-4o-mini")
async def unreliable_translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}"""
    # Simulate occasional failures
    if random.random() < 0.3:  # 30% failure rate
        raise Exception("Translation API timeout")
    pass


@agent(model="gpt-4o-mini")
async def reliable_translator(text: str, target_lang: str) -> str:
    """Translate "{{ text }}" to {{ target_lang }}"""
    pass


@agent(model="gpt-4o-mini")
async def summarizer(text: str) -> str:
    """Summarize: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def sentiment_analyzer(text: str) -> str:
    """Analyze sentiment: {{ text }}"""
    pass


async def main():
    """Demonstrate retry workflows."""
    print("=== Retry Workflow Examples ===\n")

    # Example 1: Basic retry logic
    print("1. Basic Retry Logic")
    print("-" * 50)

    @workflow
    async def retry_workflow(text: str, target_lang: str, max_retries: int = 3) -> str:
        """Workflow with retry logic."""
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries}")
                result = await unreliable_translator(text, target_lang)
                print(f"  ✓ Success on attempt {attempt + 1}")
                return result
            except Exception as e:
                print(f"  ✗ Failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts")
                await asyncio.sleep(1)  # Wait before retry

    try:
        result = await retry_workflow("Hello", "French", max_retries=5)
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Final failure: {e}\n")

    # Example 2: Exponential backoff
    print("2. Exponential Backoff")
    print("-" * 50)

    @workflow
    async def exponential_backoff_workflow(
        text: str,
        target_lang: str,
        max_retries: int = 3
    ) -> str:
        """Retry with exponential backoff."""
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries}")
                result = await unreliable_translator(text, target_lang)
                print(f"  ✓ Success")
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Failed after {max_retries} attempts")

                # Exponential backoff: 1s, 2s, 4s, 8s...
                wait_time = 2 ** attempt
                print(f"  ✗ Failed, waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)

    try:
        result = await exponential_backoff_workflow("Hello", "French")
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Final failure: {e}\n")

    # Example 3: Retry with fallback
    print("3. Retry with Fallback Agent")
    print("-" * 50)

    @workflow
    async def retry_with_fallback(text: str, target_lang: str) -> str:
        """Try primary agent, fallback to reliable agent."""
        max_retries = 2

        # Try unreliable agent first
        for attempt in range(max_retries):
            try:
                print(f"  Primary agent attempt {attempt + 1}/{max_retries}")
                result = await unreliable_translator(text, target_lang)
                print(f"  ✓ Primary agent succeeded")
                return result
            except Exception as e:
                print(f"  ✗ Primary failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)

        # Fallback to reliable agent
        print(f"  → Falling back to reliable agent")
        result = await reliable_translator(text, target_lang)
        print(f"  ✓ Fallback succeeded")
        return result

    result = await retry_with_fallback("Hello", "French")
    print(f"Result: {result}\n")

    # Example 4: Partial retry
    print("4. Partial Retry (Retry Only Failed Steps)")
    print("-" * 50)

    @workflow
    async def partial_retry_workflow(text: str) -> dict:
        """Retry only failed steps."""
        results = {}

        # Try all analyses
        tasks = {
            "sentiment": sentiment_analyzer,
            "summary": summarizer,
            "translation": lambda: unreliable_translator(text, "French")
        }

        for name, task_func in tasks.items():
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if name == "translation":
                        result = await task_func()
                    else:
                        result = await task_func(text)

                    results[name] = result
                    print(f"  ✓ {name} succeeded")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        results[name] = f"Failed: {str(e)}"
                        print(f"  ✗ {name} failed after {max_retries} attempts")
                    else:
                        print(f"  ✗ {name} attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(1)

        return results

    results = await partial_retry_workflow("Python is great")
    print("\nResults:")
    for key, value in results.items():
        print(f"  {key}: {value}")

    print()

    # Example 5: Timeout with retry
    print("5. Timeout with Retry")
    print("-" * 50)

    @workflow
    async def timeout_retry_workflow(
        text: str,
        target_lang: str,
        timeout: float = 5.0,
        max_retries: int = 3
    ) -> str:
        """Retry with timeout per attempt."""
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries} (timeout={timeout}s)")
                result = await asyncio.wait_for(
                    unreliable_translator(text, target_lang),
                    timeout=timeout
                )
                print(f"  ✓ Success")
                return result
            except asyncio.TimeoutError:
                print(f"  ✗ Timeout")
                if attempt == max_retries - 1:
                    raise Exception("Exceeded timeout retries")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                if attempt == max_retries - 1:
                    raise
            await asyncio.sleep(1)

    try:
        result = await timeout_retry_workflow("Hello", "French", timeout=10.0)
        print(f"Result: {result}\n")
    except Exception as e:
        print(f"Failed: {e}\n")

    # Example 6: Circuit breaker pattern
    print("6. Circuit Breaker Pattern")
    print("-" * 50)

    class CircuitBreaker:
        def __init__(self, failure_threshold: int = 3, timeout: float = 60.0):
            self.failure_count = 0
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            self.last_failure_time = None
            self.state = "closed"  # closed, open, half-open

        def call(self):
            if self.state == "open":
                # Check if timeout has passed
                if self.last_failure_time and \
                   (asyncio.get_event_loop().time() - self.last_failure_time) > self.timeout:
                    self.state = "half-open"
                    print("  Circuit breaker: half-open (testing)")
                else:
                    raise Exception("Circuit breaker is open")

        def success(self):
            self.failure_count = 0
            self.state = "closed"
            print("  Circuit breaker: closed (working)")

        def failure(self):
            self.failure_count += 1
            self.last_failure_time = asyncio.get_event_loop().time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                print(f"  Circuit breaker: open (too many failures)")

    breaker = CircuitBreaker(failure_threshold=2)

    @workflow
    async def circuit_breaker_workflow(text: str, target_lang: str) -> str:
        """Use circuit breaker to prevent cascading failures."""
        try:
            breaker.call()  # Check circuit state

            result = await unreliable_translator(text, target_lang)
            breaker.success()
            return result

        except Exception as e:
            breaker.failure()
            raise

    # Try multiple times to trigger circuit breaker
    for i in range(5):
        try:
            result = await circuit_breaker_workflow(f"Test {i}", "French")
            print(f"  Request {i+1}: Success")
        except Exception as e:
            print(f"  Request {i+1}: Failed - {str(e)}")

    print()

    # Example 7: Graceful degradation
    print("7. Graceful Degradation")
    print("-" * 50)

    @workflow
    async def graceful_degradation(text: str) -> dict:
        """Provide partial results on failures."""
        results = {
            "status": "partial",
            "sentiment": None,
            "summary": None,
            "translation": None
        }

        # Try each analysis, continue on failure
        try:
            results["sentiment"] = await sentiment_analyzer(text)
        except Exception as e:
            print(f"  Sentiment analysis failed: {e}")

        try:
            results["summary"] = await summarizer(text)
        except Exception as e:
            print(f"  Summarization failed: {e}")

        try:
            results["translation"] = await unreliable_translator(text, "French")
        except Exception as e:
            print(f"  Translation failed: {e}")

        # Check if we got any results
        if all(v is None for k, v in results.items() if k != "status"):
            results["status"] = "failed"
        elif all(v is not None for k, v in results.items() if k != "status"):
            results["status"] = "complete"

        return results

    results = await graceful_degradation("Python is awesome")
    print(f"\nGraceful degradation results (status: {results['status']}):")
    for key, value in results.items():
        if key != "status":
            status = "✓" if value else "✗"
            print(f"  {status} {key}: {value or 'N/A'}")

    print()

    # Example 8: Retry budget
    print("8. Retry Budget")
    print("-" * 50)

    @workflow
    async def retry_budget_workflow(texts: list[str], retry_budget: int = 5) -> list:
        """Limit total retries across multiple operations."""
        results = []
        retries_used = 0

        for i, text in enumerate(texts):
            success = False
            local_retries = 0
            max_local_retries = min(3, retry_budget - retries_used)

            for attempt in range(max_local_retries):
                try:
                    result = await unreliable_translator(text, "French")
                    results.append(result)
                    success = True
                    break
                except Exception:
                    local_retries += 1
                    retries_used += 1

            if not success:
                results.append(f"Failed: {text}")
                print(f"  Text {i+1}: Failed (retry budget exhausted)")
            else:
                print(f"  Text {i+1}: Success (used {local_retries} retries)")

        print(f"\nTotal retries used: {retries_used}/{retry_budget}")
        return results

    texts = ["Hello", "Goodbye", "Thank you", "Good morning"]
    results = await retry_budget_workflow(texts, retry_budget=6)

    print()


async def best_practices():
    """Demonstrate retry best practices."""
    print("\n" + "=" * 60)
    print("=== Retry Best Practices ===\n")

    print("1. Always set maximum retry attempts")
    print("2. Use exponential backoff for rate limits")
    print("3. Implement fallback strategies")
    print("4. Add timeouts to prevent hanging")
    print("5. Log retry attempts for debugging")
    print("6. Use circuit breakers for cascading failures")
    print("7. Provide graceful degradation when possible")
    print("8. Monitor retry rates and adjust strategies")
    print()


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Show best practices
    asyncio.run(best_practices())

    print("=" * 60)
    print("Retry workflow examples complete! 🎉")
