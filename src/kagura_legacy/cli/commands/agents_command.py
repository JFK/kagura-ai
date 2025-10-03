# cli/commands/agents_command.py
from rich import box
from rich.table import Table

from kagura.core.agent import Agent
from .base import CommandHandler


class AgentsCommandHandler(CommandHandler):
    """Handler for the /agents command that displays available agents"""

    async def handle(self, args: str) -> None:
        try:
            # Get list of all agents
            agents = Agent.list_agents()

            if not agents:
                self.console.print("[yellow]No agents found[/yellow]")
                return

            # Create and configure table
            table = Table(title="Available Agents", box=box.ROUNDED)
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Description", style="white")
            table.add_column("Path", style="blue")

            # Add agents to table
            for agent in agents:
                table.add_row(
                    agent["name"],
                    agent["type"],
                    agent["description"],
                    agent["path"],
                )

            self.console.panel(table, border_style="blue")

        except Exception as e:
            self.console.print(f"[red]Error listing agents: {str(e)}[/red]")
