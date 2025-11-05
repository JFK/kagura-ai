"""Progress bar and spinner utilities for CLI commands.

Provides reusable progress indicators to ensure consistent
visual feedback across all Kagura CLI commands.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


def create_spinner_progress(console: Console | None = None) -> Progress:
    """Create standard spinner progress indicator.

    Args:
        console: Optional console instance (creates new if None)

    Returns:
        Progress with spinner and text column

    Example:
        >>> with create_spinner_progress() as progress:
        >>>     task = progress.add_task("Processing...", total=None)
        >>>     # Do work
        >>>     progress.update(task, description="Complete!")
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def create_progress_bar(
    *columns: Any,
    console: Console | None = None,
) -> Progress:
    """Create progress bar with custom columns.

    Args:
        *columns: Rich progress columns to include
        console: Optional console instance

    Returns:
        Progress instance with specified columns

    Example:
        >>> from rich.progress import BarColumn, TaskProgressColumn
        >>> progress = create_progress_bar(
        >>>     SpinnerColumn(),
        >>>     TextColumn("[progress.description]{task.description}"),
        >>>     BarColumn(),
        >>>     TaskProgressColumn(),
        >>> )
    """
    return Progress(*columns, console=console)
