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
def chat(
    model: str,
    enable_multimodal: bool,
    dir: Path | None,
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

        # Enable multimodal without directory
        kagura chat --enable-multimodal
    """
    # Validate options
    if dir and not enable_multimodal:
        raise click.UsageError(
            "--dir requires --enable-multimodal to be set"
        )

    session = ChatSession(
        model=model,
        enable_multimodal=enable_multimodal,
        rag_directory=dir,
    )
    asyncio.run(session.run())
