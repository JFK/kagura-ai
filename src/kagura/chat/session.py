"""
Interactive Chat Session for Kagura AI
"""

import asyncio
import importlib.util
import json
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
from kagura.core.memory import MemoryManager
from kagura.routing import AgentRouter, NoAgentFoundError

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
async def _brave_search_tool(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API (high-quality results).

    Args:
        query: Search query
        count: Number of results (default: 5)

    Returns:
        JSON with search results
    """
    from rich.console import Console

    from kagura.tools.brave_search import brave_web_search

    console = Console()
    console.print(f"[dim]🔍 Brave Search: {query}...[/]")

    result = await brave_web_search(query, count=count)

    console.print("[dim]✓ Search completed[/]")
    return result


async def _web_search_tool(query: str) -> str:
    """Search the web for information (fallback to DuckDuckGo).

    Args:
        query: Search query

    Returns:
        Formatted search results
    """
    from rich.console import Console

    from kagura.web.decorators import web_search

    console = Console()
    console.print(f"[dim]🌐 Searching the web for: {query}...[/]")

    result = await web_search(query)

    console.print("[dim]✓ Web search completed[/]")
    return result


async def _url_fetch_tool(url: str) -> str:
    """Fetch and extract text from a webpage.

    Args:
        url: URL to fetch

    Returns:
        Extracted text content
    """
    from rich.console import Console

    from kagura.web import WebScraper

    console = Console()
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


async def _shell_exec_with_options_wrapper(
    options: list[dict[str, str]]
) -> str:
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

    from kagura.tools.youtube import get_youtube_transcript

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

    from kagura.tools.youtube import get_youtube_metadata

    console = Console()
    console.print(f"[dim]📺 Getting metadata for: {video_url}...[/]")

    result = await get_youtube_metadata(video_url)

    console.print("[dim]✓ Metadata retrieved[/]")
    return result


# =============================================================================
# Unified Chat Agent with All Capabilities (Claude Code-like)
# =============================================================================


@agent(
    model="gpt-5-mini",
    temperature=0.7,
    enable_memory=False,
    tools=[
        # File operations
        _file_read_tool,
        _file_write_tool,
        _file_search_tool,
        # Code execution
        _execute_python_tool,
        # Shell execution
        _shell_exec_tool_wrapper,  # Single command with auto-retry
        _shell_exec_with_options_wrapper,  # Multiple options for user to choose
        # Web & Content
        _brave_search_tool,  # Primary search (high-quality)
        _web_search_tool,  # Fallback search (DuckDuckGo)
        _url_fetch_tool,
        # YouTube
        _youtube_transcript_tool,
        _youtube_metadata_tool,
    ],
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
    - brave_search(query, count=5): Search the web with Brave (high-quality, primary)
    - web_search(query): Search the web with DuckDuckGo (fallback)
    - url_fetch(url): Fetch and extract text from webpages

    YouTube:
    - youtube_transcript(video_url, lang="en"): Get YouTube transcripts
    - youtube_metadata(video_url): Get YouTube video information

    Automatic tool usage guidelines:
    - File paths → use file_read (supports text, images, PDFs, audio, video)
    - Modify/create files → use file_write (auto-backup)
    - Execute code → use execute_python
    - URLs → use url_fetch
    - YouTube links → ALWAYS use both youtube_transcript AND youtube_metadata
      - If transcript fails (not available), summarize using metadata only
      - Suggest using web_search for additional information
    - Search requests → use web_search

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
        self.session_dir = session_dir or Path.home() / ".kagura" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create memory manager
        # Disable compression for chat to preserve full conversation context
        self.memory = MemoryManager(
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

        # Load custom agents from ./agents directory (optional)
        self.custom_agents: dict[str, Any] = {}
        self.router = AgentRouter()
        self._load_custom_agents()

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
        agents_dir = Path.home() / ".kagura" / "agents"

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
        # Try routing to custom agent first (if enabled)
        if self.router and self.custom_agents:
            try:
                self.console.print("[dim]🔍 Checking for matching agent...[/]")
                result = await self.router.route(user_input)

                # Found a custom agent match
                self.console.print("[dim]✓ Using custom agent for this request[/]\n")
                self.console.print("[bold green][AI][/]")
                self.console.print(Panel(str(result), border_style="green"))

                # Add to memory
                self.memory.add_message("user", user_input)
                self.memory.add_message("assistant", str(result))
                return

            except NoAgentFoundError:
                # No matching agent, fall through to default chat
                self.console.print(
                    "[dim]No matching custom agent, using default chat[/]"
                )

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
        global _shell_exec_already_called
        _shell_exec_already_called = False

        # Create chat agent with current model (dynamic)
        current_chat_agent = agent(
            model=self.model,  # Use current model setting
            temperature=0.7,
            enable_memory=False,
            tools=[
                _file_read_tool,
                _file_write_tool,
                _file_search_tool,
                _execute_python_tool,
                _shell_exec_tool_wrapper,
                _shell_exec_with_options_wrapper,
                _brave_search_tool,
                _web_search_tool,
                _url_fetch_tool,
                _youtube_transcript_tool,
                _youtube_metadata_tool,
            ],
        )(chat_agent)

        # Use dynamically configured agent
        response = await current_chat_agent(full_prompt, memory=self.memory)

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
        elif command == "/exit" or command == "/quit":
            return False
        elif command == "/agent" or command == "/agents":
            await self.handle_agent_command(args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/]")
            self.console.print(
                "\n[yellow]Available commands:[/]\n"
                "  [cyan]/help[/] - Show detailed help\n"
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
        features = []
        features.append(
            "[bold magenta]🚀 Claude Code-like Experience - All Features Enabled[/]"
        )
        features.append("")
        features.append("[bold cyan]🛠️  Available Tools (Auto-detected):[/]")
        features.append(
            "  [green]📄 file_read[/] - Read files (text, image, PDF, audio, video)"
        )
        features.append("  [green]📝 file_write[/] - Write/modify files (auto-backup)")
        features.append("  [green]🔍 file_search[/] - Find files by pattern")
        features.append("  [green]🐍 execute_python[/] - Run Python code safely")
        features.append(
            "  [green]💻 shell_exec[/] - Execute shell commands (confirmation)"
        )
        features.append("  [green]🔍 brave_search[/] - Brave Search (high-quality)")
        features.append("  [green]🌐 web_search[/] - DuckDuckGo (fallback)")
        features.append("  [green]🌐 url_fetch[/] - Fetch webpage content")
        features.append("  [green]📺 youtube_transcript[/] - Get YouTube transcripts")
        features.append("  [green]📺 youtube_metadata[/] - Get YouTube info")
        features.append("")
        features.append("[dim]💡 Just ask naturally - tools are used automatically![/]")
        features.append(
            "[dim]   Examples: 'Read main.py', 'Analyze image.png', 'Summarize https://...'[/]"
        )
        features.append("")
        features.append(f"[dim]Current model: {self.model}[/]")
        features.append("")
        features.append("[bold cyan]Commands:[/]")
        features.append("  [cyan]/help[/] - Show detailed help and examples")
        features.append("  [cyan]/clear[/] - Clear conversation history")
        features.append("  [cyan]/save[/] - Save current session for later")
        features.append("  [cyan]/load[/] - Load a saved session")
        features.append("  [cyan]/model[/] - Switch LLM model")
        if self.custom_agents:
            features.append(
                f"  [cyan]/agent[/] - Use custom agents "
                f"({len(self.custom_agents)} available 🎯)"
            )
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
# Kagura Chat - Claude Code-like Experience

## 💬 Chat Naturally
Just type your message. The AI will automatically use the right tools based on
your request.

**Example conversations:**
- "Read src/main.py and explain what it does"
- "Show me the current directory" → uses shell_exec (ls -la)
- "Find all Python files" → uses shell_exec (find . -name "*.py")
- "Analyze this image: diagram.png"
- "Summarize this PDF: report.pdf"
- "Extract audio from video.mp4 and transcribe it"
- "Search the web for Python best practices"
- "Summarize this YouTube video: https://youtube.com/watch?v=xxx"
- "Write a test file for this function"
- "Execute this code: print([x**2 for x in range(10)])"
- "Translate this to Japanese: Hello World"
- "Review this code and suggest improvements"

## 🛠️ Available Tools (Auto-detected)

### File Operations
- **file_read** - Read any file type (text, images, PDFs, audio, video)
- **file_write** - Write/modify files with automatic backups
- **file_search** - Find files by name pattern

### Code Execution
- **execute_python** - Execute Python code in a secure sandbox

### Shell Commands
- **shell_exec** - Execute shell commands with user confirmation
  - Interactive mode for commands that ask for input
  - Security controls (blocks dangerous commands)
  - Examples: ls, git status, find, grep

### Web & Content
- **web_search** - Search the web (Brave or DuckDuckGo)
- **url_fetch** - Fetch and extract text from webpages

### YouTube
- **youtube_transcript** - Get video transcripts
- **youtube_metadata** - Get video information (title, views, etc.)

### Multimodal Analysis (Gemini)
- **Images** - Vision analysis and description
- **PDFs** - Document analysis and summarization
- **Audio** - Transcription to text
- **Video** - Visual analysis + audio transcription

## ⌨️ Keyboard Shortcuts
- **Enter** - New line (or send message on empty line)
- **Enter twice** - Send message
- **Tab** - Autocomplete commands
- **Ctrl+P** - Previous command (history backward)
- **Ctrl+N** - Next command (history forward)
- **Ctrl+R** - Search command history

## 📝 Commands

### Session Management
- `/save [name]` - Save current conversation session
  - Example: `/save project-discussion`
  - Sessions are saved to: ~/.kagura/sessions/
  - Saved sessions can be loaded later with `/load`

- `/load <name>` - Load a previously saved session
  - Example: `/load project-discussion`
  - Restores full conversation history

- `/clear` - Clear conversation history
  - Removes all messages from current session
  - Useful for starting fresh while keeping the chat open

### Custom Agents
- `/agent` or `/agents` - List available custom agents
- `/agent <name> <input>` - Execute a custom agent
  - Example: `/agent data_analyzer sales.csv`
  - Custom agents are loaded from ~/.kagura/agents/ directory

### Model Management
- `/model` - Show current model and available options
- `/model <name>` - Switch to different model
  - Example: `/model gpt-5`
  - Models: gpt-5, gpt-5-mini, gpt-5-nano, claude-3.5-sonnet, etc.
  - Conversation history is preserved when switching

### Other
- `/help` - Show this help message
- `/exit` or `/quit` - Exit the chat session

## 💡 Tips

### No need for special commands!
You don't need `/translate`, `/summarize`, or `/review` anymore.
Just ask naturally:
- ❌ `/translate Hello to ja` → ✅ "Translate 'Hello' to Japanese"
- ❌ `/summarize long text...` → ✅ "Summarize this text: ..."
- ❌ `/review def foo()...` → ✅ "Review this code: def foo()..."

### File operations are automatic
- "Read README.md" → uses file_read tool
- "Create a test file" → uses file_write tool
- "Find all Python files" → uses file_search tool

### Multimodal is built-in
- "Analyze screenshot.png" → uses Gemini Vision
- "What's in this PDF?" → uses Gemini document analysis
- "Transcribe meeting.mp3" → uses Gemini audio transcription

## 📊 Monitoring
Use `kagura monitor --agent chat_session` to view:
- Conversation history
- Tools used
- Token usage
- Cost breakdown
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
                f"[red]Agent not found: {agent_name}[/]\n"
                "[yellow]Available agents:[/]"
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
            # Show current model and available options
            self.console.print(
                f"[cyan]Current model:[/] [bold]{self.model}[/]\n\n"
                "[bold]Available models:[/]\n"
                "  • [green]gpt-5[/] - Best quality, cheaper than gpt-4o\n"
                "  • [cyan]gpt-5-mini[/] - Balanced (recommended default)\n"
                "  • [yellow]gpt-5-nano[/] - Fastest, cheapest\n"
                "  • gpt-4o - Legacy (more expensive)\n"
                "  • gpt-4o-mini - Legacy\n"
                "  • claude-3.5-sonnet - Anthropic Claude\n"
                "  • gemini/gemini-2.0-flash-exp - Google Gemini\n\n"
                "[dim]Usage: /model <model_name>[/]\n"
                "[dim]Example: /model gpt-5[/]"
            )
            return

        new_model = args.strip()
        old_model = self.model
        self.model = new_model

        self.console.print(
            f"[green]✓ Model changed:[/] "
            f"[dim]{old_model}[/] → [cyan]{new_model}[/]\n"
            "[dim]Conversation history preserved.[/]"
        )
