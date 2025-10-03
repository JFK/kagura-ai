# cli/commands/system_command.py
import yaml

from .base import CommandHandler
from ...core.config import ConfigBase


class SystemCommandHandler(CommandHandler):
    """Handler for the /system command that displays system configuration"""

    async def handle(self, args: str) -> None:
        try:
            # Try to read from user config first
            config = ConfigBase()

            # Format the YAML for display
            formatted_yaml = yaml.dump(
                config.system_config,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                width=float("inf"),  # avoid line wrapping
            )

            self.console.panel(
                f"[cyan]{formatted_yaml}[/cyan]",
                title="[bold blue]System Configuration[/bold blue]",
                border_style="blue",
            )

        except Exception as e:
            self.console.print(
                f"[red]Error reading system configuration: {str(e)}[/red]"
            )
