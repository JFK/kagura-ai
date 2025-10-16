"""
Two-column Terminal User Interface for Kagura Chat.

Provides split-screen layout with:
- Top: Output area (scrollable, read-only)
- Bottom: Input area (multiline, expandable 3-10 lines)
- Status bar with shortcuts
"""

from pathlib import Path
from typing import Any, Optional

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import (
    D,
    HSplit,
    Layout,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.widgets import TextArea
from rich.console import Console

from kagura.core.memory import MemoryManager

from .session import chat_agent
from .utils import extract_response_content


class TwoColumnChatUI:
    """Two-column chat interface with split input/output areas.

    Layout:
    ┌─────────────────────────────────────────┐
    │ [Output Area - Scrollable]              │
    │                                         │
    │ [You] > Hello                           │
    │ [AI] Hi there!                          │
    │                                         │
    │ (auto-scroll, read-only)                │
    ├─────────────────────────────────────────┤
    │ [Input Area - Multiline, 3-10 lines]    │
    │ [You] > _                               │
    │                                         │
    │ Enter×2=Send | Ctrl+P/N=History         │
    └─────────────────────────────────────────┘
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        session_dir: Optional[Path] = None,
    ):
        """Initialize 2-column chat UI.

        Args:
            model: LLM model to use
            session_dir: Directory for session storage
        """
        self.model = model
        self.session_dir = session_dir or Path.home() / ".kagura" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Memory manager
        self.memory = MemoryManager(
            agent_name="chat_session",
            persist_dir=self.session_dir / "memory",
            enable_compression=False,
        )

        # Rich console for rendering
        self.console = Console(record=True)

        # Output area (read-only, scrollable)
        self.output_area = TextArea(
            text=self._render_welcome(),
            read_only=True,
            scrollbar=True,
            focusable=False,
            wrap_lines=True,
        )

        # Input area (multiline, expandable)
        self.input_buffer = Buffer(
            multiline=True,
            history=InMemoryHistory(),
            on_text_insert=self._on_text_insert,
        )

        self.input_area = Window(
            content=BufferControl(buffer=self.input_buffer),
            height=D(min=3, max=10),  # 3-10 lines, auto-expand
        )

        # Status bar
        status_text = (
            " Enter×2=Send | Ctrl+P/N=History | Ctrl+C=Cancel | /exit=Quit "
        )
        self.status_bar = Window(
            content=FormattedTextControl(text=status_text),
            height=1,
            style="reverse",
        )

        # Key bindings
        kb = self._create_key_bindings()

        # Layout
        layout = Layout(
            HSplit([
                self.output_area,  # Top: output
                Window(height=1, char="─"),  # Separator
                self.input_area,  # Bottom: input
                self.status_bar,  # Status bar
            ])
        )

        # Application
        self.app = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
        )

        # Track if user is scrolling up (disable auto-scroll)
        self.auto_scroll_enabled = True

    def _render_welcome(self) -> str:
        """Render welcome message."""
        return """╔══════════════════════════════════════════════════════════════════╗
║           Welcome to Kagura Chat (2-Column UI)                  ║
╚══════════════════════════════════════════════════════════════════╝

🚀 Features:
  • Shell commands with auto-correction
  • File operations (read, write, search)
  • Code execution
  • Web search & YouTube analysis

💡 Examples:
  • "Show current directory"
  • "Find all Python files"
  • "Read README.md"
  • "Search for Python best practices"

⌨️  Shortcuts:
  • Enter×2 (or Ctrl+J) = Send message
  • Ctrl+P/N = History navigation
  • Ctrl+C = Cancel input
  • /exit = Quit chat

───────────────────────────────────────────────────────────────────

"""

    def _create_key_bindings(self) -> KeyBindings:
        """Create key bindings for the application."""
        kb = KeyBindings()

        @kb.add("enter")
        def _(event: Any) -> None:
            """Handle Enter key: newline or send."""
            buf = self.input_buffer

            # Check if current line is empty (Enter×2 = send)
            if buf.document.current_line == "":
                # Send message
                user_input = buf.text.strip()
                if user_input:
                    buf.text = ""  # Clear input
                    # Create background task for chat
                    event.app.create_background_task(self._handle_message(user_input))
            else:
                # Insert newline
                buf.insert_text("\n")

        @kb.add("c-j")  # Ctrl+J = force send
        def _(event: Any) -> None:
            """Force send message."""
            user_input = self.input_buffer.text.strip()
            if user_input:
                self.input_buffer.text = ""
                event.app.create_background_task(self._handle_message(user_input))

        @kb.add("c-p")  # Previous history
        def _(event: Any) -> None:
            """Navigate to previous history item."""
            self.input_buffer.history_backward()

        @kb.add("c-n")  # Next history
        def _(event: Any) -> None:
            """Navigate to next history item."""
            self.input_buffer.history_forward()

        @kb.add("c-c")  # Cancel
        def _(event: Any) -> None:
            """Cancel current input."""
            self.input_buffer.text = ""
            self.append_output("[yellow]Input cancelled[/yellow]\n")

        return kb

    def _on_text_insert(self, buffer: Buffer) -> None:
        """Called when text is inserted in input buffer."""
        # Could add auto-completion trigger here
        pass

    def append_output(self, text: str) -> None:
        """Append text to output area with auto-scroll.

        Args:
            text: Text to append
        """
        # TextArea is read-only, so we need to update the text directly
        current_text = self.output_area.text
        at_bottom = self.auto_scroll_enabled

        # Append new text
        self.output_area.text = current_text + text

        # Auto-scroll: move cursor to end if enabled
        if at_bottom:
            self.output_area.buffer.cursor_position = len(self.output_area.text)

        # Refresh UI
        if hasattr(self, 'app') and self.app.is_running:
            self.app.invalidate()

    async def _handle_message(self, user_input: str) -> None:
        """Handle user message in background.

        Args:
            user_input: User's message
        """
        try:
            # Handle slash commands
            if user_input.startswith("/"):
                if user_input.lower() in ("/exit", "/quit"):
                    self.app.exit()
                    return
                elif user_input.lower() == "/clear":
                    self.output_area.buffer.text = self._render_welcome()
                    self.memory.context.clear()
                    return
                elif user_input.lower() == "/help":
                    self.append_output(self._render_help())
                    return

            # Display user message
            self.append_output(f"\n[bold green][You][/bold green] > {user_input}\n\n")

            # Add to memory
            self.memory.add_message("user", user_input)

            # Show thinking indicator
            self.append_output("[dim]💬 Generating response...[/dim]\n")

            # Get conversation context
            memory_context = await self.memory.get_llm_context()

            # Build full prompt with context
            full_prompt = user_input
            if memory_context:
                context_str = "\n\n[Previous conversation]\n"
                for msg in memory_context:
                    role = msg["role"]
                    content = msg["content"]
                    if role == "user":
                        context_str += f"User: {content}\n"
                    elif role == "assistant":
                        context_str += f"Assistant: {content}\n"
                full_prompt = context_str + "\n[Current message]\n" + user_input

            # Get AI response
            response = await chat_agent(full_prompt, memory=self.memory)

            # Extract content
            response_content = extract_response_content(response)

            # Add to memory
            self.memory.add_message("assistant", response_content)

            # Display response
            self.append_output(f"\n[bold cyan][AI][/bold cyan]\n{response_content}\n")

        except Exception as e:
            self.append_output(f"\n[red]Error: {e}[/red]\n")

    def _render_help(self) -> str:
        """Render help text."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║                        Kagura Chat Help                          ║
╚══════════════════════════════════════════════════════════════════╝

Commands:
  /help     - Show this help
  /clear    - Clear conversation
  /exit     - Quit chat

Shortcuts:
  Enter×2 or Ctrl+J  - Send message
  Ctrl+P/N           - Navigate history
  Ctrl+C             - Cancel input

Features:
  • Shell commands with auto-correction
  • File operations (read/write/search)
  • Code execution
  • Web search & YouTube analysis
  • Multimodal file support (images, PDFs, audio, video)

Just ask naturally - tools are used automatically!

───────────────────────────────────────────────────────────────────

"""

    def run(self) -> None:
        """Run the chat UI application."""
        try:
            self.app.run()
        except (KeyboardInterrupt, EOFError):
            pass  # Exit cleanly
