# cli/commands/help_command.py
from textwrap import dedent

from .base import CommandHandler


class HelpCommandHandler(CommandHandler):
    async def handle(self, args: str) -> None:
        help_text = dedent(
            """
            [bold cyan]Available Commands:[/bold cyan]

            [bold green]/help[/bold green]
                Show this help message
                Usage: /help

            [bold green]/history[/bold green]
                Display message history
                Usage: /history

            [bold green]/clear[/bold green]
                Clear message history
                Usage: /clear

            [bold green]/exit[/bold green]
                Exit Kagura AI
                Usage: /exit
        """
        )
        self.console.panel(help_text, title="[bold blue]Kagura AI Help[/bold blue]")
