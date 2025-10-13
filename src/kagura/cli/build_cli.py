"""CLI commands for building agents with Meta Agent"""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax

from kagura.meta import MetaAgent
from kagura.meta.validator import ValidationError

console = Console()


@click.group(name="build")
def build_group():
    """Build agents, tools, and workflows using AI

    The build command group provides AI-powered code generation
    for creating Kagura agents from natural language descriptions.

    Examples:
        kagura build agent              Interactive agent builder
        kagura build agent -d "..."     Build agent from description
    """
    pass


@build_group.command(name="agent")
@click.option(
    "--description",
    "-d",
    help="Natural language agent description",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: agents/<name>.py)",
)
@click.option(
    "--model",
    default="gpt-4o-mini",
    help="LLM model for code generation (default: gpt-4o-mini)",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Interactive mode (default: True)",
)
@click.option(
    "--chat",
    "-c",
    is_flag=True,
    help="Conversational mode with multi-turn refinement",
)
@click.option(
    "--no-validate",
    is_flag=True,
    help="Skip code validation",
)
def agent_command(
    description: str | None,
    output: Path | None,
    model: str,
    interactive: bool,
    chat: bool,
    no_validate: bool,
):
    """Build an AI agent from natural language description

    This command uses AI to generate complete Kagura agent code
    from your natural language description. The generated code
    includes the @agent decorator, proper type hints, and
    documentation.

    Examples:
        # Interactive mode
        kagura build agent

        # Direct mode
        kagura build agent -d "Translate English to Japanese" -o translator.py

        # With custom model
        kagura build agent -d "..." --model gpt-4o
    """
    if chat:
        asyncio.run(
            _build_agent_chat_async(
                description, output, model, interactive, no_validate
            )
        )
    else:
        asyncio.run(
            _build_agent_async(description, output, model, interactive, no_validate)
        )


async def _build_agent_async(
    description: str | None,
    output: Path | None,
    model: str,
    interactive: bool,
    no_validate: bool,
):
    """Async implementation of agent build command"""

    # Interactive mode
    if interactive and not description:
        console.print(
            Panel.fit(
                "[bold cyan]🤖 Kagura Agent Builder[/bold cyan]\n"
                "Describe your agent in natural language and I'll generate the code.",
                border_style="cyan",
            )
        )

        description = Prompt.ask(
            "\n[bold]What should your agent do?[/bold]",
            default="Summarize text in 3 bullet points",
        )

    if not description:
        console.print("[red]Error: Description required[/red]")
        raise click.Abort()

    # Initialize MetaAgent
    console.print("\n[cyan]🔍 Parsing agent specification...[/cyan]")
    meta = MetaAgent(model=model, validate=not no_validate)

    try:
        # Parse description and generate code
        try:
            spec = await meta.parser.parse(description)
        except Exception as e:
            # Check if it's a Pydantic validation error
            error_msg = str(e)
            if "validation error" in error_msg.lower():
                console.print(
                    f"[red]❌ Failed to parse agent specification[/red]\n"
                    f"[yellow]The AI returned an invalid format. Please try:[/yellow]\n"
                    f"  • Simplifying your description\n"
                    f"  • Being more specific about what the agent should do\n"
                    f"  • Using a different model (--model gpt-4o)\n\n"
                    f"[dim]Technical details: {error_msg}[/dim]"
                )
                raise click.Abort()
            raise

        # Show parsed spec
        console.print(
            Panel(
                f"[bold]Name:[/bold] {spec.name}\n"
                f"[bold]Description:[/bold] {spec.description}\n"
                f"[bold]Input:[/bold] {spec.input_type}\n"
                f"[bold]Output:[/bold] {spec.output_type}\n"
                f"[bold]Tools:[/bold] "
                f"{', '.join(spec.tools) if spec.tools else 'None'}\n"
                f"[bold]Memory:[/bold] {'Yes' if spec.has_memory else 'No'}\n"
                f"[bold]Code execution:[/bold] "
                f"{'[green]Yes[/green]' if spec.requires_code_execution else 'No'}",
                title="📋 Agent Specification",
                border_style="green",
            )
        )

        # Confirm
        if interactive:
            if not Confirm.ask(
                "\n[bold]Generate agent code?[/bold]", default=True
            ):
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Generate code
        console.print("\n[cyan]⚙️  Generating agent code...[/cyan]")
        code = await meta.generate_from_spec(spec)

        # Validate (unless --no-validate)
        if not no_validate:
            console.print("[cyan]🔒 Validating code security...[/cyan]")
            console.print("[green]✅ Code validated[/green]")

        # Preview code
        if interactive:
            console.print("\n[bold]Generated Code Preview:[/bold]")
            syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
            console.print(syntax)

        # Determine output path
        if not output:
            output = Path("agents") / f"{spec.name}.py"

        # Save
        if interactive:
            output_str = Prompt.ask(
                "\n[bold]Save to[/bold]", default=str(output)
            )
            output = Path(output_str)

        # Save file
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(code, encoding="utf-8")

        console.print(f"\n[bold green]✅ Agent created: {output}[/bold green]")
        console.print(
            f"\n[dim]Usage:\n"
            f"  from {output.stem} import {spec.name}\n"
            f"  result = await {spec.name}(input_data)[/dim]"
        )

    except ValidationError as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if "--verbose" in click.get_current_context().args:
            console.print_exception()
        raise click.Abort()


