"""Rich console formatting helpers for CLI commands.

Provides reusable Rich components to ensure consistent formatting
across all Kagura CLI commands.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def create_console() -> Console:
    """Create standard Console instance for Kagura CLI.

    Returns:
        Console with Kagura defaults

    Example:
        >>> console = create_console()
        >>> console.print("Hello")
    """
    return Console()


def create_table(
    title: str | None = None,
    show_header: bool = True,
    show_lines: bool = False,
    **kwargs: Any,
) -> Table:
    """Create standard Table for Kagura CLI output.

    Args:
        title: Optional table title
        show_header: Show column headers (default: True)
        show_lines: Show row divider lines (default: False)
        **kwargs: Additional Table arguments

    Returns:
        Configured Table instance

    Example:
        >>> table = create_table(title="Projects")
        >>> table.add_column("Name")
        >>> table.add_column("Status")
        >>> table.add_row("kagura-ai", "active")
    """
    return Table(
        title=title,
        show_header=show_header,
        show_lines=show_lines,
        **kwargs,
    )


def create_success_panel(
    message: str,
    title: str = "Success",
    expand: bool = False,
) -> Panel:
    """Create success panel with green styling.

    Args:
        message: Success message (supports Rich markup)
        title: Panel title (default: "Success")
        expand: Expand to full width (default: False)

    Returns:
        Styled Panel for success messages

    Example:
        >>> panel = create_success_panel("Operation completed!")
        >>> console.print(panel)
    """
    return Panel(
        message,
        title=f"[bold]{title}[/]",
        style="green",
        expand=expand,
    )


def create_error_panel(
    message: str,
    title: str = "Error",
    expand: bool = False,
) -> Panel:
    """Create error panel with red styling.

    Args:
        message: Error message (supports Rich markup)
        title: Panel title (default: "Error")
        expand: Expand to full width (default: False)

    Returns:
        Styled Panel for error messages

    Example:
        >>> panel = create_error_panel("Connection failed")
        >>> console.print(panel)
    """
    return Panel(
        message,
        title=f"[bold]{title}[/]",
        style="red",
        expand=expand,
    )


def create_warning_panel(
    message: str,
    title: str = "Warning",
    expand: bool = False,
) -> Panel:
    """Create warning panel with yellow styling.

    Args:
        message: Warning message (supports Rich markup)
        title: Panel title (default: "Warning")
        expand: Expand to full width (default: False)

    Returns:
        Styled Panel for warning messages

    Example:
        >>> panel = create_warning_panel("Deprecated feature")
        >>> console.print(panel)
    """
    return Panel(
        message,
        title=f"[bold]{title}[/]",
        style="yellow",
        expand=expand,
    )


def create_info_panel(
    message: str,
    title: str = "Info",
    expand: bool = False,
) -> Panel:
    """Create info panel with blue styling.

    Args:
        message: Info message (supports Rich markup)
        title: Panel title (default: "Info")
        expand: Expand to full width (default: False)

    Returns:
        Styled Panel for informational messages

    Example:
        >>> panel = create_info_panel("System ready")
        >>> console.print(panel)
    """
    return Panel(
        message,
        title=f"[bold]{title}[/]",
        style="blue",
        expand=expand,
    )
