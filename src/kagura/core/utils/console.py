import asyncio
from typing import Any, Callable, Dict, List, Union

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from pydantic import BaseModel
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (BarColumn, Progress, SpinnerColumn, TextColumn,
                           TimeElapsedColumn)
from rich.prompt import Prompt
from rich.table import Table


class KaguraConsole:
    """Console class for Kagura"""

    def __init__(
        self,
        console: Console = None,
        qiuet: bool = False,
        width: int = 120,
    ) -> None:
        if console is None:
            self._console = Console(quiet=qiuet, width=width)
        else:
            self._console = console

        self.input_history = []
        self.history_position = 0

    @property
    def console(self) -> Console:
        return self._console

    @property
    def progress(self) -> Progress:
        if not hasattr(self, "_progress"):
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            )
        return self._progress

    def print(self, message: Any = "\n"):
        self.console.print(message)

    def panel(self, message: Any, title: str = "", border_style: str = "blue"):
        return self.print(Panel(message, title=title, border_style=border_style))

    def input(self, message: str) -> str:
        prompt = Prompt()
        return prompt.ask(message)

    async def input_async(self, message: str) -> str:
        prompt = PromptSession()
        return await prompt.prompt_async(message)

    async def multiline_input(self, prompt_message: str = "") -> str:
        if prompt_message:
            await self.display_typing(prompt_message)

        bindings = KeyBindings()

        @bindings.add("c-m")  # Enter
        def _(event):
            buffer = event.app.current_buffer
            if buffer.document.text.endswith("\n"):
                event.app.exit(result=buffer.document.text)
            else:
                buffer.insert_text("\n")

        @bindings.add("c-p")  # Previous history (Ctrl+P)
        def _(event):
            if self.input_history and self.history_position < len(self.input_history):
                self.history_position += 1
                event.app.current_buffer.text = self.input_history[
                    -self.history_position
                ]

        @bindings.add("c-n")  # Next history (Ctrl+N)
        def _(event):
            if self.history_position > 1:
                self.history_position -= 1
                event.app.current_buffer.text = self.input_history[
                    -self.history_position
                ]
            elif self.history_position == 1:
                self.history_position = 0
                event.app.current_buffer.text = ""

        session = PromptSession(" > ", key_bindings=bindings)
        lines = []

        try:
            result = await session.prompt_async(multiline=True)
            lines.append(result)

            # Remove trailing empty lines
            while lines and not lines[-1].strip():
                lines.pop()

            final_input = "\n".join(lines)
            if final_input.strip():  # Only add non-empty inputs to history
                self.input_history.append(final_input)
                self.history_position = 0  # Reset position after new input

            return final_input

        except KeyboardInterrupt:
            return "/exit"
        except EOFError:
            return "/exit"

    async def display_spinner_with_task(
        self, message: str, async_task: Callable
    ) -> Any:
        """This function will display a spinner with a message and run the async task"""

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(message, total=None)

            result = await async_task

            progress.update(task, completed=True)
            progress.remove_task(task)

            return result

    async def astream_display_typing(
        self,
        async_task: Callable,
        **kwargs,
    ) -> str:
        displayed_text = ""
        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold blue]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Loading...", total=None)
            progress.start_task(task)
            async for char in async_task(**kwargs):
                displayed_text += char
                update_text = f"[bold green]🤖 {displayed_text}[/bold green]"
                progress.update(task, description=update_text)
            progress.update(task, visible=False)
            self.print(update_text)
            progress.stop_task(task)
        return displayed_text

    async def display_typing_with_panel(
        self,
        text: str,
        panel_title: str = "",
        text_color: str = "green",
        border_style: str = "blue",
        speed: float = 0.012,
        refresh_per_second: int = 10,
    ):
        displayed_text = ""
        with Live(
            Panel(displayed_text, title=panel_title, border_style=border_style),
            console=self.console,
            refresh_per_second=refresh_per_second,
        ) as live:
            for char in text:
                displayed_text += char
                update_text = f"[bold {text_color}]{displayed_text}[/bold {text_color}]"
                live.update(
                    Panel(update_text, title=panel_title, border_style=border_style)
                )
                if speed > 0.0:
                    await asyncio.sleep(speed)

    async def display_typing(
        self,
        text: str,
        panel_title: str = "",
        text_color: str = "green",
        border_style: str = "blue",
        speed: float = 0.012,
        refresh_per_second: int = 10,
    ):
        displayed_text = ""
        with Live(
            displayed_text,
            console=self.console,
            refresh_per_second=refresh_per_second,
        ) as live:
            for char in text:
                displayed_text += char
                update_text = f"[bold {text_color}]{displayed_text}[/bold {text_color}]"
                live.update(update_text)
                if speed > 0.0:
                    await asyncio.sleep(speed)

    def _print_single_table(
        self,
        items: Union[List[BaseModel], List[Dict]],
        title: str,
        max_width: int,
        key: str = None,
    ):
        table = Table(title=title, box=box.ROUNDED)

        first_item = items[0]

        if isinstance(first_item, BaseModel):
            fields = first_item.__fields__.keys()
        elif isinstance(first_item, dict):
            fields = first_item.keys()
        else:
            # when key is provided, use it as column name
            column_name = key if key else "Value"
            table.add_column(column_name, style="cyan")
            for item in items:
                table.add_row(self._truncate_text(str(item), max_width))
            self.panel(table)
            return

        # Add columns for dict or BaseModel
        for field in fields:
            table.add_column(str(field), style="cyan")

        # Add rows with truncated text
        for item in items:
            if isinstance(item, BaseModel):
                row = [
                    self._truncate_text(str(getattr(item, field)), max_width)
                    for field in fields
                ]
            elif isinstance(item, dict):
                row = [
                    self._truncate_text(str(item.get(field, "")), max_width)
                    for field in fields
                ]
            else:
                row = [self._truncate_text(str(item), max_width)]
            table.add_row(*row)

        self.panel(table)

    def print_data_table(
        self,
        data: Union[List[BaseModel], List[Dict], Dict],
        title: str = "Data Table",
        max_width: int = 50,
    ):
        """
        Prints data in a rich table format with truncated text.

        Args:
            data: List of BaseModel instances, list of dictionaries, or dictionary containing lists
            title: Title for the table
            max_width: Maximum width of text in columns before truncation
        """
        if isinstance(data, dict):
            # Just a simple dictionary
            if not any(isinstance(v, (list, dict, BaseModel)) for v in data.values()):
                table = Table(title=title, box=box.ROUNDED)
                table.add_column("Key", style="cyan")
                table.add_column("Value", style="green")

                for key, value in data.items():
                    if (
                        key == "ERROR_MESSAGE" and value is not None
                    ):  # this is present in case of error in core.models.py
                        self.log_error(value)
                        return
                    table.add_row(
                        str(key),
                        self._truncate_text(str(value), max_width),
                    )
                self.panel(table)
                return

            # Nested dictionary or list of dictionaries
            for key, items in data.items():
                if isinstance(items, list):
                    if items and not isinstance(items[0], str):
                        self._print_single_table(items, title, max_width, key)
                    else:
                        table = Table(title=title, box=box.ROUNDED)
                        table.add_column(key, style="cyan")
                        for item in items:
                            table.add_row(self._truncate_text(str(item), max_width))
                        self.panel(table)
                    self.print()
                elif isinstance(items, (dict, BaseModel)):
                    # Nested dictionary is also displayed in Key-Value format
                    table = Table(title=f"{title} - {key}", box=box.ROUNDED)
                    table.add_column("Key", style="cyan")
                    table.add_column("Value", style="green")

                    if isinstance(items, dict):
                        for k, v in items.items():
                            table.add_row(
                                str(k), self._truncate_text(str(v), max_width)
                            )
                    else:  # BaseModel
                        for k in items.__fields__.keys():
                            v = getattr(items, k)
                            table.add_row(
                                str(k), self._truncate_text(str(v), max_width)
                            )

                    self.panel(table)
                    self.print()

        # When list of dictionaries, display each dictionary in Key-Value format
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                for i, item in enumerate(data, 1):
                    table = Table(title=f"{title} {i}", box=box.ROUNDED)
                    table.add_column("Key", style="cyan")
                    table.add_column("Value", style="green")

                    for key, value in item.items():
                        table.add_row(
                            str(key), self._truncate_text(str(value), max_width)
                        )

                    self.panel(table)
                    self.print()
            elif data and not isinstance(data[0], str):
                self._print_single_table(data, title, max_width)
            else:
                table = Table(title=title, box=box.ROUNDED)
                table.add_column("Value", style="cyan")
                for item in data:
                    table.add_row(self._truncate_text(str(item), max_width))
                self.panel(table)

    def _truncate_text(self, text: str, max_width: int) -> str:
        """Truncate text to the specified length and add ... if necessary"""
        text = str(text)
        if len(text) <= max_width:
            return text
        return text[: max_width - 3] + "..."

    def log_error(self, message: str):
        """エラーメッセージを表示"""
        self.print(f"[bold red]{message}[/bold red]")
