"""Tests for testing utilities."""

import time

import pytest

from kagura.testing.utils import Timer


def test_timer_initialization():
    """Test Timer initialization."""
    timer = Timer()

    assert timer.start_time is None
    assert timer.end_time is None
    assert timer.duration == 0.0


def test_timer_context_manager():
    """Test Timer as context manager."""
    with Timer() as timer:
        time.sleep(0.1)  # Sleep for 100ms

    # Duration should be approximately 0.1s
    assert timer.start_time is not None
    assert timer.end_time is not None
    assert timer.duration >= 0.1
    assert timer.duration < 0.2  # Should not be too long


def test_timer_multiple_uses():
    """Test Timer can be used multiple times."""
    timer1 = Timer()
    with timer1:
        time.sleep(0.05)

    timer2 = Timer()
    with timer2:
        time.sleep(0.1)

    # First timer should be shorter
    assert timer1.duration < timer2.duration
    assert timer1.duration >= 0.05
    assert timer2.duration >= 0.1


def test_timer_precision():
    """Test Timer has reasonable precision."""
    with Timer() as timer:
        time.sleep(0.05)

    # Should be close to 0.05s (within 20ms tolerance)
    assert 0.04 <= timer.duration <= 0.07
