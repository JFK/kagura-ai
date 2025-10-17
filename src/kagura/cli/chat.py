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
    default="gpt-5-mini",
    help="LLM model to use",
    show_default=True,
)
def chat(model: str) -> None:
    """
    Start an interactive chat session with AI (Claude Code-like experience).

    All capabilities are automatically available:
    - File operations (read, write, search) with multimodal support
    - Code execution (Python sandbox)
    - Web search and URL fetching
    - YouTube video summarization
    - Image, PDF, audio, and video analysis with Gemini

    The agent will automatically use the right tool based on your request.

    Examples:

        # Basic chat
        kagura chat

        # Use specific model
        kagura chat --model gpt-4o

        # Then in chat:
        [You] > Read src/main.py and explain it
        [You] > Analyze this image: diagram.png
        [You] > Summarize this PDF: report.pdf
        [You] > Extract audio from video.mp4 and transcribe
        [You] > Search the web for Python best practices
        [You] > Summarize https://youtube.com/watch?v=xxx
        [You] > Write a test file for this function
        [You] > Execute: print([x**2 for x in range(10)])
    """
    session = ChatSession(model=model)
    asyncio.run(session.run())
