"""Interactive REPL for Kagura AI"""

import asyncio
import importlib.util
import keyword
import os
import sys
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import (
    Completer,
    Completion,
    WordCompleter,
    merge_completers,
)
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.python import PythonLexer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Ensure UTF-8 encoding for console I/O
console = Console(force_terminal=True, legacy_windows=False)

# Custom prompt_toolkit style
prompt_style = Style.from_dict(
    {
        "prompt": "#00aa00 bold",  # Green prompt
        "continuation": "#888888",  # Gray continuation
    }
)


class CommandCompleter(Completer):
    """Custom completer for REPL commands (starting with /)"""

    def __init__(self):
        self.commands = ["help", "agents", "model", "temp", "exit", "clear"]

    def get_completions(self, document, complete_event):
        """Generate completions for commands"""
        text = document.text_before_cursor

        # Only complete if text starts with /
        if text.startswith("/"):
            word = text[1:]  # Remove leading /
            for cmd in self.commands:
                if cmd.startswith(word.lower()):
                    # Yield completion without the leading /
                    # start_position is negative to replace the typed word
                    yield Completion(cmd, start_position=-len(word))


class KaguraREPL:
    """Interactive REPL for Kagura AI"""

    def __init__(self, auto_import_agents: bool = True):
        # Load .env file if it exists
        load_dotenv()

        self.agents: dict[str, Any] = {}
        self.history: list[str] = []
        self.default_model: str = "gpt-4o-mini"
        self.default_temperature: float = 0.7
        self.auto_import_agents = auto_import_agents

        # Create persistent event loop for async execution
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Persistent namespace for REPL
        self.namespace: dict[str, Any] = {
            "__name__": "__main__",
            "console": console,
            "agents": self.agents,
        }

        # Set up prompt_toolkit session
        history_dir = os.path.expanduser("~/.kagura")
        os.makedirs(history_dir, exist_ok=True)
        self.history_file = os.path.join(history_dir, "repl_history")

        # Command completer for REPL commands (custom completer to avoid // issue)
        command_completer = CommandCompleter()

        # Python code completer (keywords, builtins, common imports)
        python_keywords = list(keyword.kwlist)

        # Get built-in functions properly
        if isinstance(__builtins__, dict):
            python_builtins = list(__builtins__.keys())
        else:
            python_builtins = dir(__builtins__)

        # Common functions and imports to prioritize
        common_words = [
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "input",
            "open",
            "help",
            "type",
            "isinstance",
            "enumerate",
            "zip",
            "map",
            "filter",
            "import",
            "from",
            "as",
            "kagura",
            "asyncio",
            "async",
            "await",
            "agent",
        ]

        # Combine all words and remove duplicates while preserving order
        seen = set()
        self.python_words = []
        for word in common_words + python_keywords + python_builtins:
            if word not in seen and not word.startswith("_"):
                seen.add(word)
                self.python_words.append(word)

        # Create python completer (will be updated with agent names)
        self.python_completer = WordCompleter(
            self.python_words,
            ignore_case=False,
            sentence=False,  # Allow word-level completion
            match_middle=False,  # Only match from start of word
        )

        # Merge completers
        combined_completer = merge_completers(
            [command_completer, self.python_completer]
        )

        # Custom key bindings for multiline support
        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            """Handle Enter key - newline or execute on double Enter"""
            buffer = event.current_buffer
            text = buffer.text

            # Commands starting with / execute immediately
            if text.strip().startswith("/"):
                buffer.validate_and_handle()
                return

            # IPython-style: empty line triggers execution
            # If current line is empty and we have previous content, execute
            if text.endswith("\n") or (text and not text.split("\n")[-1].strip()):
                # Last line is empty, execute
                if text.strip():  # But only if there's actual content
                    buffer.validate_and_handle()
                    return

            # Otherwise, insert newline
            buffer.insert_text("\n")

        self.session = PromptSession(
            history=FileHistory(self.history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=combined_completer,
            complete_while_typing=True,
            lexer=PygmentsLexer(PythonLexer),
            style=prompt_style,
            multiline=True,  # Enable multiline input
            prompt_continuation="... ",  # Continuation prompt
            key_bindings=kb,
            enable_history_search=True,
        )

    def update_completions(self):
        """Update tab completion with current agent names"""
        # Add agent names to completion list
        agent_names = list(self.agents.keys())

        # Combine python words with agent names (remove duplicates)
        all_words = list(dict.fromkeys(self.python_words + agent_names))

        # Update the completer's word list
        self.python_completer.words = all_words

    def load_agents_from_directory(self, directory: Path | None = None):
        """Load agents from the specified directory (default: ./agents)"""
        if directory is None:
            directory = Path.cwd() / "agents"

        if not directory.exists() or not directory.is_dir():
            return

        console.print(f"[dim]Loading agents from {directory}...[/dim]")

        agent_files = list(directory.glob("*.py"))
        if not agent_files:
            return

        loaded_count = 0
        for agent_file in agent_files:
            try:
                # Load the module
                module_name = agent_file.stem
                spec = importlib.util.spec_from_file_location(
                    module_name, agent_file
                )

                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Find agent functions
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and asyncio.iscoroutinefunction(attr):
                        # Check for @agent decorator marker
                        if hasattr(attr, "_is_agent"):
                            self.agents[attr_name] = attr
                            loaded_count += 1
                            console.print(
                                f"[green]✓[/green] Loaded agent: "
                                f"[cyan]{attr_name}[/cyan] "
                                f"from [dim]{agent_file.name}[/dim]"
                            )

            except Exception as e:
                console.print(
                    f"[yellow]⚠[/yellow] Failed to load {agent_file.name}: {e}"
                )

        if loaded_count > 0:
            console.print(
                f"[green]Loaded {loaded_count} agent(s)[/green]\n"
            )
            # Update tab completions with loaded agent names
            self.update_completions()

    def show_welcome(self):
        """Display welcome message"""
        agent_info = ""
        if self.agents:
            agent_info = (
                f"\n[green]Loaded {len(self.agents)} agent(s) - "
                f"available in Tab completion[/green]"
            )

        console.print(
            Panel.fit(
                "[bold green]Kagura AI REPL[/bold green]\n"
                "Python-First AI Agent Framework\n\n"
                "Type [cyan]/help[/cyan] for commands, [cyan]/exit[/cyan] to quit\n"
                "[dim]Commands (/help, /exit)[/dim] = execute immediately\n"
                "[dim]Python code + Enter[/dim] = newline\n"
                "[dim]Empty line + Enter[/dim] = execute (IPython style)\n"
                "[dim]Tab[/dim] = autocomplete (includes loaded agents)"
                + agent_info,
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
                    temp_val = self.default_temperature
                    console.print(f"[green]Temperature changed to:[/green] {temp_val}")
                except ValueError:
                    console.print("[red]Error:[/red] Temperature must be a number")
            else:
                console.print(
                    f"Current temperature: [cyan]{self.default_temperature}[/cyan]"
                )
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
            # Add loaded agents to namespace
            for agent_name, agent_func in self.agents.items():
                self.namespace[agent_name] = agent_func

            # Try to import kagura modules (only once)
            if "agent" not in self.namespace:
                try:
                    from kagura import agent
                    from kagura.agents import execute_code

                    self.namespace["agent"] = agent
                    self.namespace["execute_code"] = execute_code
                except ImportError:
                    pass

            # Import asyncio for await support
            self.namespace["asyncio"] = asyncio

            # Check if code contains await (needs async context)
            if "await " in code:
                # Create async wrapper that modifies the persistent namespace
                async_code = "async def __repl_exec():\n"
                async_code += "    global " + ", ".join(
                    [k for k in self.namespace.keys() if not k.startswith("_")]
                )
                async_code += "\n"
                for line in code.split("\n"):
                    async_code += f"    {line}\n"
                async_code += "    return locals()\n"

                # Execute the async function definition
                exec(async_code, self.namespace)

                # Run and get local variables
                local_vars = self.loop.run_until_complete(
                    self.namespace["__repl_exec"]()
                )

                # Update namespace with new variables
                for key, value in local_vars.items():
                    if not key.startswith("_"):
                        self.namespace[key] = value

                # If the result should be printed (not an assignment)
                if "=" not in code.split("await")[0]:
                    # This was an expression, print the result
                    if "__repl_exec" in self.namespace:
                        result = local_vars.get("return", None)
                        if result is not None:
                            console.print(repr(result))

            else:
                # Try to evaluate as expression first
                try:
                    result = eval(code, self.namespace)
                    if result is not None:
                        console.print(repr(result))
                except SyntaxError:
                    # If not an expression, execute as statement
                    exec(code, self.namespace)

            # Update agents if any were defined
            agents_updated = False
            for key, value in self.namespace.items():
                if key not in ["__name__", "console", "agents"] and callable(value):
                    if hasattr(value, "_is_agent"):
                        self.agents[key] = value
                        console.print(f"[green]Agent '{key}' defined[/green]")
                        agents_updated = True

            # Update completions if new agents were added
            if agents_updated:
                self.update_completions()

        except SyntaxError as e:
            console.print(f"[red]Syntax Error:[/red] {e}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {type(e).__name__}: {e}")

    def read_multiline(self) -> str:
        """Read multiline input with prompt_toolkit"""
        try:
            # PromptSession now handles multiline internally
            # with our custom Enter/Shift+Enter key bindings
            user_input = self.session.prompt(">>> ")
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

    def run(self, agents_directory: Path | None = None):
        """Run the REPL"""
        # Auto-import agents from ./agents directory first
        if self.auto_import_agents:
            self.load_agents_from_directory(agents_directory)

        # Show welcome after loading agents (so count is correct)
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
@click.option(
    "--no-auto-import",
    is_flag=True,
    help="Disable automatic agent import from ./agents directory",
)
@click.option(
    "--agents-dir",
    type=click.Path(exists=True, path_type=Path),
    help="Custom agents directory (default: ./agents)",
)
def repl(no_auto_import: bool, agents_dir: Path | None):
    """Start interactive REPL

    The REPL automatically imports agents from ./agents directory.
    Use --no-auto-import to disable this behavior.

    Examples:
        kagura repl                    # Auto-import from ./agents
        kagura repl --no-auto-import   # Don't auto-import
        kagura repl --agents-dir ./my-agents  # Custom directory
    """
    repl_instance = KaguraREPL(auto_import_agents=not no_auto_import)
    repl_instance.run(agents_directory=agents_dir)
