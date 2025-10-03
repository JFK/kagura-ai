"""Interactive REPL for Kagura AI"""
import sys
from typing import Any
import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel

# Ensure UTF-8 encoding for console I/O
console = Console(force_terminal=True, legacy_windows=False)


class KaguraREPL:
    """Interactive REPL for Kagura AI"""

    def __init__(self):
        self.agents: dict[str, Any] = {}
        self.history: list[str] = []

    def show_welcome(self):
        """Display welcome message"""
        console.print(
            Panel.fit(
                "[bold green]Kagura AI REPL[/bold green]\n"
                "Python-First AI Agent Framework\n\n"
                "Type [cyan]/help[/cyan] for commands, "
                "[cyan]/exit[/cyan] to quit",
                border_style="green",
            )
        )

    def show_help(self):
        """Display help information"""
        help_table = Table(title="Available Commands", show_header=True)
        help_table.add_column("Command", style="cyan", width=15)
        help_table.add_column("Description", style="white")

        commands = [
            ("/help", "Show this help message"),
            ("/agents", "List all defined agents"),
            ("/exit", "Exit the REPL"),
            ("/clear", "Clear the screen"),
        ]

        for cmd, desc in commands:
            help_table.add_row(cmd, desc)

        console.print(help_table)

    def show_agents(self):
        """Display all defined agents"""
        if not self.agents:
            console.print("[yellow]No agents defined yet[/yellow]")
            return

        agents_table = Table(title="Defined Agents", show_header=True)
        agents_table.add_column("Name", style="cyan", width=20)
        agents_table.add_column("Type", style="green")

        for name, agent in self.agents.items():
            agent_type = type(agent).__name__
            agents_table.add_row(name, agent_type)

        console.print(agents_table)

    def clear_screen(self):
        """Clear the console screen"""
        console.clear()
        self.show_welcome()

    def execute_command(self, command: str):
        """Execute a special command"""
        command = command.strip()

        if command == "/help":
            self.show_help()
        elif command == "/agents":
            self.show_agents()
        elif command == "/exit":
            console.print("[green]Goodbye![/green]")
            sys.exit(0)
        elif command == "/clear":
            self.clear_screen()
        else:
            console.print(f"[red]Unknown command: {command}[/red]")
            console.print("Type [cyan]/help[/cyan] for available commands")

    def execute_code(self, code: str):
        """Execute Python code"""
        try:
            # Create a namespace with kagura imports
            namespace = {
                "__name__": "__main__",
                "console": console,
                "agents": self.agents,
            }

            # Try to import kagura modules
            try:
                from kagura import agent
                from kagura.agents import execute_code

                namespace["agent"] = agent
                namespace["execute_code"] = execute_code
            except ImportError:
                pass

            # Execute the code
            exec(code, namespace)

            # Update agents if any were defined
            for key, value in namespace.items():
                if key not in ["__name__", "console", "agents"] and callable(value):
                    if hasattr(value, "_is_agent"):
                        self.agents[key] = value

        except SyntaxError as e:
            console.print(f"[red]Syntax Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {type(e).__name__}: {e}")

    def read_multiline(self) -> str:
        """Read multiline input"""
        lines = []
        prompt = "[bold blue]>>>[/bold blue] "

        while True:
            try:
                if lines:
                    prompt = "[bold blue]...[/bold blue] "

                # Use input() instead of console.input() to avoid encoding issues
                console.print(prompt, end="")
                line = input()

                # Empty line ends multiline input
                if not line.strip() and lines:
                    break

                lines.append(line)

                # Single command or single line
                if line.startswith("/"):
                    break

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Input cancelled[/yellow]")
                return ""

        return "\n".join(lines)

    def run(self):
        """Run the REPL"""
        self.show_welcome()

        while True:
            try:
                user_input = self.read_multiline()

                if not user_input.strip():
                    continue

                # Save to history
                self.history.append(user_input)

                # Handle commands
                if user_input.strip().startswith("/"):
                    self.execute_command(user_input.strip())
                else:
                    self.execute_code(user_input)

            except (KeyboardInterrupt, EOFError):
                console.print("\n[green]Goodbye![/green]")
                break


@click.command()
def repl():
    """Start interactive REPL"""
    repl_instance = KaguraREPL()
    repl_instance.run()
