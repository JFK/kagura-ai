"""
Main CLI entry point for Kagura AI
"""

import click

# Direct import to avoid loading kagura/__init__.py
from kagura.version import __version__

from .lazy import LazyGroup


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "chat": (
            "kagura.cli.chat",
            "chat",
            "Start an interactive chat session with AI",
        ),
        "mcp": (
            "kagura.cli.mcp",
            "mcp",
            "MCP (Model Context Protocol) commands",
        ),
        "monitor": (
            "kagura.cli.monitor",
            "monitor",
            "Monitor agent execution telemetry",
        ),
        "auth": (
            "kagura.cli.auth_cli",
            "auth_group",
            "OAuth2 authentication commands",
        ),
    },
)
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


if __name__ == "__main__":
    cli(obj={})
