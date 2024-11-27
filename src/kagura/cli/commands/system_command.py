# cli/commands/system_command.py
from pathlib import Path
import yaml

from .base import CommandHandler


class SystemCommandHandler(CommandHandler):
    """Handler for the /system command that displays system configuration"""

    async def handle(self, args: str) -> None:
        try:
            # Try to read from user config first
            config_path = Path.home() / ".config" / "kagura" / "agents" / "system.yml"

            if not config_path.exists():
                # Fall back to package default if user config doesn't exist
                config_path = (
                    Path(__file__).parent.parent.parent / "agents" / "system.yml"
                )
            if not config_path.exists():
                self.console.print("[red]Error: system.yml not found[/red]")
                return

            with open(config_path, "r", encoding="utf-8") as f:
                system_config = yaml.safe_load(f)

            # Format the YAML for display
            formatted_yaml = yaml.dump(
                system_config,
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
