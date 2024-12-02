import asyncio
import sys
from importlib.metadata import version

import click

from kagura.core.config import ConfigInitializer

from .assistant import KaguraAIAssistant
from .commands import create, install


def get_version():
    try:
        return version("kagura-ai")
    except Exception:
        return "unknown"


@click.group(invoke_without_command=True)
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    """Kagura AI - A flexible AI agent framework"""
    # Initialize configuration if needed
    ConfigInitializer().initialize()

    # デフォルトでchatコマンドを実行
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
def chat():
    """Start interactive chat with Kagura AI"""
    try:
        assistant = KaguraAIAssistant()
        asyncio.run(assistant.arun())
    except KeyboardInterrupt:
        print("\nShutting down Kagura AI...")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


# Add the create command
cli.add_command(create)

# Add the install command
cli.add_command(install)


def entry_point():
    """Entry point for the CLI application"""
    return cli()


if __name__ == "__main__":
    sys.exit(entry_point())
