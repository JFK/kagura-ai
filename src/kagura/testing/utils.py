"""Testing utilities and helpers."""

import time
from typing import Optional


class Timer:
    """Context manager to measure execution time.

    Example:
        >>> with Timer() as timer:
        ...     # Some operation
        ...     pass
        >>> print(f"Duration: {timer.duration:.2f}s")
    """

    def __init__(self) -> None:
        """Initialize timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: float = 0.0

    def __enter__(self) -> "Timer":
        """Start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, *args: object) -> None:
        """Stop timer and calculate duration."""
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
