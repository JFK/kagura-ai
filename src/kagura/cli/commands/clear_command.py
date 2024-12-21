# cli/commands/clear_command.py
from .base import CommandHandler


class ClearCommandHandler(CommandHandler):
    async def handle(self, args: str) -> None:
        try:
            if self.message_history is None:
                self.console.print(
                    "[red]Message history is not initialized. Please connect to a server first.[/red]"
                )
                return
            await self.message_history.clear()
            # システムプロンプトを保持したまま新しいメッセージ履歴を初期化
            await self.message_history.factory(
                system_prompt=self.message_history._system_prompt
            )
            self.console.print("[green]Message history has been cleared.[/green]")
        except Exception as e:
            self.console.print(f"[red]Error clearing history: {str(e)}[/red]")
