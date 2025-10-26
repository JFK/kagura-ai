"""Tests for advanced workflow decorators (chain, parallel, stateful)."""

import asyncio

import pytest
from pydantic import BaseModel

from kagura.core import workflow

# ===== @workflow.chain Tests =====


@pytest.mark.asyncio
async def test_workflow_chain_basic():
    """Test basic chain workflow execution."""

    @workflow.chain
    async def simple_chain(x: int) -> int:
        """Simple chain workflow"""
        await asyncio.sleep(0.01)  # Simulate async work
        return x * 2

    result = await simple_chain(5)
    assert result == 10


@pytest.mark.asyncio
async def test_workflow_chain_sequential():
    """Test chain workflow with sequential steps."""
    execution_order = []

    async def step1(x: int) -> int:
        await asyncio.sleep(0.01)
        execution_order.append("step1")
        return x + 1

    async def step2(x: int) -> int:
        await asyncio.sleep(0.01)
        execution_order.append("step2")
        return x * 2

    async def step3(x: int) -> str:
        await asyncio.sleep(0.01)
        execution_order.append("step3")
        return f"result: {x}"

    @workflow.chain
    async def pipeline(value: int) -> str:
        """Sequential pipeline"""
        v1 = await step1(value)
        v2 = await step2(v1)
        v3 = await step3(v2)
        return v3

    result = await pipeline(5)
    assert result == "result: 12"  # (5 + 1) * 2 = 12
    assert execution_order == ["step1", "step2", "step3"]


@pytest.mark.asyncio
async def test_workflow_chain_metadata():
    """Test chain workflow metadata attributes."""

    @workflow.chain
    async def my_chain(x: int) -> int:
        """My chain workflow docstring"""
        return x

    assert hasattr(my_chain, "_is_workflow_chain")
    assert my_chain._is_workflow_chain is True
    assert my_chain._workflow_name == "my_chain"
    assert "My chain workflow docstring" in my_chain._workflow_docstring


# ===== @workflow.parallel Tests =====


@pytest.mark.asyncio
async def test_workflow_parallel_basic():
    """Test basic parallel workflow execution."""

    @workflow.parallel
    async def simple_parallel(x: int) -> int:
        """Simple parallel workflow"""
        await asyncio.sleep(0.01)
        return x * 2

    result = await simple_parallel(5)
    assert result == 10


@pytest.mark.asyncio
async def test_workflow_parallel_concurrent():
    """Test parallel workflow with concurrent execution."""
    execution_times = []

    async def slow_task(delay: float, value: int) -> int:
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(delay)
        end = asyncio.get_event_loop().time()
        execution_times.append(end - start)
        return value * 2

    @workflow.parallel
    async def concurrent_workflow() -> dict[str, int]:
        """Concurrent workflow with asyncio.gather"""
        # Execute three tasks in parallel
        results = await asyncio.gather(
            slow_task(0.05, 1),
            slow_task(0.05, 2),
            slow_task(0.05, 3),
        )
        return {"task1": results[0], "task2": results[1], "task3": results[2]}

    result = await concurrent_workflow()

    assert result == {"task1": 2, "task2": 4, "task3": 6}
    # All tasks should run in parallel, total time should be ~0.05s, not 0.15s
    assert len(execution_times) == 3


@pytest.mark.asyncio
async def test_workflow_parallel_with_run_parallel():
    """Test parallel workflow with run_parallel helper."""

    async def task_a(x: int) -> int:
        await asyncio.sleep(0.01)
        return x + 1

    async def task_b(x: int) -> int:
        await asyncio.sleep(0.01)
        return x * 2

    async def task_c(x: int) -> int:
        await asyncio.sleep(0.01)
        return x**2

    @workflow.parallel
    async def parallel_with_helper(value: int) -> dict[str, int]:
        """Parallel workflow using run_parallel"""
        results = await workflow.run_parallel(
            a=task_a(value), b=task_b(value), c=task_c(value)
        )
        return results

    result = await parallel_with_helper(5)

    assert result == {"a": 6, "b": 10, "c": 25}


@pytest.mark.asyncio
async def test_workflow_parallel_metadata():
    """Test parallel workflow metadata attributes."""

    @workflow.parallel
    async def my_parallel(x: int) -> int:
        """My parallel workflow docstring"""
        return x

    assert hasattr(my_parallel, "_is_workflow_parallel")
    assert my_parallel._is_workflow_parallel is True
    assert my_parallel._workflow_name == "my_parallel"
    assert "My parallel workflow docstring" in my_parallel._workflow_docstring


# ===== @workflow.stateful Tests =====


class CounterState(BaseModel):
    """Simple counter state for testing."""

    count: int = 0
    history: list[int] = []


class ResearchState(BaseModel):
    """Research workflow state for testing."""

    topic: str
    keywords: list[str] = []
    search_results: list[str] = []
    summary: str = ""


@pytest.mark.asyncio
async def test_workflow_stateful_basic():
    """Test basic stateful workflow execution."""

    @workflow.stateful(state_class=CounterState)
    async def increment(state: CounterState) -> CounterState:
        """Increment counter"""
        state.count += 1
        state.history.append(state.count)
        return state

    initial_state = CounterState(count=0)
    result_state = await increment(initial_state)

    assert result_state.count == 1
    assert result_state.history == [1]


