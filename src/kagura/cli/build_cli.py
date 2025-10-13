"""CLI commands for building agents with Meta Agent"""

import asyncio
from pathlib import Path

import click
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
    "--no-validate",
    is_flag=True,
    help="Skip code validation",
)
def agent_command(
    description: str | None,
    output: Path | None,
    model: str,
    interactive: bool,
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
                f"[bold]Memory:[/bold] {'Yes' if spec.has_memory else 'No'}",
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
