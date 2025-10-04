"""Interactive REPL for Kagura AI"""
import sys
import os
from typing import Any
import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion, WordCompleter, merge_completers
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.filters import Condition
from pygments.lexers.python import PythonLexer
import keyword

# Ensure UTF-8 encoding for console I/O
console = Console(force_terminal=True, legacy_windows=False)

# Custom prompt_toolkit style
prompt_style = Style.from_dict({
    'prompt': '#00aa00 bold',  # Green prompt
    'continuation': '#888888',  # Gray continuation
})


class CommandCompleter(Completer):
    """Custom completer for REPL commands (starting with /)"""

    def __init__(self):
        self.commands = ['help', 'agents', 'model', 'temp', 'exit', 'clear']

    def get_completions(self, document, complete_event):
        """Generate completions for commands"""
        text = document.text_before_cursor

        # Only complete if text starts with /
        if text.startswith('/'):
            word = text[1:]  # Remove leading /
            for cmd in self.commands:
                if cmd.startswith(word.lower()):
                    # Yield completion without the leading /
                    # start_position is negative to replace the typed word
                    yield Completion(cmd, start_position=-len(word))


class KaguraREPL:
    """Interactive REPL for Kagura AI"""

    def __init__(self):
        # Load .env file if it exists
        load_dotenv()

        self.agents: dict[str, Any] = {}
        self.history: list[str] = []
        self.default_model: str = "gpt-4o-mini"
        self.default_temperature: float = 0.7

        # Set up prompt_toolkit session
        history_dir = os.path.expanduser("~/.kagura")
        os.makedirs(history_dir, exist_ok=True)
        self.history_file = os.path.join(history_dir, "repl_history")

        # Command completer for REPL commands (custom completer to avoid // issue)
        command_completer = CommandCompleter()

        # Python code completer (keywords, builtins, common imports)
        python_keywords = list(keyword.kwlist)
        python_builtins = list(dir(__builtins__))
        common_imports = ['import', 'from', 'as', 'kagura', 'asyncio', 'async', 'await']
        python_words = list(set(python_keywords + python_builtins + common_imports))
        python_completer = WordCompleter(
            python_words,
            ignore_case=False,
            sentence=False,  # Allow word-level completion
            match_middle=False,  # Only match from start of word
        )

        # Merge completers
        combined_completer = merge_completers([command_completer, python_completer])

        # Custom key bindings for multiline support
        kb = KeyBindings()

        @kb.add('enter')
        def _(event):
            """Handle Enter key - newline or execute on double Enter"""
            buffer = event.current_buffer
            text = buffer.text

            # IPython-style: empty line triggers execution
            # If current line is empty and we have previous content, execute
            if text.endswith('\n') or (text and not text.split('\n')[-1].strip()):
                # Last line is empty, execute
                if text.strip():  # But only if there's actual content
                    buffer.validate_and_handle()
                    return

            # Otherwise, insert newline
            buffer.insert_text('\n')

        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=combined_completer,
            complete_while_typing=True,
            lexer=PygmentsLexer(PythonLexer),
            style=prompt_style,
            multiline=True,  # Enable multiline input
            prompt_continuation='... ',  # Continuation prompt
            key_bindings=kb,
            enable_history_search=True,
        )

    def show_welcome(self):
        """Display welcome message"""
        console.print(
            Panel.fit(
                "[bold green]Kagura AI REPL[/bold green]\n"
                "Python-First AI Agent Framework\n\n"
                "Type [cyan]/help[/cyan] for commands, [cyan]/exit[/cyan] to quit\n"
                "[dim]Enter[/dim] = newline\n"
                "[dim]Empty line + Enter[/dim] = execute (IPython style)\n"
                "[dim]Tab[/dim] = autocomplete",
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
            ("/model", "Show or set default model"),
            ("/temp", "Show or set default temperature"),
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
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        if cmd == "/help":
            self.show_help()
        elif cmd == "/agents":
            self.show_agents()
        elif cmd == "/model":
            if arg:
                self.default_model = arg
                console.print(f"[green]Model changed to:[/green] {arg}")
            else:
                console.print(f"Current model: [cyan]{self.default_model}[/cyan]")
        elif cmd == "/temp":
            if arg:
                try:
                    self.default_temperature = float(arg)
                    console.print(f"[green]Temperature changed to:[/green] {self.default_temperature}")
                except ValueError:
                    console.print("[red]Error:[/red] Temperature must be a number")
            else:
                console.print(f"Current temperature: [cyan]{self.default_temperature}[/cyan]")
        elif cmd == "/exit":
            console.print("[green]Goodbye![/green]")
            sys.exit(0)
        elif cmd == "/clear":
            self.clear_screen()
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
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

            # Try to evaluate as expression first
            try:
                result = eval(code, namespace)
                if result is not None:
                    console.print(repr(result))
            except SyntaxError:
                # If not an expression, execute as statement
                exec(code, namespace)

            # Update agents if any were defined
            for key, value in namespace.items():
                if key not in ["__name__", "console", "agents"] and callable(value):
                    if hasattr(value, "_is_agent"):
                        self.agents[key] = value
                        console.print(f"[green]Agent '{key}' defined[/green]")

        except SyntaxError as e:
            console.print(f"[red]Syntax Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {type(e).__name__}: {e}")

    def read_multiline(self) -> str:
        """Read multiline input with prompt_toolkit"""
        try:
            # PromptSession now handles multiline internally
            # with our custom Enter/Shift+Enter key bindings
            user_input = self.session.prompt('>>> ')
            return user_input
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Input cancelled[/yellow]")
            return ""

    def _is_incomplete(self, code: str) -> bool:
        """Check if code is incomplete and needs more lines"""
        # Simple heuristic: if it ends with : or has unclosed brackets
        code = code.rstrip()
        if code.endswith(":"):
            return True

        # Check for unclosed brackets/parentheses
        open_brackets = code.count("(") + code.count("[") + code.count("{")
        close_brackets = code.count(")") + code.count("]") + code.count("}")
        if open_brackets > close_brackets:
            return True

        # Try to compile - if SyntaxError with "unexpected EOF", it's incomplete
        try:
            compile(code, "<stdin>", "exec")
            return False
        except SyntaxError as e:
            if "unexpected EOF" in str(e) or "incomplete" in str(e).lower():
                return True
            return False
        except Exception:
            return False

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
