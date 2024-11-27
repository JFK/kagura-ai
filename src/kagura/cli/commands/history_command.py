# cli/commands/history_command.py
from rich import box
from rich.table import Table

from .base import CommandHandler


class HistoryCommandHandler(CommandHandler):

    async def handle(self, args: str) -> None:
        messages = await self.message_history.get_messages()
        if not messages:
            self.console.print("[yellow]No message history available[/yellow]")
            return

        table = Table(title="Message History", box=box.ROUNDED)
        table.add_column("Role", style="cyan")
        table.add_column("Content", style="green")

        for msg in messages:
            table.add_row(
                msg["role"], self._truncate_text(msg["content"], max_width=80)
            )

        self.console.panel(table, border_style="blue")

    def _truncate_text(self, text: str, max_width: int) -> str:
        if len(text) <= max_width:
            return text
        return text[: max_width - 3] + "..."
