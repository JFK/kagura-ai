"""
Enhanced display utilities for Kagura Chat with rich markdown and syntax highlighting
"""

import re
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax


class EnhancedDisplay:
    """
    Enhanced display manager for chat responses.

    Features:
    - Automatic syntax highlighting for code blocks
    - Rich markdown rendering
    - Clickable links (terminal support required)
    - Pretty panels for structured content
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize enhanced display.

        Args:
            console: Rich Console instance (creates new if None)
        """
        self.console = console or Console()

    def display_response(self, response: str) -> None:
        """
        Display AI response with enhanced formatting.

        Args:
            response: Response text to display
        """
        # Check if response contains code blocks
        if "```" in response:
            self._display_with_code_blocks(response)
        else:
            # Regular markdown
            self.console.print(Markdown(response))

    def _display_with_code_blocks(self, response: str) -> None:
        """
        Display response with syntax-highlighted code blocks.

        Args:
            response: Response text with code blocks
        """
        # Split by code block markers
        parts = re.split(r"```(\w+)?\n", response)

        i = 0
        while i < len(parts):
            part = parts[i]

            # Regular text
            if i % 2 == 0:
                if part.strip():
                    self.console.print(Markdown(part))
                i += 1
            # Code block
            else:
                # Language from split capture group
                language = part if part else "python"
                i += 1

                # Get code content
                if i < len(parts):
                    code = parts[i].rstrip("```").rstrip()
                    i += 1

                    # Display with syntax highlighting
                    syntax = Syntax(
                        code,
                        language,
                        theme="monokai",
                        line_numbers=True,
                        word_wrap=True,
                    )
                    self.console.print(
                        Panel(syntax, title=f"Code ({language})", border_style="blue")
                    )

    def display_panel(
        self,
        content: str | Any,
        title: str = "",
        border_style: str = "green",
        markdown: bool = False,
    ) -> None:
        """
        Display content in a panel.

        Args:
            content: Content to display
            title: Panel title
            border_style: Border color/style
            markdown: Whether to render content as markdown
        """
        if markdown and isinstance(content, str):
            content = Markdown(content)

        self.console.print(Panel(content, title=title, border_style=border_style))

    def display_error(self, message: str) -> None:
        """
        Display error message.

        Args:
            message: Error message
        """
        self.console.print(f"[red]✗ {message}[/]")

    def display_success(self, message: str) -> None:
        """
        Display success message.

        Args:
            message: Success message
        """
        self.console.print(f"[green]✓ {message}[/]")

    def display_info(self, message: str) -> None:
        """
        Display info message.

        Args:
            message: Info message
        """
        self.console.print(f"[cyan]ℹ {message}[/]")

    def display_warning(self, message: str) -> None:
        """
        Display warning message.

        Args:
            message: Warning message
        """
        self.console.print(f"[yellow]⚠ {message}[/]")
