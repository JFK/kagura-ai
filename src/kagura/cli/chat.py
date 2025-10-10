"""
CLI command for interactive chat
"""
import asyncio

import click

from kagura.chat import ChatSession


@click.command()
@click.option(
    "--model",
    "-m",
    default="gpt-4o-mini",
    help="LLM model to use",
    show_default=True,
)
def chat(model: str) -> None:
    """
    Start an interactive chat session with AI.

    Examples:

        # Start chat with default model
        kagura chat

        # Use specific model
        kagura chat --model gpt-4o
    """
    session = ChatSession(model=model)
    asyncio.run(session.run())
