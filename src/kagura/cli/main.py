"""
Main CLI entry point for Kagura AI
"""

import click
from dotenv import load_dotenv

# Direct import to avoid loading kagura/__init__.py
from kagura.version import __version__

from .lazy import LazyGroup


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "init": (
            "kagura.cli.init",
            "init",
            "Setup user preferences (name, location, topics)",
        ),
        "doctor": (
            "kagura.cli.doctor",
            "doctor",
            "Run comprehensive system health check",
        ),
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
        "api": (
            "kagura.cli.api_cli",
            "api_group",
            "API Key management commands",
        ),
        "memory": (
            "kagura.cli.memory_cli",
            "memory_group",
            "Memory management commands",
        ),
        "coding": (
            "kagura.cli.coding_cli",
            "coding",
            "Coding memory inspection commands",
        ),
        "config": (
            "kagura.cli.config_cli",
            "app",
            "Configuration management and diagnostics",
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
    # Auto-load .env file from current directory (Issue #444)
    # This allows users to store API keys in .env instead of system environment
    load_dotenv()

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
