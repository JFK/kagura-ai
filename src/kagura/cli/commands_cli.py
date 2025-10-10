"""CLI commands for custom command execution."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from ..commands import CommandExecutor, CommandLoader

console = Console()


@click.command()
@click.argument("command_name")
@click.option(
    "--param",
    "-p",
    multiple=True,
    help="Command parameter in key=value format (can be used multiple times)",
)
@click.option(
    "--commands-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Custom commands directory (default: ~/.kagura/commands)",
)
@click.option(
    "--no-inline",
    is_flag=True,
    help="Disable inline command execution",
)
@click.pass_context
def run(
    ctx: click.Context,
    command_name: str,
    param: tuple[str, ...],
    commands_dir: Path | None,
    no_inline: bool,
):
    """Run a custom command.

    Execute a custom command defined in a Markdown file.

    Examples:

      \b
      # Run a command
      kagura run git-workflow

      \b
      # Run with parameters
      kagura run analyze-data --param file=data.csv --param verbose=true

      \b
      # Use custom commands directory
      kagura run my-cmd --commands-dir ./my-commands

      \b
      # Disable inline command execution
      kagura run my-cmd --no-inline
    """
    try:
        # Load commands
        loader = CommandLoader(commands_dir)

        try:
            commands = loader.load_all()
        except FileNotFoundError:
            dirs_str = ", ".join(str(d) for d in loader.commands_dirs)
            console.print(f"[red]Error:[/red] Commands directory not found: {dirs_str}")
            console.print("\n[yellow]Tip:[/yellow] Create the directory with:")
            for cmd_dir in loader.commands_dirs:
                console.print(f"  mkdir -p {cmd_dir}")
            sys.exit(1)

        # Get command
        command = commands.get(command_name)
        if not command:
            console.print(f"[red]Error:[/red] Command not found: {command_name}")
            console.print("\n[yellow]Available commands:[/yellow]")
            for name, cmd in commands.items():
                console.print(f"  • {name}: {cmd.description}")
            sys.exit(1)

        # Parse parameters
        parameters = {}
        for p in param:
            if "=" not in p:
                console.print(f"[red]Error:[/red] Invalid parameter format: {p}")
                console.print("[yellow]Use format:[/yellow] key=value")
                sys.exit(1)

            key, value = p.split("=", 1)
            parameters[key.strip()] = value.strip()

        # Validate parameters
        try:
            if command.parameters:
                command.validate_parameters(parameters)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            if command.parameters:
                console.print("\n[yellow]Required parameters:[/yellow]")
                for param_name, param_def in command.parameters.items():
                    if isinstance(param_def, dict):
                        required = param_def.get("required", False)
                        param_type = param_def.get("type", "any")
                        req_str = " (required)" if required else " (optional)"
                        console.print(f"  • {param_name}: {param_type}{req_str}")
                    else:
                        console.print(f"  • {param_name}: {param_def}")
            sys.exit(1)

        # Execute command
        if not ctx.obj.get("quiet"):
            console.print(
                Panel(
                    f"[bold]{command.name}[/bold]\n{command.description}",
                    title="Executing Command",
                    border_style="blue",
                )
            )

        executor = CommandExecutor(enable_inline=not no_inline)
        result = executor.execute(command, parameters)

        # Display result
        if not ctx.obj.get("quiet"):
            console.print("\n[bold green]Rendered Command:[/bold green]")
            console.print(Panel(result, border_style="green"))
        else:
            # In quiet mode, just print the result
            console.print(result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if ctx.obj.get("verbose"):
            import traceback

            console.print("\n[yellow]Traceback:[/yellow]")
            traceback.print_exc()
        sys.exit(1)