@pytest.mark.asyncio
async def test_workflow_stateful_multi_step():
    """Test stateful workflow with multiple steps."""

    async def extract_keywords(topic: str) -> list[str]:
        await asyncio.sleep(0.01)
        return topic.split()

    async def search(keywords: list[str]) -> list[str]:
        await asyncio.sleep(0.01)
        return [f"result for {kw}" for kw in keywords]

    async def summarize(results: list[str]) -> str:
        await asyncio.sleep(0.01)
        return f"Summary of {len(results)} results"

    @workflow.stateful(state_class=ResearchState)
    async def research_workflow(state: ResearchState) -> ResearchState:
        """Research workflow with state management"""
        # Step 1: Extract keywords
        state.keywords = await extract_keywords(state.topic)

        # Step 2: Search
        state.search_results = await search(state.keywords)

        # Step 3: Summarize
        state.summary = await summarize(state.search_results)

        return state

    initial_state = ResearchState(topic="AI safety")
    result_state = await research_workflow(initial_state)

    assert result_state.topic == "AI safety"
    assert result_state.keywords == ["AI", "safety"]
    assert len(result_state.search_results) == 2
    assert result_state.summary == "Summary of 2 results"


@pytest.mark.asyncio
async def test_workflow_stateful_validation():
    """Test stateful workflow validates input and output types."""

    @workflow.stateful(state_class=CounterState)
    async def increment(state: CounterState) -> CounterState:
        """Increment counter"""
        state.count += 1
        return state

    # Valid state
    valid_state = CounterState(count=0)
    result = await increment(valid_state)
    assert result.count == 1

    # Invalid state type
    with pytest.raises(TypeError, match="Expected state of type"):
        await increment("not a state")  # type: ignore


@pytest.mark.asyncio
async def test_workflow_stateful_return_validation():
    """Test stateful workflow validates return type."""

    @workflow.stateful(state_class=CounterState)
    async def bad_workflow(state: CounterState) -> CounterState:
        """Workflow that returns wrong type"""
        return "not a state"  # type: ignore

    state = CounterState(count=0)
    with pytest.raises(TypeError, match="Workflow must return"):
        await bad_workflow(state)


def test_workflow_stateful_requires_pydantic_model():
    """Test stateful decorator requires Pydantic BaseModel."""

    class NotAPydanticModel:
        pass

    with pytest.raises(TypeError, match="must be a Pydantic BaseModel"):
        workflow.stateful(state_class=NotAPydanticModel)  # type: ignore


@pytest.mark.asyncio
async def test_workflow_stateful_metadata():
    """Test stateful workflow metadata attributes."""

    @workflow.stateful(state_class=CounterState)
    async def my_stateful(state: CounterState) -> CounterState:
        """My stateful workflow docstring"""
        return state

    assert hasattr(my_stateful, "_is_workflow_stateful")
    assert my_stateful._is_workflow_stateful is True
    assert my_stateful._workflow_name == "my_stateful"
    assert "My stateful workflow docstring" in my_stateful._workflow_docstring
    assert my_stateful._workflow_state_class is CounterState


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_workflow_chain_with_parallel():
    """Test combining chain and parallel workflows."""

    async def parallel_search(query: str) -> list[str]:
        """Parallel search across multiple sources"""

        async def source_a(q: str) -> str:
            await asyncio.sleep(0.01)
            return f"A: {q}"

        async def source_b(q: str) -> str:
            await asyncio.sleep(0.01)
            return f"B: {q}"

        results = await asyncio.gather(source_a(query), source_b(query))
        return list(results)

    @workflow.chain
    async def search_and_aggregate(query: str) -> str:
        """Chain: search -> aggregate"""
        results = await parallel_search(query)
        return " | ".join(results)

    result = await search_and_aggregate("test")
    assert result == "A: test | B: test"


@pytest.mark.asyncio
async def test_workflow_stateful_with_parallel():
    """Test stateful workflow using parallel execution internally."""

    class MultiSourceState(BaseModel):
        query: str
        source_a_result: str = ""
        source_b_result: str = ""
        combined: str = ""

    async def fetch_a(query: str) -> str:
        await asyncio.sleep(0.01)
        return f"A: {query}"

    async def fetch_b(query: str) -> str:
        await asyncio.sleep(0.01)
        return f"B: {query}"

    @workflow.stateful(state_class=MultiSourceState)
    async def multi_source_workflow(state: MultiSourceState) -> MultiSourceState:
        """Stateful workflow with parallel fetching"""
        # Fetch from both sources in parallel
        results = await asyncio.gather(fetch_a(state.query), fetch_b(state.query))

        state.source_a_result = results[0]
        state.source_b_result = results[1]
        state.combined = f"{results[0]} | {results[1]}"

        return state

    initial = MultiSourceState(query="test")
    result = await multi_source_workflow(initial)

    assert result.source_a_result == "A: test"
    assert result.source_b_result == "B: test"
    assert result.combined == "A: test | B: test"


# ===== run_parallel Helper Tests =====


@pytest.mark.asyncio
async def test_run_parallel_helper():
    """Test run_parallel helper function."""

    async def task1() -> int:
        await asyncio.sleep(0.01)
        return 1

    async def task2() -> int:
        await asyncio.sleep(0.01)
        return 2

    async def task3() -> int:
        await asyncio.sleep(0.01)
        return 3

    results = await workflow.run_parallel(a=task1(), b=task2(), c=task3())

    assert results == {"a": 1, "b": 2, "c": 3}


@pytest.mark.asyncio
async def test_run_parallel_preserves_order():
    """Test run_parallel preserves task name-to-result mapping."""

    async def task(value: int) -> int:
        await asyncio.sleep(0.01)
        return value

    results = await workflow.run_parallel(z=task(26), a=task(1), m=task(13))

    assert results == {"z": 26, "a": 1, "m": 13}
