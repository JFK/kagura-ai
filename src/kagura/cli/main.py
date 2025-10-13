"""
Main CLI entry point for Kagura AI
"""

import click

from ..version import __version__
from .auth_cli import auth_group
from .build_cli import build_group
from .chat import chat
from .commands_cli import run
from .mcp import mcp
from .monitor import monitor
from .repl import repl


@click.group()
@click.version_option(version=__version__, prog_name="Kagura AI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool):
    """
    Kagura AI - Python-First AI Agent Framework

    A framework for building AI agents with code execution capabilities.
    Use subcommands to interact with the framework.

    Examples:
      kagura version          Show version information
      kagura --help           Show this help message
    """
    # Store options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@cli.command()
@click.pass_context
def version(ctx: click.Context):
    """Show version information"""
    if not ctx.obj.get("quiet"):
        click.echo(f"Kagura AI v{__version__}")
        if ctx.obj.get("verbose"):
            click.echo("Python-First AI Agent Framework")
            click.echo("https://github.com/JFK/kagura-ai")


# Add subcommands to CLI group
cli.add_command(repl)
cli.add_command(chat)
cli.add_command(mcp)
cli.add_command(run)
cli.add_command(monitor)
cli.add_command(auth_group)
cli.add_command(build_group)


if __name__ == "__main__":
    cli(obj={})
