"""
Interactive Chat Session for Kagura AI
"""

import asyncio
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from kagura import agent
from kagura.config.paths import get_config_dir, get_data_dir
from kagura.core.memory import MemoryManager
from kagura.core.tool_registry import tool_registry
from kagura.routing import AgentRouter, NoAgentFoundError

# Import chat tools to trigger @tool registration
from . import tools  # noqa: F401
from .completer import KaguraCompleter
from .display import EnhancedDisplay
from .utils import extract_response_content

# =============================================================================
# Tool Definitions for Claude Code-like Chat Experience
# =============================================================================


# Video Processing Helper
async def _video_extract_audio_tool(
    video_path: str, output_path: str | None = None
) -> str:
    """Extract audio from video file using ffmpeg.

    Args:
        video_path: Path to video file
        output_path: Output audio file path (default: same name .mp3)

    Returns:
        Success message with audio path or error message
    """
    import asyncio
    from pathlib import Path

    from rich.console import Console

    console = Console()
    console.print(f"[dim]🎥 Extracting audio from {video_path}...[/]")

    try:
        video = Path(video_path)
        if not video.exists():
            return f"Error: Video file not found: {video_path}"

        # Default output path
        if output_path is None:
            output_path = str(video.with_suffix(".mp3"))

        # Use ffmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i",
            str(video),
            "-vn",  # No video
            "-acodec",
            "libmp3lame",  # MP3 codec
            "-q:a",
            "2",  # Quality
            "-y",  # Overwrite
            output_path,
        ]

        # Run ffmpeg asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)

        if process.returncode == 0:
            console.print(f"[dim]✓ Audio extracted to {output_path}[/]")
            return f"Audio extracted successfully to: {output_path}"
        else:
            error_msg = stderr.decode("utf-8") if stderr else "Unknown error"
            return f"Error extracting audio: {error_msg}"

    except FileNotFoundError:
        return (
            "Error: ffmpeg not found.\n"
            "Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )
    except asyncio.TimeoutError:
        return "Error: Audio extraction timed out (>5 minutes)"
    except Exception as e:
        return f"Error: {str(e)}"


# File Operation Tools
async def _file_read_tool(
    file_path: str, prompt: str | None = None, mode: str = "auto"
) -> str:
    """Read a file (text or multimodal) and return its content.

    Supports:
    - Text files (.txt, .md, .py, .json, etc.): Direct reading
    - Images (.png, .jpg, etc.): Gemini Vision analysis
    - PDFs (.pdf): Gemini document analysis
    - Audio (.mp3, .wav, etc.): Gemini transcription
    - Video (.mp4, .mov, etc.):
        - mode="visual": Gemini visual analysis only
        - mode="audio": Extract audio + transcribe
        - mode="auto": Both visual + audio (default)

    Args:
        file_path: Path to file
        prompt: Optional custom prompt for multimodal files
        mode: Processing mode for videos (visual/audio/auto)

    Returns:
        File content or analysis result
    """
    from pathlib import Path

    from rich.console import Console

    from kagura.loaders.file_types import FileType, detect_file_type, is_multimodal_file

    console = Console()
    path = Path(file_path)

    if not path.exists():
        return f"Error: File not found: {file_path}"

    file_type = detect_file_type(path)

    # Text files: direct reading
    if file_type == FileType.TEXT or file_type == FileType.DATA:
        console.print(f"[dim]📄 Reading {file_path}...[/]")
        try:
            content = path.read_text(encoding="utf-8")
            lines = len(content.splitlines())
            console.print(f"[dim]✓ Read {lines} lines[/]")
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    # Multimodal files: use Gemini
    elif is_multimodal_file(path):
        console.print(f"[dim]📄 Processing {file_path} ({file_type.value})...[/]")

        try:
            from kagura.loaders.gemini import GeminiLoader
        except ImportError:
            return (
                "Error: Multimodal support requires google-generativeai.\n"
                "Install with: pip install kagura-ai[web]"
            )

        try:
            loader = GeminiLoader()

            # Special handling for video
            if file_type == FileType.VIDEO:
                if mode == "audio":
                    # Audio extraction + transcription only
                    audio_result = await _video_extract_audio_tool(file_path)

                    if "Error" not in audio_result:
                        audio_path = audio_result.split(": ")[-1].strip()
                        console.print("[dim]🎤 Transcribing extracted audio...[/]")
                        transcript = await loader.transcribe_audio(
                            audio_path, language="ja"
                        )
                        console.print("[dim]✓ Transcription complete[/]")
                        return transcript
                    else:
                        return audio_result

                elif mode == "auto":
                    # Both visual + audio
                    results = []

                    # Visual analysis
                    console.print("[dim]🎥 Analyzing video visually...[/]")
                    visual = await loader.analyze_video(
                        path,
                        prompt=prompt or "Describe what's happening in this video.",
                        language="ja",
                    )
                    results.append(f"### Visual Analysis\n{visual}")

                    # Audio extraction + transcription
                    audio_result = await _video_extract_audio_tool(file_path)
                    if "Error" not in audio_result:
                        audio_path = audio_result.split(": ")[-1].strip()
                        console.print("[dim]🎤 Transcribing extracted audio...[/]")
                        transcript = await loader.transcribe_audio(
                            audio_path, language="ja"
                        )
                        results.append(f"### Audio Transcription\n{transcript}")

                    console.print("[dim]✓ Video processing complete[/]")
                    return "\n\n".join(results)

                else:  # mode == "visual"
                    # Visual only
                    result = await loader.analyze_video(
                        path, prompt=prompt or "Describe this video.", language="ja"
                    )
                    console.print("[dim]✓ Visual analysis complete[/]")
                    return result

            else:
                # Other multimodal files (image, audio, PDF)
                result = await loader.process_file(path, prompt=prompt, language="ja")
                console.print(f"[dim]✓ {file_type.value.capitalize()} processed[/]")
                return result

        except Exception as e:
            return f"Error processing multimodal file: {str(e)}"

    else:
        return f"Unsupported file type: {file_type}"


async def _file_write_tool(file_path: str, content: str) -> str:
    """Write content to a local file.

    Args:
        file_path: Path to the file to write
        content: Content to write

    Returns:
        Success message or error
    """
    import shutil
    from pathlib import Path

    from rich.console import Console

    console = Console()
    console.print(f"[dim]📝 Writing to {file_path}...[/]")

    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Backup if file exists
        if path.exists():
            backup = path.with_suffix(path.suffix + ".backup")
            shutil.copy2(path, backup)
            console.print(f"[dim]💾 Backup created: {backup}[/]")

        path.write_text(content, encoding="utf-8")
        lines = len(content.splitlines())

        console.print(f"[dim]✓ Wrote {lines} lines[/]")
        return f"Successfully wrote {lines} lines to {file_path}"

    except Exception as e:
        return f"Error writing file: {str(e)}"


async def _file_search_tool(pattern: str, directory: str = ".") -> str:
    """Search for files matching pattern.

    Args:
        pattern: File name pattern (supports wildcards)
        directory: Directory to search in

    Returns:
        List of matching file paths
    """
    from pathlib import Path

    from rich.console import Console

    console = Console()
    console.print(f"[dim]🔍 Searching for '{pattern}' in {directory}...[/]")

    try:
        base_path = Path(directory)
        matches = list(base_path.rglob(pattern))

        console.print(f"[dim]✓ Found {len(matches)} files[/]")

        if not matches:
            return f"No files matching '{pattern}' found in {directory}"

        return "\n".join(str(m.relative_to(base_path)) for m in matches[:50])

    except Exception as e:
        return f"Error searching files: {str(e)}"


# Code Execution Tool
async def _execute_python_tool(code: str) -> str:
    """Execute Python code safely.

    Args:
        code: Python code to execute

    Returns:
        Execution result (stdout, stderr, or error)
    """
    from rich.console import Console

    from kagura.core.executor import CodeExecutor

    console = Console()
    console.print("[dim]🐍 Executing Python code...[/]")

    try:
        executor = CodeExecutor(timeout=30.0)
        result = await executor.execute(code)

        if result.success:
            console.print(f"[dim]✓ Executed in {result.execution_time:.2f}s[/]")

            output = []
            if result.stdout:
                output.append(f"Output:\n{result.stdout}")
            if result.result is not None:
                output.append(f"Result: {result.result}")

            return "\n".join(output) if output else "Execution successful (no output)"
        else:
            console.print("[dim]✗ Execution failed[/]")
            return f"Error: {result.error}\n{result.stderr}"

    except Exception as e:
        return f"Execution error: {str(e)}"


# Web & Content Tools
def _extract_youtube_urls_from_results(results_json: str) -> list[str]:
    """Extract YouTube URLs from Brave Search results

    Args:
        results_json: JSON string of search results

    Returns:
        List of YouTube URLs found in results
    """
    import json

    try:
        results = json.loads(results_json)
    except Exception:
        return []

    youtube_urls = []
    for result in results:
        url = result.get("url", "")
        if "youtube.com/watch" in url or "youtu.be/" in url:
            youtube_urls.append(url)

    return youtube_urls


async def _fetch_youtube_enhanced_data(url: str) -> dict[str, Any]:
    """Fetch YouTube metadata + transcript (safe, won't fail)

    Args:
        url: YouTube video URL

    Returns:
        Dict with url, title, duration, transcript (or error)
    """
    import json

    # Use backward-compatible import (re-exported from kagura.tools)
    from kagura.tools import get_youtube_metadata, get_youtube_transcript

    try:
        # Always fetch metadata first
        metadata_str = await get_youtube_metadata(url)
        metadata = json.loads(metadata_str)

        # Try to get transcript (may not be available)
        transcript = None
        try:
            transcript = await get_youtube_transcript(url, lang="en")
            # Truncate to reasonable length for context
            if len(transcript) > 2000:
                transcript = transcript[:2000] + "... (transcript continues)"
        except Exception:
            pass  # Transcript not available, continue without it

        return {
            "url": url,
            "title": metadata.get("title", "Unknown"),
            "duration": metadata.get("duration", ""),
            "transcript": transcript,
        }
    except Exception as e:
        return {"url": url, "error": str(e)}


async def _brave_search_tool(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API.

    Args:
        query: Search query
        count: Number of results (default: 5)

    Returns:
        Formatted search results

    Note:
        YouTube enhancement temporarily disabled for simplicity.
        Will re-enable in future update.
    """
    from rich.console import Console

    from kagura.tools import brave_web_search

    console = Console()
    console.print(f"[dim]  └─ 🔍 Brave Search: {query}...[/]")

    # Call search (now returns formatted text)
    result = await brave_web_search(query, count=count)

    # Parse and display results with titles and URLs
    try:
        # Extract title and URL pairs from formatted result
        lines = result.split("\n")
        results_to_display = []

        current_title = None
        for line in lines:
            # Title lines (numbered, e.g., "1. Title")
            match = re.match(r"^(\d+)\.\s+(.+)$", line)
            if match:
                current_title = match.group(2).strip()
            # URL lines (indented, start with http)
            elif current_title and line.strip().startswith("http"):
                url = line.strip()
                results_to_display.append((current_title, url))
                current_title = None

        if results_to_display:
            console.print("\n[dim]📋 Search Results:[/]")
            for i, (title, url) in enumerate(results_to_display, 1):
                # Shorten title if too long
                display_title = title if len(title) < 60 else title[:57] + "..."
                # Shorten URL if too long
                display_url = url if len(url) < 60 else url[:57] + "..."
                console.print(f"  [cyan]{i}[/]. {display_title}")
                console.print(f"     [dim]{display_url}[/]")

            console.print("")  # Blank line
    except Exception as e:
        # Show error for debugging
        console.print(f"[yellow]Note: Could not parse URLs ({str(e)})[/]")

    # Add note about result count to help LLM understand
    result_count = len(results_to_display) if results_to_display else 0
    if result_count > 0:
        result = f"[Found {result_count} results]\n\n{result}"

    console.print("[dim]  └─ ✓ Search completed[/]")
    return result


async def _analyze_image_url_tool(
    url: str, prompt: str = "Analyze this image in detail."
) -> str:
    """Analyze image from URL using Vision API

    Auto-selects:
    - OpenAI Vision (gpt-4o) for standard formats (fast, direct URL)
    - Future: Gemini for WebP/HEIC (download required)

    Args:
        url: Image URL
        prompt: Analysis prompt

    Returns:
        Image analysis result
    """
    from rich.console import Console

    from kagura.core.llm import LLMConfig
    from kagura.core.llm_openai import call_openai_vision_url
    from kagura.utils.media_detector import detect_media_type_from_url

    console = Console()
    console.print(f"[dim]🖼️  Analyzing image from URL: {url}...[/]")

    # Detect media type
    try:
        media_type, mime_type = await detect_media_type_from_url(url)
    except Exception as e:
        return f"Error detecting media type: {str(e)}"

    if media_type != "image":
        return f"Error: URL is not an image (detected: {media_type})"

    # Use OpenAI Vision for standard formats
    if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        console.print("[dim]Using OpenAI Vision API (direct URL)...[/]")
        try:
            config = LLMConfig(model="gpt-4o")
            result = await call_openai_vision_url(url, prompt, config)
            console.print("[dim]✓ Analysis complete[/]")
            return result.content
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    # WebP/HEIC - use Gemini SDK
    elif mime_type in ["image/webp", "image/heic", "image/heif"]:
        console.print(f"[dim]Using Gemini SDK ({mime_type})...[/]")
        try:
            from kagura.core.llm_gemini import call_gemini_direct

            config = LLMConfig(model="gemini/gemini-2.0-flash")
            result = await call_gemini_direct(
                prompt, config, media_url=url, media_type=mime_type
            )
            console.print("[dim]✓ Analysis complete[/]")
            return result.content
        except Exception as e:
            return f"Error analyzing with Gemini: {str(e)}"

    else:
        return f"Unsupported image format: {mime_type}"


async def _url_fetch_tool(url: str) -> str:
    """Fetch and extract text from a webpage.

    Args:
        url: URL to fetch

    Returns:
        Extracted text content
    """
    from rich.console import Console

    from kagura.utils.media_detector import is_image_url
    from kagura.web import WebScraper

    console = Console()

    # If it's an image URL, suggest using analyze_image_url instead
    if is_image_url(url):
        return (
            f"This appears to be an image URL: {url}\n"
            f"Use 'analyze {url}' to get image analysis instead of text extraction."
        )

    console.print(f"[dim]🌐 Fetching {url}...[/]")

    try:
        scraper = WebScraper()
        text = await scraper.fetch_text(url)

        chars = len(text)
        console.print(f"[dim]✓ Fetched {chars} characters[/]")
        return text

    except Exception as e:
        return f"Error fetching URL: {str(e)}"


# Shell Execution Tool
_shell_exec_already_called = False  # Prevent multiple calls per request


async def _shell_exec_tool_wrapper(command: str, user_intent: str = "") -> str:
    """Execute shell command with user confirmation and auto-retry on failure.

    Args:
        command: Shell command to execute
        user_intent: What the user is trying to accomplish (optional)

    Returns:
        Command output or error message
    """
    global _shell_exec_already_called

    from rich.console import Console

    from kagura.chat.shell_tool import shell_exec_tool

    console = Console()

    # CRITICAL FIX: Only allow ONE shell_exec call per request
    if _shell_exec_already_called:
        return (
            "⚠️ Shell command already executed in this request. "
            "Please wait for the first command to complete."
        )

    _shell_exec_already_called = True

    # Show command before execution (for user awareness)
    console.print(f"\n[yellow]💡 Executing:[/] [cyan]{command}[/cyan]")

    # Use shell_exec_tool with AUTO-APPROVE mode
    result = await shell_exec_tool(
        command=command,
        auto_confirm=True,  # Auto-approve (no confirmation prompt)
        interactive=False,  # No TTY (simpler, more reliable)
        enable_auto_retry=False,  # Disable auto-retry (let LLM handle failures)
        user_intent=user_intent or command,
    )

    # Display result immediately (don't wait for LLM processing)
    if result and not result.startswith("❌") and not result.startswith("🛑"):
        # Success - show output directly
        console.print(f"\n[dim]{result}[/dim]\n")
        # Return short summary to LLM - tell it NOT to repeat the output
        return (
            f"✓ Command '{command}' executed successfully.\n"
            f"Output ({len(result)} chars) has been displayed to the user.\n"
            f"DO NOT repeat or reformat the output.\n"
            f"Simply acknowledge completion or ask if user needs anything else."
        )
    else:
        # Error - return to LLM for handling
        return result


async def _shell_exec_with_options_wrapper(options: list[dict[str, str]]) -> str:
    """Execute shell command from multiple options with user selection.

    Args:
        options: List of command options, each with:
            - "command": The shell command to execute
            - "description": Short description of what it does

    Returns:
        Command output or error message

    Examples:
        >>> options = [
        ...     {"command": "pwd", "description": "current directory path"},
        ...     {"command": "ls -la", "description": "detailed listing"},
        ... ]
        >>> result = await _shell_exec_with_options_wrapper(options)
    """
    from kagura.chat.shell_tool import shell_exec_with_options

    return await shell_exec_with_options(
        options=options,
        auto_select=0,  # Ask user to select
        interactive=True,
    )


# YouTube Tools
async def _youtube_transcript_tool(video_url: str, lang: str = "en") -> str:
    """Get YouTube video transcript.

    Args:
        video_url: YouTube video URL
        lang: Language code (default: en, ja for Japanese)

    Returns:
        Video transcript text
    """
    from rich.console import Console

    # Use backward-compatible import (re-exported from kagura.tools)
    from kagura.tools import get_youtube_transcript

    console = Console()
    console.print(f"[dim]📺 Getting transcript for: {video_url}...[/]")

    result = await get_youtube_transcript(video_url, lang)

    console.print("[dim]✓ Transcript retrieved[/]")
    return result


async def _youtube_metadata_tool(video_url: str) -> str:
    """Get YouTube video metadata.

    Args:
        video_url: YouTube video URL

    Returns:
        JSON string with video metadata (title, author, duration, views, etc.)
    """
    from rich.console import Console

    # Use backward-compatible import (re-exported from kagura.tools)
    from kagura.tools import get_youtube_metadata

    console = Console()
    console.print(f"[dim]📺 Getting metadata for: {video_url}...[/]")

    result = await get_youtube_metadata(video_url)

    console.print("[dim]✓ Metadata retrieved[/]")
    return result


# =============================================================================
# Get chat tools from tool_registry (RFC-036 Phase 2)
# =============================================================================


def _get_chat_tools() -> list:
    """Get chat tools from tool_registry dynamically.

    Returns:
        List of tool functions for chat agent
    """
    # Get tools registered in kagura.chat.tools
    all_tools = tool_registry.get_all()

    # Chat-specific tools (registered via @tool in tools.py)
    chat_tool_names = [
        "file_read",
        "file_write",
        "file_search",
        "execute_python",
        "shell_exec",
        "brave_search",
        "url_fetch",
        "analyze_image_url",
        "youtube_transcript",
        "youtube_metadata",
    ]

    # Get tool functions from registry
    chat_tools = []
    for tool_name in chat_tool_names:
        if tool_name in all_tools:
            chat_tools.append(all_tools[tool_name])

    # Also add session-specific tools that aren't in registry yet
    # (e.g., shell_exec_with_options)
    chat_tools.append(_shell_exec_with_options_wrapper)

    return chat_tools


# =============================================================================
# Unified Chat Agent with All Capabilities (Claude Code-like)
# =============================================================================


@agent(
    model="gpt-5-mini",
    temperature=0.7,
    enable_memory=False,
    tools=_get_chat_tools(),  # Dynamic tool retrieval from tool_registry
)
async def chat_agent(user_input: str, memory: MemoryManager) -> str:
    """
    You are a helpful AI assistant with extensive capabilities, similar to Claude Code.
    Previous conversation context is available in your memory.

    User: {{ user_input }}

    Available tools - use them automatically when appropriate:

    File Operations:
    - file_read(file_path, prompt=None, mode="auto"): Read any file type
        - Text files: Direct reading
        - Images: Gemini Vision analysis
        - PDFs: Gemini document analysis
        - Audio: Gemini transcription
        - Video: Visual + audio analysis (mode: visual/audio/auto)
    - file_write(file_path, content): Write/modify files (auto-backup)
    - file_search(pattern, directory="."): Search files by pattern

    Code Execution:
    - execute_python(code): Execute Python code safely in sandbox

    Shell Commands:
    - shell_exec(command, user_intent=""): Execute with auto-retry on failure
        - CRITICAL: Call this tool ONLY ONCE per user request
        - Choose the SINGLE MOST appropriate command
        - DO NOT call shell_exec multiple times in one response
        - User confirms before execution
        - If fails, automatically suggests alternatives
        - Interactive mode: supports commands asking for input (apt-get, rm -i)
        - Security: blocks dangerous commands (sudo, rm -rf /, | sh)
        - Example: shell_exec("ls -la", user_intent="show directory")

    IMPORTANT RULE:
    - For "show directory": Use ONLY "ls -la" (NOT pwd + ls -la + ls)
    - For "current path": Use ONLY "pwd" (NOT pwd + ls)
    - Execute ONE command, wait for result, then respond to user
    - If user wants more info, they will ask in next message

    Web & Content:
    - brave_search(query, count=5): Search the web with Brave Search
      - CRITICAL: Call this tool ONLY ONCE per user request
      - Use the search results provided - do NOT search again
      - Only search again if user explicitly asks "search for X"
    - analyze_image_url(url, prompt="Analyze..."): Analyze image from URL
      - Direct URL support (no download) for jpg/png/gif/webp
      - Uses OpenAI Vision API (gpt-4o)
    - url_fetch(url): Fetch and extract text from webpages

    YouTube:
    - youtube_transcript(video_url, lang="en"): Get YouTube transcripts
    - youtube_metadata(video_url): Get YouTube video information

    Automatic tool usage guidelines:
    - File paths → use file_read (supports text, images, PDFs, audio, video)
    - Modify/create files → use file_write (auto-backup)
    - Execute code → use execute_python
    - Image URLs → use analyze_image_url (jpg/png/gif/webp)
    - General URLs → use url_fetch (webpage text)
    - YouTube links → ALWAYS use both youtube_transcript AND youtube_metadata
      - If transcript fails (not available), summarize using metadata only
      - Suggest using brave_search for additional information
    - Search requests → use brave_search ONCE, then use results

    CRITICAL RULES for brave_search:
    - Call brave_search ONLY ONCE per response (not multiple times in one answer)
    - Always call brave_search when user asks a search query,
      even if similar to past queries
    - Search results are cached automatically - you don't need to worry
      about repeat searches
    - Use the results provided by the tool - do NOT interpret cache messages
    - If results are insufficient, answer with available info

    For videos:
    - Default (mode="auto"): Both visual analysis + audio transcription
    - User can request specific mode if needed

    Best practices:
    - Create backups before modifying files
    - Show clear progress indicators
    - Provide helpful error messages
    - Suggest next steps

    Respond naturally in Japanese or English as appropriate. Use markdown formatting.
    """
    ...


class ChatSession:
    """
    Interactive chat session manager for Kagura AI.

    Provides a Claude Code-like REPL interface with:
    - Natural language conversations with automatic tool detection
    - File operations (read, write, search) with multimodal support
    - Code execution in secure Python sandbox
    - Web search and URL fetching
    - YouTube video summarization
    - Session management (/save, /load, /clear)
    - Custom agent support
    - Rich UI with markdown rendering
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        session_dir: Path | None = None,
    ):
        """
        Initialize chat session.

        Args:
            model: LLM model to use
            session_dir: Directory for session storage
        """
        self.console = Console()
        self.model = model
        self.session_dir = session_dir or get_data_dir() / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create memory manager
        # Disable compression for chat to preserve full conversation context
        self.memory = MemoryManager(
            user_id="system",
            agent_name="chat_session",
            persist_dir=self.session_dir / "memory",
            enable_compression=False,  # Keep full context for natural conversation
        )

        # Enhanced display
        self.display = EnhancedDisplay(self.console)

        # Create keybindings
        kb = self._create_keybindings()

        # Prompt session with history, completion, and keybindings
        # multiline=True but with custom Enter behavior:
        # - Enter on non-empty line: newline
        # - Enter on empty line: send
        history_file = self.session_dir / "chat_history.txt"
        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file)),
            completer=KaguraCompleter(self),
            enable_history_search=True,  # Ctrl+R
            key_bindings=kb,
            multiline=True,
        )

        # Session statistics tracking (v3.0)
        from .stats import SessionStats

        self.stats = SessionStats()

        # Load custom agents from ./agents directory (optional)
        self.custom_agents: dict[str, Any] = {}

        # Initialize router with intent-based matching (v3.0)
        # Intent-based is more reliable and doesn't require extra API calls
        self.router = AgentRouter(strategy="intent", confidence_threshold=0.3)

        self._load_custom_agents()
        self._register_personal_tools()

    def _create_keybindings(self) -> KeyBindings:
        """
        Create custom keybindings for chat session.

        Returns:
            KeyBindings with:
            - Enter once: New line
            - Enter twice (empty line): Send message
            - Ctrl+P/N: History navigation
        """
        kb = KeyBindings()

        # Ctrl+P: Previous command (like shell)
        @kb.add("c-p")
        def _previous_command(event: Any) -> None:
            event.current_buffer.history_backward()

        # Ctrl+N: Next command
        @kb.add("c-n")
        def _next_command(event: Any) -> None:
            event.current_buffer.history_forward()

        # Enter: Check if previous line is empty, if so send, otherwise newline
        @kb.add("enter")
        def _enter(event: Any) -> None:
            buffer = event.current_buffer
            # Check if current line is empty
            current_line = buffer.document.current_line
            if not current_line.strip():
                # Empty line, send message
                buffer.validate_and_handle()
            else:
                # Non-empty line, insert newline
                buffer.insert_text("\n")

        return kb

    def _load_custom_agents(self) -> None:
        """Load custom agents from ~/.kagura/agents/"""
        agents_dir = get_config_dir() / "agents"

        # Create directory if not exists
        agents_dir.mkdir(parents=True, exist_ok=True)

        if not agents_dir.is_dir():
            return

        agent_files = list(agents_dir.glob("*.py"))
        if not agent_files:
            return

        self.console.print(f"[dim]Loading custom agents from {agents_dir}...[/dim]")

        loaded_count = 0
        for agent_file in agent_files:
            try:
                # Load the module
                module_name = agent_file.stem
                spec = importlib.util.spec_from_file_location(module_name, agent_file)

                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Find agent functions
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if callable(attr) and asyncio.iscoroutinefunction(attr):
                        if hasattr(attr, "_is_agent"):
                            self.custom_agents[attr_name] = attr
                            loaded_count += 1
                            self.console.print(
                                f"[green]✓[/green] Loaded custom agent: "
                                f"[cyan]{attr_name}[/cyan] "
                                f"from [dim]{agent_file.name}[/dim]"
                            )

                            # Register with router if enabled
                            if self.router:
                                # Extract keywords from agent name and docstring
                                keywords = [attr_name.replace("_", " ")]
                                if attr.__doc__:
                                    # Add first line of docstring as keyword
                                    first_line = attr.__doc__.strip().split("\n")[0]
                                    keywords.append(first_line.lower())

                                self.router.register(attr, intents=keywords)

            except Exception as e:
                self.console.print(
                    f"[yellow]⚠[/yellow] Failed to load {agent_file.name}: {e}"
                )

        if loaded_count > 0:
            routing_msg = " (routing enabled)" if self.router else ""
            self.console.print(
                f"[green]Loaded {loaded_count} custom agent(s){routing_msg}[/green]\n"
            )

    def _register_personal_tools(self) -> None:
        """Register personal tools with semantic routing (v3.0)

        NOTE: Personal tools removed in v4.0 (#373).
        This method is kept for backward compatibility but does nothing.
        """
        # Personal tools removed in v4.0 - no-op for backward compatibility
        pass

    async def run(self) -> None:
        """Run interactive chat loop."""
        self.show_welcome()

        while True:
            try:
                # Get user input with formatted prompt
                prompt_text = FormattedText([("class:prompt", "\n[You] > ")])
                user_input = await self.prompt_session.prompt_async(prompt_text)

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Regular chat
                await self.chat(user_input)

            except (KeyboardInterrupt, EOFError):
                self.console.print("\n\n[yellow]Goodbye![/]")
                break

    async def chat(self, user_input: str) -> None:
        """
        Handle regular chat interaction.

        Args:
            user_input: User message
        """
        # Try routing to custom/personal agent first (if enabled)
        if self.router:
            try:
                # Get matched agents with confidence scores
                matches = self.router.get_matched_agents(user_input, top_k=1)

                if matches:
                    agent_func, confidence = matches[0]

                    # Check confidence threshold
                    if confidence >= self.router.confidence_threshold:
                        agent_name = agent_func.__name__

                        # Show which agent was selected (with confidence)
                        self.console.print(
                            f"[dim]🎯 Using {agent_name} agent "
                            f"(confidence: {confidence:.2f})[/]"
                        )

                        # Check if agent supports streaming
                        if hasattr(agent_func, "stream"):
                            # Hybrid: Tool progress prints + Live markdown streaming
                            from rich.live import Live

                            from kagura.core.llm_openai import set_progress_callback

                            # Set up progress callback for tool execution
                            def show_progress(msg: str) -> None:
                                """Show tool execution progress"""
                                self.console.print(f"[dim]{msg}[/]")

                            set_progress_callback(show_progress)

                            # Stream response with Live markdown rendering
                            accumulated = ""
                            first_chunk = False

                            async for chunk in agent_func.stream(user_input):
                                if not first_chunk:
                                    # Show [AI] when streaming actually starts
                                    self.console.print("\n[bold green][AI][/]")
                                    first_chunk = True

                                    # Start Live for markdown rendering
                                    live = Live(
                                        Markdown(""),
                                        console=self.console,
                                        refresh_per_second=10,
                                    )
                                    live.start()

                                accumulated += chunk
                                if first_chunk:
                                    live.update(Markdown(accumulated))

                            # Stop Live if started
                            if first_chunk:
                                live.stop()

                            # Show completion
                            self.console.print("\n[dim]  └─ ✓ Complete[/]")

                            # Clear callback
                            set_progress_callback(None)

                            # Add to memory
                            self.memory.add_message("user", user_input)
                            self.memory.add_message("assistant", accumulated)
                            return
                        else:
                            # Non-streaming execution
                            self.console.print("[dim]  └─ 💬 Processing...[/]\n")

                            # Execute the matched agent
                            result = await agent_func(user_input)

                            # Show completion
                            self.console.print("[dim]  └─ ✓ Complete[/]")

                            # Display result with Markdown formatting
                            self.console.print("\n[bold green][AI][/]")
                            self.display.display_response(str(result))

                            # Add to memory
                            self.memory.add_message("user", user_input)
                            self.memory.add_message("assistant", str(result))
                            return

            except NoAgentFoundError:
                # No matching agent, fall through to default chat
                pass
            except Exception as e:
                # Other errors in routing
                self.console.print(f"[dim]Routing error: {e}[/]")

        # No agent match or routing failed - use default chat

        # Add user message to memory
        self.memory.add_message("user", user_input)

        # Get AI response using unified chat_agent (with all tools)
        # Pass memory context manually since we disabled enable_memory in decorator
        self.console.print("[dim]💬 Generating response...[/]")

        # Get conversation context
        memory_context = await self.memory.get_llm_context()

        # Add current input to the context
        full_prompt = user_input
        if memory_context:
            # Prepend conversation history
            context_str = "\n\n[Previous conversation]\n"
            for msg in memory_context:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    context_str += f"User: {content}\n"
                elif role == "assistant":
                    context_str += f"Assistant: {content}\n"
            full_prompt = context_str + "\n[Current message]\n" + user_input

        # Reset shell_exec flag for this request
        from kagura.chat.tools import reset_shell_exec_flag

        reset_shell_exec_flag()

        # Create chat agent with current model (dynamic)
        current_chat_agent = agent(
            model=self.model,  # Use current model setting
            temperature=0.7,
            enable_memory=False,
            tools=_get_chat_tools(),  # Dynamic tool retrieval from tool_registry
        )(chat_agent)

        # Use dynamically configured agent
        response = await current_chat_agent(full_prompt, memory=self.memory)

        # Track stats if response has usage metadata (LLMResponse)
        # Note: response can be LLMResponse or str depending on implementation
        if hasattr(response, "usage") and hasattr(response, "duration"):
            from kagura.observability.pricing import calculate_cost

            # Type check: ensure these are the expected types
            usage_dict = getattr(response, "usage", {})
            duration_val = getattr(response, "duration", 0.0)

            if usage_dict and isinstance(usage_dict, dict):
                cost = calculate_cost(usage_dict, self.model)
                self.stats.track_call(
                    model=self.model,
                    usage=usage_dict,
                    duration=float(duration_val),
                    cost=cost,
                )

        # Extract content from response
        response_content = extract_response_content(response)

        # Add assistant message to memory
        self.memory.add_message("assistant", response_content)

        # Display response with enhanced formatting
        self.console.print("\n[bold green][AI][/]")
        self.display.display_response(response_content)

    async def handle_command(self, cmd: str) -> bool:
        """
        Handle slash commands.

        Args:
            cmd: Command string

        Returns:
            True to continue session, False to exit
        """
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command == "/help":
            self.show_help()
        elif command == "/clear":
            self.clear_history()
        elif command == "/save":
            await self.save_session(args)
        elif command == "/load":
            await self.load_session(args)
        elif command == "/model":
            self.handle_model_command(args)
        elif command == "/create":
            await self.handle_create_command(args)
        elif command == "/reload":
            await self.handle_reload_command()
        elif command == "/stats":
            await self.handle_stats_command(args)
        elif command == "/list":
            await self.handle_list_command(args)
        elif command == "/exit" or command == "/quit":
            return False
        elif command == "/agent" or command == "/agents":
            await self.handle_agent_command(args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/]")
            self.console.print(
                "\n[yellow]Available commands:[/]\n"
                "  [cyan]/help[/] - Show detailed help\n"
                "  [cyan]/create[/] - Create custom agent (v3.0)\n"
                "  [cyan]/reload[/] - Reload custom agents (v3.0)\n"
                "  [cyan]/stats[/] - Show token/cost stats (v3.0)\n"
                "  [cyan]/list[/] - List agents & tools (v3.0)\n"
                "  [cyan]/clear[/] - Clear conversation history\n"
                "  [cyan]/save[/] - Save current session\n"
                "  [cyan]/load[/] - Load saved session\n"
                "  [cyan]/model[/] - Switch LLM model\n"
                "  [cyan]/agent[/] - Use custom agents\n"
                "  [cyan]/exit[/] - Exit chat\n\n"
                "[dim]💡 Tip: For translation, summarization, and code review,\n"
                "   just ask naturally! (e.g., 'Translate this to Japanese')[/]"
            )

        return True

    def show_welcome(self) -> None:
        """Display welcome message."""
        # Check if user config exists
        try:
            from kagura.config import get_user_config

            user_config = get_user_config()
            has_config = bool(user_config.name or user_config.location)
        except Exception:
            has_config = False

        features = []
        features.append(
            "[bold magenta]🚀 Claude Code-like Experience - All Features Enabled[/]"
        )

        # Show init reminder if no config
        if not has_config:
            features.append("")
            features.append(
                "[yellow]💡 First time? Run [cyan]kagura init[/cyan] "
                "to personalize Personal Tools![/]"
            )
            features.append(
                "[dim]   (Set your name, location, preferences for better responses)[/]"
            )

        features.append("")
        features.append("[bold cyan]🎯 Personal Tools (v3.0 - NEW!):[/]")
        features.append("  [green]📰 daily_news[/] - Morning news briefing")
        features.append("  [green]🌤️  weather_forecast[/] - Weather updates")
        features.append("  [green]🍳 search_recipes[/] - Recipe suggestions")
        features.append("  [green]🎉 find_events[/] - Event finder")
        features.append("")
        features.append("[bold cyan]🛠️  Built-in Tools (Auto-detected):[/]")

        # Dynamic tool listing from tool_registry (RFC-036 Phase 3)
        all_tools = tool_registry.get_all()
        for tool_name, tool_func in sorted(all_tools.items()):
            # Get description from docstring
            doc = tool_func.__doc__ or "No description"
            first_line = doc.strip().split("\n")[0]
            # Truncate if too long
            desc = first_line if len(first_line) < 60 else first_line[:57] + "..."
            features.append(f"  [green]{tool_name}[/] - {desc}")
        features.append("")
        features.append("[dim]💡 Just ask naturally - tools are used automatically![/]")
        features.append(
            "[dim]   Examples: 'Get tech news', 'Weather in Tokyo', "
            "'Find recipes with chicken'[/]"
        )
        features.append("")
        features.append(f"[dim]Current model: {self.model}[/]")
        features.append("")
        features.append("[bold cyan]Commands:[/]")
        features.append("  [cyan]/help[/] - Show detailed help and examples")
        features.append("  [cyan]/create[/] - Create custom agent (v3.0 ✨)")
        features.append("  [cyan]/stats[/] - View token usage & costs (v3.0 ✨)")
        features.append("  [cyan]/model[/] - Switch LLM model")
        features.append("  [cyan]/clear[/] - Clear conversation history")
        features.append("  [cyan]/save[/] - Save current session for later")
        features.append("  [cyan]/load[/] - Load a saved session")
        if self.custom_agents:
            features.append(
                f"  [cyan]/agent[/] - Use custom agents "
                f"({len(self.custom_agents)} available 🎯)"
            )
        features.append("  [cyan]/reload[/] - Reload custom agents (v3.0)")
        features.append("  [cyan]/exit[/] - Exit chat")
        features.append("")
        features.append(
            "[dim]Shortcuts: Enter×2=Send, Ctrl+P/N=History, Tab=Complete[/]"
        )

        welcome = Panel(
            "[bold green]Welcome to Kagura Chat![/]\n\n" + "\n".join(features) + "\n",
            title="Kagura AI Chat",
            border_style="green",
        )
        self.console.print(welcome)

    def show_help(self) -> None:
        """Display help message."""
        help_text = """
# Kagura Chat - Your AI Assistant

## ⚡️ Quick Start
Just type naturally - AI auto-detects what you need:
```
今日のニュースは？        → daily_news (streaming ✨)
東京の天気              → weather_forecast (streaming ✨)
Read README.md         → file_read tool
```

**No commands needed** - Responses stream in real-time (no long waits!)

---

## 🎯 Personal Tools (v3.0 - NEW!)

Daily assistance with real-time streaming:

- 📰 **"Get tech news"** → `daily_news`
  - Latest headlines from any topic
  - Streams results as they're generated ✨

- 🌤️ **"Weather in Tokyo"** → `weather_forecast`
  - Current + forecast (today/tomorrow)
  - Tips (umbrella, clothing) ✨

- 🍳 **"Find chicken recipes"** → `search_recipes`
  - Recipe search by ingredients/cuisine
  - Cooking time, difficulty, links ✨

- 🎉 **"Events this weekend"** → `find_events`
  - Local event search
  - Music, sports, arts, food, festivals ✨

---

## 🛠️ Built-in Tools (Auto-detected)

**Files & Code**:
- Read files: `"Read src/main.py"` (text, images, PDFs, audio, video)
- Write files: `"Create a test file"` (auto-backup)
- Execute code: `"Run: print('Hello')"` (secure sandbox)
- Shell commands: `"Show directory"` → `ls -la` (auto-confirm)

**Web & Content**:
- Search: `"Search for Python best practices"` (Brave Search)
- Fetch URLs: `"Summarize https://..."` (webpage text)
- YouTube: `"Summarize https://youtube.com/watch?v=xxx"` (transcript + metadata)

**Multimodal (Gemini)**:
- Images: `"Analyze diagram.png"` (vision analysis)
- PDFs: `"Summarize report.pdf"` (document analysis)
- Audio: `"Transcribe meeting.mp3"` (speech-to-text)

---

## ⌨️ Commands & Shortcuts

**Session**:
- `/save [name]` - Save conversation
- `/load <name>` - Load saved session
- `/clear` - Clear history

**Agent Management** (v3.0 ✨):
- `/create agent <desc>` - Generate custom agent from natural language
- `/reload` - Reload agents from ~/.kagura/agents/
- `/agent` - List/execute custom agents

**Monitoring** (v3.0 ✨):
- `/stats` - Token usage & costs
- `/stats export <file>` - Export to JSON/CSV
- `/list` - List all agents & tools

**Other**:
- `/model [name]` - Switch LLM model
- `/help` - This help
- `/exit` - Quit

**Shortcuts**:
- `Enter×2` - Send message
- `Ctrl+P/N` - History navigation
- `Ctrl+R` - Search history
- `Tab` - Autocomplete

---

## 💡 Pro Tips

✨ **Real-time streaming** - Responses appear instantly (no 30-60s waits!)
🎯 **Auto-routing** - Personal tools are detected automatically
📊 **Cost tracking** - Use `/stats` to monitor token usage
🔧 **Custom agents** - Use `/create` to build your own agents
🌐 **Multimodal** - Images, PDFs, audio, video all supported
💾 **Session save** - `/save` to continue conversations later

**Common patterns**:
- File ops: Just say "Read X" or "Create Y" - no special syntax
- Translation: "Translate 'Hello' to Japanese" (not `/translate`)
- Code review: "Review this code: ..." (not `/review`)
- News/weather: Just ask - they're auto-detected with streaming ✨
"""
        self.console.print(Markdown(help_text))

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.memory.context.clear()
        self.console.print("[yellow]Conversation history cleared.[/]")

    async def save_session(self, name: str = "") -> None:
        """
        Save current session.

        Args:
            name: Session name (default: timestamp)
        """
        session_name = name or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_file = self.session_dir / f"{session_name}.json"

        # Get messages from memory (in LLM format - dict)
        messages = await self.memory.get_llm_context()

        # Save to file
        session_data = {
            "name": session_name,
            "created_at": datetime.now().isoformat(),
            "messages": messages,
        }

        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)

        self.console.print(f"[green]Session saved to: {session_file}[/]")

    async def load_session(self, name: str) -> None:
        """
        Load saved session.

        Args:
            name: Session name
        """
        session_file = self.session_dir / f"{name}.json"

        if not session_file.exists():
            self.console.print(f"[red]Session not found: {name}[/]")
            return

        # Load session data
        with open(session_file) as f:
            session_data = json.load(f)

        # Clear current memory
        self.memory.context.clear()

        # Restore messages
        messages = session_data.get("messages", [])
        for msg in messages:
            self.memory.add_message(msg["role"], msg["content"])

        self.console.print(
            f"[green]Session loaded: {session_data['name']} "
            f"({len(messages)} messages)[/]"
        )

    async def handle_agent_command(self, args: str) -> None:
        """
        Handle custom agent command.

        Args:
            args: "agent_name input_data" or empty to list agents
        """
        # If no args, list available agents
        if not args.strip():
            if not self.custom_agents:
                self.console.print(
                    "[yellow]No custom agents available.[/]\n"
                    "[dim]Custom agents are stored in ~/.kagura/agents/[/]\n"
                    "[dim]Create agents using natural language in chat.[/]"
                )
                return

            self.console.print("[bold cyan]Available Custom Agents:[/]")
            for name, agent_func in self.custom_agents.items():
                doc = agent_func.__doc__ or "No description"
                # Get first line of docstring
                first_line = doc.strip().split("\n")[0]
                self.console.print(f"  • [cyan]{name}[/]: {first_line}")

            self.console.print("\n[dim]Usage: /agent <name> <input>[/]")
            return

        # Parse agent name and input
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            self.console.print(
                "[red]Usage: /agent <name> <input>[/]\n"
                "[yellow]Tip: Use /agent to list available agents[/]"
            )
            return

        agent_name = parts[0]
        input_data = parts[1]

        # Find agent
        if agent_name not in self.custom_agents:
            self.console.print(
                f"[red]Agent not found: {agent_name}[/]\n[yellow]Available agents:[/]"
            )
            for name in self.custom_agents.keys():
                self.console.print(f"  • {name}")
            return

        # Execute agent
        agent_func = self.custom_agents[agent_name]
        self.console.print(f"\n[cyan]Executing {agent_name}...[/]")

        try:
            result = await agent_func(input_data)

            # Extract content from response
            result_content = extract_response_content(result)

            # Display result
            self.console.print(f"\n[bold green][{agent_name} Result][/]")
            self.console.print(Panel(result_content, border_style="green"))

            # Add to memory for context
            self.memory.add_message("user", f"/agent {agent_name} {input_data}")
            self.memory.add_message("assistant", result_content)

        except Exception as e:
            self.console.print(f"[red]Error executing {agent_name}: {e}[/]")

    def handle_model_command(self, args: str) -> None:
        """
        Handle model switching command.

        Args:
            args: Model name or empty to show current model
        """
        if not args.strip():
            # Check which API keys are available
            import os

            has_openai = bool(os.getenv("OPENAI_API_KEY"))
            has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
            has_google = bool(
                os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            )

            # Show current model and available options
            self.console.print(f"[cyan]Current model:[/] [bold]{self.model}[/]\n")
            self.console.print("[bold]Available models:[/]\n")

            # OpenAI models
            if has_openai:
                self.console.print("  [green]OpenAI:[/] (✓ API key set)")
                self.console.print("  • [green]gpt-5[/] - Best quality")
                self.console.print("  • [cyan]gpt-5-mini[/] - Balanced (default)")
                self.console.print("  • [yellow]gpt-5-nano[/] - Fastest")
                self.console.print("  • gpt-4o, gpt-4o-mini - Legacy\n")
            else:
                self.console.print(
                    "  [dim]OpenAI:[/] [yellow](⚠ OPENAI_API_KEY not set)[/]\n"
                )

            # Anthropic models
            if has_anthropic:
                self.console.print("  [green]Anthropic:[/] (✓ API key set)")
                self.console.print("  • claude-3-5-sonnet-20241022\n")
            else:
                self.console.print(
                    "  [dim]Anthropic:[/] [yellow](⚠ ANTHROPIC_API_KEY not set)[/]\n"
                )

            # Google models
            if has_google:
                self.console.print("  [green]Google Gemini:[/] (✓ API key set)")
                self.console.print("  • gemini/gemini-2.0-flash - Latest")
                self.console.print("  • gemini/gemini-1.5-pro-latest - Pro\n")
            else:
                self.console.print(
                    "  [dim]Google Gemini:[/] [yellow](⚠ GOOGLE_API_KEY not set)[/]\n"
                )

            self.console.print(
                "[dim]Usage: /model <model_name>[/]\n"
                "[dim]Example: /model gpt-5[/]\n"
                "[dim]Gemini example: /model gemini/gemini-2.0-flash[/]"
            )
            return

        new_model = args.strip()

        # Validate API key for the selected model
        import os

        model_lower = new_model.lower()
        missing_key = None

        if model_lower.startswith("gpt-") or model_lower.startswith("o1-"):
            if not os.getenv("OPENAI_API_KEY"):
                missing_key = "OPENAI_API_KEY"
        elif model_lower.startswith("claude-"):
            if not os.getenv("ANTHROPIC_API_KEY"):
                missing_key = "ANTHROPIC_API_KEY"
        elif model_lower.startswith("gemini/"):
            if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
                missing_key = "GOOGLE_API_KEY or GEMINI_API_KEY"

        if missing_key:
            self.console.print(
                f"[red]⚠ Error: {missing_key} not set[/]\n"
                f"[yellow]Cannot use model '{new_model}' without API key.[/]\n\n"
                f"[dim]Set the environment variable:[/]\n"
                f"  export {missing_key.split(' or ')[0]}=your-api-key\n"
            )
            return

        old_model = self.model
        self.model = new_model

        self.console.print(
            f"[green]✓ Model changed:[/] "
            f"[dim]{old_model}[/] → [cyan]{new_model}[/]\n"
            "[dim]Conversation history preserved.[/]"
        )

    async def handle_create_command(self, args: str) -> None:
        """Handle /create agent command (v3.0 feature)

        Generate custom agent from natural language description.

        Args:
            args: Agent description (e.g., "agent that summarizes tech news")
        """
        # Parse "agent <description>" or just "<description>"
        description = args.strip()
        if description.lower().startswith("agent "):
            description = description[6:].strip()

        if not description:
            self.console.print(
                "[yellow]Usage: /create agent <description>[/]\n"
                "[dim]Example: /create agent that summarizes morning tech news[/]"
            )
            return

        try:
            # Import SelfImprovingMetaAgent (RFC-005)
            from kagura.meta.self_improving import SelfImprovingMetaAgent

            # Show progress
            self.console.print(
                f"\n[dim]💬 Generating agent from:[/] [cyan]{description}[/]"
            )

            # Generate agent
            meta_agent = SelfImprovingMetaAgent(model=self.model)
            code, errors = await meta_agent.generate_with_retry(
                description, validate=True
            )

            # Extract agent name from code
            import re

            match = re.search(r"^async def (\w+)\(", code, re.MULTILINE)
            agent_name = match.group(1) if match else "custom_agent"

            # Show result
            self.console.print(f"\n[green]✓ Agent created: {agent_name}[/]")
            if errors:
                self.console.print(
                    f"[yellow]Note: Fixed {len(errors)} error(s) automatically[/]"
                )

            # Display code preview
            self.console.print(Panel(code, title="Generated Code", border_style="cyan"))

            # Confirm save
            self.console.print(
                "\n[yellow]Save to ~/.kagura/agents/? (y/n):[/] ", end=""
            )
            confirm = input().strip().lower()

            if confirm == "y":
                # Save to file
                agents_dir = get_config_dir() / "agents"
                agents_dir.mkdir(parents=True, exist_ok=True)
                agent_file = agents_dir / f"{agent_name}.py"

                agent_file.write_text(code, encoding="utf-8")

                # Reload agents
                self._load_custom_agents()

                self.console.print(
                    f"[green]✓ Saved and loaded:[/] [cyan]{agent_name}[/]\n"
                    f"[dim]Location: {agent_file}[/]"
                )
            else:
                self.console.print("[yellow]Cancelled. Agent not saved.[/]")

        except Exception as e:
            self.console.print(f"[red]Error creating agent: {e}[/]")

    async def handle_reload_command(self) -> None:
        """Handle /reload command (v3.0 feature)

        Reload custom agents from ~/.kagura/agents/
        """
        self.console.print("[dim]Reloading custom agents...[/]")

        # Clear current agents
        self.custom_agents.clear()

        # Reload
        self._load_custom_agents()

        count = len(self.custom_agents)
        if count > 0:
            self.console.print(f"[green]✓ Reloaded {count} agent(s)[/]")
        else:
            self.console.print("[yellow]No custom agents found in ~/.kagura/agents/[/]")

    async def handle_stats_command(self, args: str) -> None:
        """Handle /stats command (v3.0 feature)

        Display session statistics (token usage, costs).

        Args:
            args: Optional subcommand:
                - empty: Display stats table
                - "export <file>": Export to JSON or CSV
        """
        if not args.strip():
            # Display stats table
            from rich.table import Table

            summary = self.stats.get_summary()

            if summary["total_calls"] == 0:
                self.console.print("[yellow]No LLM calls yet in this session.[/]")
                return

            # Create table
            table = Table(title="Session Statistics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            # Total stats
            table.add_row("Total Calls", str(summary["total_calls"]))
            table.add_row("Total Tokens", f"{summary['total_tokens']:,}")
            table.add_row("Total Cost", f"${summary['total_cost']:.4f}")
            duration_min = int(summary["duration"] // 60)
            duration_sec = int(summary["duration"] % 60)
            table.add_row("Session Duration", f"{duration_min}m {duration_sec}s")

            self.console.print("\n")
            self.console.print(table)

            # Model breakdown
            if summary["models"]:
                self.console.print("\n[bold cyan]Breakdown by Model:[/]")
                for model, stats in summary["models"].items():
                    self.console.print(
                        f"  • [cyan]{model}[/]: "
                        f"{stats['calls']} calls, "
                        f"{stats['tokens']:,} tokens, "
                        f"${stats['cost']:.4f}"
                    )

            self.console.print(
                "\n[dim]Tip: Use '/stats export <file>' to export to JSON or CSV[/]\n"
            )

        elif args.startswith("export "):
            # Export stats
            file_path = args[7:].strip()

            if not file_path:
                self.console.print(
                    "[yellow]Usage: /stats export <file>[/]\n"
                    "[dim]Example: /stats export stats.json or stats.csv[/]"
                )
                return

            try:
                if file_path.endswith(".json"):
                    self.stats.export_json(file_path)
                    self.console.print(f"[green]✓ Exported to {file_path}[/]")
                elif file_path.endswith(".csv"):
                    self.stats.export_csv(file_path)
                    self.console.print(f"[green]✓ Exported to {file_path}[/]")
                else:
                    self.console.print(
                        "[yellow]Please specify .json or .csv file extension[/]"
                    )
            except Exception as e:
                self.console.print(f"[red]Error exporting stats: {e}[/]")

        else:
            self.console.print(
                "[yellow]Unknown subcommand.[/]\n"
                "[dim]Usage: /stats or /stats export <file>[/]"
            )

    async def handle_list_command(self, args: str) -> None:
        """Handle /list command (v3.0 feature)

        List available agents and tools.

        Args:
            args: Optional filter ("agents", "tools", or empty for all)
        """
        filter_type = args.strip().lower()

        # Personal Tools
        if not filter_type or filter_type == "agents":
            self.console.print("\n[bold cyan]📋 Personal Tools (v3.0):[/]")
            personal_tools = [
                ("daily_news", "Morning news briefing"),
                ("weather_forecast", "Weather updates"),
                ("search_recipes", "Recipe suggestions"),
                ("find_events", "Event finder"),
            ]
            for name, desc in personal_tools:
                self.console.print(f"  • [cyan]{name}[/] - {desc}")

        # Custom Agents
        if (not filter_type or filter_type == "agents") and self.custom_agents:
            self.console.print("\n[bold cyan]🎯 Custom Agents:[/]")
            for name, agent_func in self.custom_agents.items():
                doc = agent_func.__doc__ or "No description"
                first_line = doc.strip().split("\n")[0]
                self.console.print(f"  • [cyan]{name}[/] - {first_line}")

        # Built-in Tools (dynamic from tool_registry)
        if not filter_type or filter_type == "tools":
            self.console.print("\n[bold cyan]🛠️  Built-in Tools:[/]")

            # Get tools from tool_registry dynamically (RFC-036 Phase 3)
            all_tools = tool_registry.get_all()
            for tool_name, tool_func in sorted(all_tools.items()):
                # Get description from docstring
                doc = tool_func.__doc__ or "No description"
                first_line = doc.strip().split("\n")[0]
                # Truncate if too long
                desc = first_line if len(first_line) < 50 else first_line[:47] + "..."
                self.console.print(f"  • [green]{tool_name}[/] - {desc}")

        self.console.print(
            "\n[dim]💡 Just ask naturally - agents/tools are auto-detected![/]"
        )
        self.console.print(
            "[dim]   Examples: 'Get news', 'Weather in Tokyo', 'Find recipes'[/]\n"
        )
