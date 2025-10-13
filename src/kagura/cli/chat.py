"""
CLI command for interactive chat
"""

import asyncio
from pathlib import Path

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
@click.option(
    "--enable-multimodal",
    is_flag=True,
    help="Enable multimodal RAG (images, PDFs, audio)",
)
@click.option(
    "--dir",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to index for RAG (requires --enable-multimodal)",
)
@click.option(
    "--enable-web",
    is_flag=True,
    help="Enable web search capabilities",
)
@click.option(
    "--full",
    is_flag=True,
    help="Enable all features (multimodal + web). Requires --dir",
)
@click.option(
    "--no-routing",
    is_flag=True,
    help="Disable automatic agent routing",
)
def chat(
    model: str,
    enable_multimodal: bool,
    dir: Path | None,
    enable_web: bool,
    full: bool,
    no_routing: bool,
) -> None:
    """
    Start an interactive chat session with AI.

    Examples:

        # Start chat with default model
        kagura chat

        # Use specific model
        kagura chat --model gpt-4o

        # Enable multimodal with directory RAG
        kagura chat --enable-multimodal --dir ./project

        # Enable web search
        kagura chat --enable-web

        # Enable both multimodal and web
        kagura chat --enable-multimodal --dir ./project --enable-web

        # Full-featured mode (all capabilities)
        kagura chat --full --dir ./project
    """
    # Handle --full flag
    if full:
        if not dir:
            raise click.UsageError(
                "--full requires --dir to be set for multimodal RAG"
            )
        enable_multimodal = True
        enable_web = True

    # Validate options
    if dir and not enable_multimodal:
        raise click.UsageError(
            "--dir requires --enable-multimodal to be set"
        )

    session = ChatSession(
        model=model,
        enable_multimodal=enable_multimodal,
        rag_directory=dir,
        enable_web=enable_web,
        enable_routing=not no_routing,
    )
    asyncio.run(session.run())