async def _build_agent_chat_async(
    description: str | None,
    output: Path | None,
    model: str,
    interactive: bool,
    no_validate: bool,
):
    """Conversational mode for agent building with multi-turn refinement"""

    # Setup prompt session with history
    history = InMemoryHistory()
    session: PromptSession[str] = PromptSession(history=history)

    console.print(
        Panel.fit(
            "[bold cyan]🤖 Kagura Agent Builder - Chat Mode[/bold cyan]\n"
            "Describe your agent and refine it through conversation.\n"
            "[dim]Use ↑/↓ or Ctrl+P/N to navigate history[/dim]",
            border_style="cyan",
        )
    )

    # Initialize MetaAgent
    meta = MetaAgent(model=model, validate=not no_validate)

    # Get initial description
    if not description:
        console.print(
            "\n[bold]What should your agent do?[/bold] "
            "[dim](Be as detailed as you like)[/dim]"
        )
        description = await session.prompt_async(">>> ")

    if not description:
        console.print("[red]Error: Description required[/red]")
        raise click.Abort()

    # Conversation loop for spec refinement
    spec = None
    while True:
        try:
            console.print("\n[cyan]🔍 Parsing agent specification...[/cyan]")
            spec = await meta.parser.parse(description)

            # Show parsed spec
            console.print(
                Panel(
                    f"[bold]Name:[/bold] {spec.name}\n"
                    f"[bold]Description:[/bold] {spec.description}\n"
                    f"[bold]Input:[/bold] {spec.input_type}\n"
                    f"[bold]Output:[/bold] {spec.output_type}\n"
                    f"[bold]Tools:[/bold] "
                    f"{', '.join(spec.tools) if spec.tools else 'None'}\n"
                    f"[bold]Memory:[/bold] {'Yes' if spec.has_memory else 'No'}\n"
                    f"[bold]Code execution:[/bold] "
                    f"{'[green]Yes[/green]' if spec.requires_code_execution else 'No'}",
                    title="📋 Agent Specification",
                    border_style="green",
                )
            )

            # Ask for approval or refinement
            console.print(
                "\n[bold]What would you like to do?[/bold]\n"
                "  [green]approve[/green] - Generate code with this spec\n"
                "  [yellow]refine[/yellow] - Modify the specification\n"
                "  [red]cancel[/red] - Cancel agent creation"
            )

            action = await session.prompt_async(">>> ")
            action = action.lower().strip()

            if action == "approve":
                break
            elif action == "refine":
                console.print(
                    "\n[bold]How should I modify the specification?[/bold]"
                )
                refinement = await session.prompt_async(">>> ")
                description = f"{description}\n\nAdditional requirements: {refinement}"
                continue
            elif action == "cancel":
                console.print("[yellow]Cancelled[/yellow]")
                return
            else:
                console.print(
                    "[yellow]Invalid choice. Please enter 'approve', 'refine', "
                    "or 'cancel'[/yellow]"
                )
                continue

        except Exception as e:
            error_msg = str(e)
            if "validation error" in error_msg.lower():
                console.print(
                    f"[red]❌ Failed to parse agent specification[/red]\n"
                    f"[yellow]The AI returned an invalid format. "
                    f"Let's try again.[/yellow]\n"
                    f"[dim]Technical details: {error_msg}[/dim]"
                )
                console.print(
                    "\n[bold]Please rephrase your agent description:[/bold]"
                )
                description = await session.prompt_async(">>> ")
                if not description:
                    console.print("[yellow]Cancelled[/yellow]")
                    return
                continue
            raise

    if not spec:
        console.print("[red]Error: No specification approved[/red]")
        raise click.Abort()

    # Generate code
    console.print("\n[cyan]⚙️  Generating agent code...[/cyan]")
    code = await meta.generate_from_spec(spec)

    # Validate (unless --no-validate)
    if not no_validate:
        console.print("[cyan]🔒 Validating code security...[/cyan]")
        console.print("[green]✅ Code validated[/green]")

    # Preview code
    console.print("\n[bold]Generated Code Preview:[/bold]")
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
    console.print(syntax)

    # Ask for final approval
    console.print(
        "\n[bold]Do you want to save this code?[/bold]\n"
        "  [green]yes[/green] - Save the code\n"
        "  [yellow]no[/yellow] - Discard and exit"
    )

    save_action = await session.prompt_async(">>> ")
    if save_action.lower().strip() not in ["yes", "y"]:
        console.print("[yellow]Code discarded[/yellow]")
        return

    # Determine output path
    if not output:
        output = Path("agents") / f"{spec.name}.py"

    console.print("\n[bold]Save to:[/bold] [dim](press Enter for default)[/dim]")
    output_str = await session.prompt_async(f"[{output}] >>> ")
    if output_str.strip():
        output = Path(output_str.strip())

    # Save file
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(code, encoding="utf-8")

    console.print(f"\n[bold green]✅ Agent created: {output}[/bold green]")
    console.print(
        f"\n[dim]Usage:\n"
        f"  from {output.stem} import {spec.name}\n"
        f"  result = await {spec.name}(input_data)[/dim]"
    )


