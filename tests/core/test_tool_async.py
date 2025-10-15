"""
Tests for @tool decorator with async functions
"""

import pytest

from kagura import tool


@tool
async def async_adder(a: int, b: int) -> int:
    """Add two numbers asynchronously"""
    return a + b


@tool
def sync_multiplier(a: int, b: int) -> int:
    """Multiply two numbers synchronously"""
    return a * b


@pytest.mark.asyncio
async def test_async_tool_basic() -> None:
    """Test async tool basic functionality"""
    result = await async_adder(2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_async_tool_with_kwargs() -> None:
    """Test async tool with keyword arguments"""
    result = await async_adder(a=10, b=20)
    assert result == 30


def test_sync_tool_basic() -> None:
    """Test sync tool basic functionality"""
    result = sync_multiplier(3, 4)
    assert result == 12


def test_sync_tool_with_kwargs() -> None:
    """Test sync tool with keyword arguments"""
    result = sync_multiplier(a=5, b=6)
    assert result == 30


@pytest.mark.asyncio
async def test_async_tool_is_coroutine_function() -> None:
    """Test that async tool wrapper is detected as coroutine function"""
    import inspect

    assert inspect.iscoroutinefunction(async_adder)


def test_sync_tool_is_not_coroutine_function() -> None:
    """Test that sync tool wrapper is not detected as coroutine function"""
    import inspect

    assert not inspect.iscoroutinefunction(sync_multiplier)


@pytest.mark.asyncio
async def test_async_tool_invalid_args() -> None:
    """Test async tool with invalid arguments"""
    with pytest.raises(TypeError, match="invalid arguments"):
        await async_adder(1)  # type: ignore  # Missing required argument


def test_sync_tool_invalid_args() -> None:
    """Test sync tool with invalid arguments"""
    with pytest.raises(TypeError, match="invalid arguments"):
        sync_multiplier(1)  # type: ignore  # Missing required argument
