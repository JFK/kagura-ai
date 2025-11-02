"""
Chat tools registered with @tool decorator for tool_registry integration.

This module converts session.py's hardcoded tool functions into @tool-decorated
functions that are automatically registered with the global tool_registry.

This enables:
- Dynamic tool discovery in ChatSession
- MCP access to chat tools
- Unified tool management across all interfaces

Related: RFC-036 Phase 1
"""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from rich.console import Console

from kagura import tool
from kagura.core.executor import CodeExecutor
from kagura.loaders.file_types import FileType, detect_file_type, is_multimodal_file

# =============================================================================
# File Operation Tools
# =============================================================================


@tool
async def file_read(
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
                    audio_result = await _video_extract_audio(file_path)

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
                    audio_result = await _video_extract_audio(file_path)
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


@tool
async def file_write(file_path: str, content: str) -> str:
    """Write content to a local file.

    Args:
        file_path: Path to the file to write
        content: Content to write

    Returns:
        Success message or error
    """
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


@tool
async def file_search(pattern: str, directory: str = ".") -> str:
    """Search for files matching pattern.

    Args:
        pattern: File name pattern (supports wildcards)
        directory: Directory to search in

    Returns:
        List of matching file paths
    """
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


# =============================================================================
# Code Execution Tool
# =============================================================================


@tool
async def execute_python(code: str) -> str:
    """Execute Python code safely.

    Args:
        code: Python code to execute

    Returns:
        Execution result (stdout, stderr, or error)
    """
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


# =============================================================================
# Shell Execution Tool
# =============================================================================

# Global flag to prevent multiple shell_exec calls per request
_shell_exec_already_called = False


@tool
async def shell_exec(command: str, user_intent: str = "") -> str:
    """Execute shell command with user confirmation and auto-retry on failure.

    Args:
        command: Shell command to execute
        user_intent: What the user is trying to accomplish (optional)

    Returns:
        Command output or error message
    """
    global _shell_exec_already_called

    from kagura.chat.shell_tool import shell_exec_tool

    console = Console()

    # CRITICAL: Only allow ONE shell_exec call per request
    if _shell_exec_already_called:
        return (
            "⚠️ Shell command already executed in this request. "
            "Please wait for the first command to complete."
        )

    _shell_exec_already_called = True

    # Show command before execution
    console.print(f"\n[yellow]💡 Executing:[/] [cyan]{command}[/cyan]")

    # Use shell_exec_tool with AUTO-APPROVE mode
    result = await shell_exec_tool(
        command=command,
        auto_confirm=True,
        interactive=False,
        enable_auto_retry=False,
        user_intent=user_intent or command,
    )

    # Display result immediately
    if result and not result.startswith("❌") and not result.startswith("🛑"):
        # Success - show output directly
        console.print(f"\n[dim]{result}[/dim]\n")
        return (
            f"✓ Command '{command}' executed successfully.\n"
            f"Output ({len(result)} chars) has been displayed to the user.\n"
            f"DO NOT repeat or reformat the output.\n"
            f"Simply acknowledge completion or ask if user needs anything else."
        )
    else:
        # Error - return to LLM for handling
        return result


def reset_shell_exec_flag() -> None:
    """Reset the shell_exec flag for new request"""
    global _shell_exec_already_called
    _shell_exec_already_called = False


# =============================================================================
# Web & Content Tools
# =============================================================================


@tool
async def brave_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API.

    Args:
        query: Search query
        count: Number of results (default: 5)

    Returns:
        Formatted search results
    """
    import re

    from kagura.tools import brave_web_search

    console = Console()
    console.print(f"[dim]  └─ 🔍 Brave Search: {query}...[/]")

    # Call search (returns formatted text)
    result = await brave_web_search(query, count=count)

    # Parse and display results with titles and URLs
    try:
        lines = result.split("\n")
        results_to_display = []

        current_title = None
        for line in lines:
            # Title lines (numbered)
            match = re.match(r"^(\d+)\.\s+(.+)$", line)
            if match:
                current_title = match.group(2).strip()
            # URL lines (indented)
            elif current_title and line.strip().startswith("http"):
                url = line.strip()
                results_to_display.append((current_title, url))
                current_title = None

        if results_to_display:
            console.print("\n[dim]📋 Search Results:[/]")
            for i, (title, url) in enumerate(results_to_display, 1):
                display_title = title if len(title) < 60 else title[:57] + "..."
                display_url = url if len(url) < 60 else url[:57] + "..."
                console.print(f"  [cyan]{i}[/]. {display_title}")
                console.print(f"     [dim]{display_url}[/]")
            console.print("")

    except Exception as e:
        console.print(f"[yellow]Note: Could not parse URLs ({str(e)})[/]")

    # Add result count
    result_count = len(results_to_display) if results_to_display else 0
    if result_count > 0:
        result = f"[Found {result_count} results]\n\n{result}"

    console.print("[dim]  └─ ✓ Search completed[/]")
    return result


@tool
async def url_fetch(url: str) -> str:
    """Fetch and extract text from a webpage.

    Args:
        url: URL to fetch

    Returns:
        Extracted text content
    """
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


@tool
async def analyze_image_url(
    url: str, prompt: str = "Analyze this image in detail."
) -> str:
    """Analyze image from URL using Vision API.

    Auto-selects:
    - OpenAI Vision (gpt-4o) for standard formats
    - Gemini for WebP/HEIC

    Args:
        url: Image URL
        prompt: Analysis prompt

    Returns:
        Image analysis result
    """
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


# =============================================================================
# YouTube Tools
# =============================================================================


@tool
async def youtube_transcript(video_url: str, lang: str = "en") -> str:
    """Get YouTube video transcript.

    Args:
        video_url: YouTube video URL
        lang: Language code (default: en, ja for Japanese)

    Returns:
        Video transcript text
    """
    from kagura.tools import get_youtube_transcript

    console = Console()
    console.print(f"[dim]📺 Getting transcript for: {video_url}...[/]")

    result = await get_youtube_transcript(video_url, lang)

    console.print("[dim]✓ Transcript retrieved[/]")
    return result


@tool
async def youtube_metadata(video_url: str) -> str:
    """Get YouTube video metadata.

    Args:
        video_url: YouTube video URL

    Returns:
        JSON string with video metadata (title, author, duration, views, etc.)
    """
    from kagura.tools import get_youtube_metadata

    console = Console()
    console.print(f"[dim]📺 Getting metadata for: {video_url}...[/]")

    result = await get_youtube_metadata(video_url)

    console.print("[dim]✓ Metadata retrieved[/]")
    return result


# =============================================================================
# Helper Functions (Internal)
# =============================================================================


async def _video_extract_audio(video_path: str, output_path: str | None = None) -> str:
    """Extract audio from video file using ffmpeg (internal helper).

    Args:
        video_path: Path to video file
        output_path: Output audio file path (default: same name .mp3)

    Returns:
        Success message with audio path or error message
    """
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