@build_group.command(name="run-agent")
@click.argument("agent_file", type=click.Path(exists=True, path_type=Path))
@click.argument("input_data", required=False)
@click.option(
    "--json",
    "-j",
    "as_json",
    is_flag=True,
    help="Parse input_data as JSON",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Save output to file instead of printing",
)
def run_agent_command(
    agent_file: Path,
    input_data: str | None,
    as_json: bool,
    output: Path | None,
):
    """Execute a generated agent file

    Run a Kagura agent from a Python file. The file must contain
    exactly one async function decorated with @agent.

    Examples:
        # Run with string input
        kagura build run-agent agents/translator.py "Hello world"

        # Run with JSON input
        kagura build run-agent agents/analyzer.py '{"text": "..."}' --json

        # Save output to file
        kagura build run-agent agents/generator.py "prompt" -o output.txt
    """
    asyncio.run(_run_agent_async(agent_file, input_data, as_json, output))


async def _run_agent_async(
    agent_file: Path,
    input_data: str | None,
    as_json: bool,
    output_path: Path | None,
):
    """Async implementation of agent execution"""

    try:
        # Load the agent module dynamically
        console.print(f"[cyan]📂 Loading agent from {agent_file}...[/cyan]")

        module_name = agent_file.stem
        spec = importlib.util.spec_from_file_location(module_name, agent_file)

        if spec is None or spec.loader is None:
            console.print(f"[red]❌ Failed to load module from {agent_file}[/red]")
            raise click.Abort()

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Find the agent function (async function decorated with @agent)
        agent_func = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and asyncio.iscoroutinefunction(attr):
                # Check if it has the agent marker
                if hasattr(attr, "_is_agent"):
                    agent_func = attr
                    break

        if agent_func is None:
            console.print(
                f"[red]❌ No @agent decorated async function found in "
                f"{agent_file}[/red]"
            )
            console.print(
                "[yellow]Make sure your agent file contains an async function "
                "decorated with @agent[/yellow]"
            )
            raise click.Abort()

        console.print(f"[green]✅ Loaded agent: {agent_func.__name__}[/green]")

        # Parse input data
        if input_data is None:
            console.print("[yellow]No input data provided, using empty string[/yellow]")
            parsed_input = ""
        elif as_json:
            try:
                parsed_input = json.loads(input_data)
            except json.JSONDecodeError as e:
                console.print(f"[red]❌ Invalid JSON: {e}[/red]")
                raise click.Abort()
        else:
            parsed_input = input_data

        # Execute the agent
        console.print("\n[cyan]⚙️  Executing agent...[/cyan]\n")

        result = await agent_func(parsed_input)

        # Display result
        console.print("\n[bold green]✅ Execution completed[/bold green]")
        console.print(
            Panel(
                str(result),
                title="Agent Output",
                border_style="green",
            )
        )

        # Save to file if requested
        if output_path:
            output_path.write_text(str(result), encoding="utf-8")
            console.print(f"\n[dim]Output saved to: {output_path}[/dim]")

    except ImportError as e:
        console.print(f"[red]❌ Failed to import agent: {e}[/red]")
        console.print(
            "[yellow]Make sure all dependencies are installed[/yellow]"
        )
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]❌ Error executing agent: {e}[/red]")
        console.print_exception()
        raise click.Abort()
