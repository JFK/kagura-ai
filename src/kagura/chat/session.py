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
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from kagura import agent
from kagura.core.memory import MemoryManager
from kagura.routing import AgentRouter, NoAgentFoundError

from .preset import CodeReviewAgent, SummarizeAgent, TranslateAgent


@agent(model="gpt-4o-mini", temperature=0.7, enable_memory=True)
async def chat_agent(user_input: str, memory: MemoryManager) -> str:
    """
    You are a helpful AI assistant. Previous conversation context is available
    in your memory.

    User: {{ user_input }}

    Respond naturally and helpfully. Provide code examples when relevant.
    Use markdown formatting for better readability.
    """
    ...


# Web-enabled chat agent with web_search tool
async def _web_search_tool(query: str) -> str:
    """Search the web for information.

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


@agent(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_memory=True,
    tools=[_web_search_tool],
)
async def chat_agent_with_web(user_input: str, memory: MemoryManager) -> str:
    """
    You are a helpful AI assistant with web search capabilities. Previous
    conversation context is available in your memory.

    User: {{ user_input }}

    You have access to the web_search(query) tool. Use it when you need to:
    - Find current information or recent events
    - Look up facts, statistics, or references
    - Research topics the user asks about

    Respond naturally and helpfully. Provide code examples when relevant.
    Use markdown formatting for better readability.
    """
    ...


class ChatSession:
    """
    Interactive chat session manager for Kagura AI.

    Provides a REPL interface with:
    - Natural language conversations
    - Preset commands (/translate, /summarize, /review)
    - Session management (/save, /load)
    - Rich UI with markdown rendering
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        session_dir: Path | None = None,
        enable_multimodal: bool = False,
        rag_directory: Path | None = None,
        enable_web: bool = False,
        enable_routing: bool = True,
    ):
        """
        Initialize chat session.

        Args:
            model: LLM model to use
            session_dir: Directory for session storage
            enable_multimodal: Enable multimodal RAG (images, PDFs, audio)
            rag_directory: Directory to index for RAG (requires enable_multimodal)
            enable_web: Enable web search capabilities
            enable_routing: Enable automatic agent routing (default: True)
        """
        self.console = Console()
        self.model = model
        self.enable_multimodal = enable_multimodal
        self.rag_directory = rag_directory
        self.enable_web = enable_web
        self.enable_routing = enable_routing
        self.session_dir = session_dir or Path.home() / ".kagura" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create memory manager
        self.memory = MemoryManager(
            agent_name="chat_session",
            persist_dir=self.session_dir / "memory",
        )

        # Initialize MultimodalRAG if enabled
        self.rag = None
        if self.enable_multimodal:
            self._init_multimodal_rag()

        # Prompt session with history
        history_file = self.session_dir / "chat_history.txt"
        self.prompt_session: PromptSession[str] = PromptSession(
            history=FileHistory(str(history_file))
        )

        # Load custom agents from ./agents directory
        self.custom_agents: dict[str, Any] = {}
        self.router: AgentRouter | None = None
        if self.enable_routing:
            self.router = AgentRouter()
        self._load_custom_agents()

    def _init_multimodal_rag(self) -> None:
        """Initialize MultimodalRAG."""
        try:
            from kagura.core.memory import MultimodalRAG
        except ImportError:
            self.console.print(
                "[red]Error: MultimodalRAG requires multimodal extra.[/]\n"
                "[yellow]Install with: pip install kagura-ai[multimodal][/]"
            )
            raise

        if not self.rag_directory:
            self.console.print(
                "[yellow]Warning: Multimodal RAG enabled without directory.[/]\n"
                "[yellow]Use --dir to index a directory for RAG.[/]"
            )
            return

        # Initialize RAG with directory
        self.console.print(
            f"[cyan]Initializing multimodal RAG for: {self.rag_directory}[/]"
        )

        self.rag = MultimodalRAG(
            directory=self.rag_directory,
            collection_name="chat_session_rag",
            persist_dir=self.session_dir / "rag",
        )

        self.console.print(
            f"[green]✓ Indexed {len(list(self.rag_directory.rglob('*')))} "
            f"files from {self.rag_directory}[/]"
        )

    def _load_custom_agents(self) -> None:
        """Load custom agents from ./agents directory."""
        agents_dir = Path.cwd() / "agents"

        if not agents_dir.exists() or not agents_dir.is_dir():
            return

        agent_files = list(agents_dir.glob("*.py"))
        if not agent_files:
            return

        self.console.print(
            f"[dim]Loading custom agents from {agents_dir}...[/dim]"
        )

        loaded_count = 0
        for agent_file in agent_files:
            try:
                # Load the module
                module_name = agent_file.stem
                spec = importlib.util.spec_from_file_location(
                    module_name, agent_file
                )

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

                                self.router.register(
                                    attr,
                                    intents=keywords
                                )

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
                # Get user input
                user_input = await self.prompt_session.prompt_async(
                    "\n[You] > ",
                    # multiline=True,
                )

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
                self.console.print(
                    "[dim]✓ Using custom agent for this request[/]\n"
                )
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

        # Query RAG if available
        rag_context = ""
        if self.rag is not None:
            self.console.print("[dim]Searching indexed files...[/]")
            rag_results = self.rag.query(user_input, n_results=3)

            if rag_results:
                rag_context = "\n\n[Relevant context from indexed files]:\n"
                for i, result in enumerate(rag_results, 1):
                    rag_context += f"\n{i}. From {result.get('source', 'unknown')}:\n"
                    rag_context += f"{result.get('content', '')}\n"

                self.console.print(
                    f"[dim]Found {len(rag_results)} relevant documents[/]"
                )

        # Enhance input with RAG context
        enhanced_input = user_input
        if rag_context:
            enhanced_input = f"{user_input}\n{rag_context}"

        # Get AI response (use web-enabled agent if enabled)
        self.console.print("[dim]💬 Generating response...[/]")
        if self.enable_web:
            response = await chat_agent_with_web(enhanced_input, memory=self.memory)
        else:
            response = await chat_agent(enhanced_input, memory=self.memory)

        # Add assistant message to memory
        self.memory.add_message("assistant", str(response))

        # Display response with markdown
        self.console.print("\n[bold green][AI][/]")
        self.console.print(Markdown(str(response)))

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
        elif command == "/exit" or command == "/quit":
            return False
        elif command == "/translate":
            await self.preset_translate(args)
        elif command == "/summarize":
            await self.preset_summarize(args)
        elif command == "/review":
            await self.preset_review(args)
        elif command == "/agent" or command == "/agents":
            await self.handle_agent_command(args)
        else:
            self.console.print(f"[red]Unknown command: {command}[/]")
            self.console.print("Type [bold]/help[/] for available commands")

        return True

    def show_welcome(self) -> None:
        """Display welcome message."""
        features = []
        features.append("Type your message to chat with AI, or use commands:")
        features.append("  [cyan]/help[/]      - Show help")
        features.append("  [cyan]/translate[/] - Translate text")
        features.append("  [cyan]/summarize[/] - Summarize text")
        features.append("  [cyan]/review[/]    - Review code")
        if self.custom_agents:
            routing_status = " 🎯 auto-routing" if self.router else ""
            features.append(
                f"  [cyan]/agent[/]     - Use custom agents "
                f"({len(self.custom_agents)} available{routing_status})"
            )
        features.append("  [cyan]/exit[/]      - Exit chat")

        # Full-featured mode
        if self.enable_multimodal and self.enable_web:
            features.insert(1, "\n[bold magenta]🚀 Full-Featured Mode[/]")
            features.insert(2, "[bold yellow]⚡ Multimodal RAG[/]")
            if self.rag_directory:
                features.insert(3, f"[dim]   Indexed: {self.rag_directory}[/]")
            features.insert(4, "[bold cyan]🌐 Web Search[/]")
        else:
            # Individual features
            if self.enable_multimodal:
                features.insert(1, "\n[bold yellow]⚡ Multimodal RAG Enabled[/]")
                if self.rag_directory:
                    features.insert(
                        2,
                        f"[dim]Indexed: {self.rag_directory}[/]"
                    )

            if self.enable_web:
                insert_pos = 2 if self.enable_multimodal else 1
                features.insert(insert_pos, "\n[bold cyan]🌐 Web Search Enabled[/]")

        welcome = Panel(
            "[bold green]Welcome to Kagura Chat![/]\n\n" + "\n".join(features) + "\n",
            title="Kagura AI Chat",
            border_style="green",
        )
        self.console.print(welcome)

    def show_help(self) -> None:
        """Display help message."""
        help_text = """
# Kagura Chat Commands

## Chat
- Just type your message to chat with AI

## Preset Commands
- `/translate <text> [to <language>]` - Translate text (default: to Japanese)
- `/summarize <text>` - Summarize text
- `/review` - Review code (paste code after command)

## Custom Agents
- `/agent` or `/agents` - List available custom agents
- `/agent <name> <input>` - Execute a custom agent

## Session Management
- `/save [name]` - Save current session (default: timestamp)
- `/load <name>` - Load saved session
- `/clear` - Clear conversation history

## Other
- `/help` - Show this help
- `/exit` or `/quit` - Exit chat
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

    async def preset_translate(self, args: str) -> None:
        """
        Translate text using preset agent.

        Args:
            args: "text [to language]"
        """
        if not args:
            self.console.print("[red]Usage: /translate <text> [to <language>][/]")
            return

        # Parse arguments
        parts = args.split(" to ")
        text = parts[0].strip()
        target_lang = parts[1].strip() if len(parts) > 1 else "ja"

        # Translate
        self.console.print(f"\n[cyan]Translating to {target_lang}...[/]")
        result = await TranslateAgent(text, target_language=target_lang)

        # Display result
        self.console.print(Panel(result, title="Translation", border_style="cyan"))

    async def preset_summarize(self, args: str) -> None:
        """
        Summarize text using preset agent.

        Args:
            args: Text to summarize
        """
        if not args:
            self.console.print("[red]Usage: /summarize <text>[/]")
            return

        # Summarize
        self.console.print("\n[cyan]Summarizing...[/]")
        result = await SummarizeAgent(args)

        # Display result
        self.console.print(Panel(result, title="Summary", border_style="cyan"))

    async def preset_review(self, args: str) -> None:
        """
        Review code using preset agent.

        Args:
            args: Code to review (or empty to prompt for input)
        """
        if not args:
            # Prompt for multiline code input
            self.console.print(
                "[cyan]Paste your code (press Enter twice to finish):[/]"
            )
            lines: list[str] = []
            empty_count = 0
            while True:
                try:
                    line = await self.prompt_session.prompt_async("")
                    if not line:
                        empty_count += 1
                        if empty_count >= 2:
                            break
                    else:
                        empty_count = 0
                        lines.append(line)
                except (KeyboardInterrupt, EOFError):
                    break

            code = "\n".join(lines)
            if not code.strip():
                self.console.print("[red]No code provided[/]")
                return
        else:
            code = args

        # Review code
        self.console.print("\n[cyan]Reviewing code...[/]")
        result = await CodeReviewAgent(code)

        # Display result
        self.console.print("\n[bold green][Code Review][/]")
        self.console.print(Markdown(result))

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
                    "[dim]Create agents in ./agents/ directory using:[/]\n"
                    "[dim]  kagura build agent[/]"
                )
                return

            self.console.print("[bold cyan]Available Custom Agents:[/]")
            for name, agent_func in self.custom_agents.items():
                doc = agent_func.__doc__ or "No description"
                # Get first line of docstring
                first_line = doc.strip().split("\n")[0]
                self.console.print(f"  • [cyan]{name}[/]: {first_line}")

            self.console.print(
                "\n[dim]Usage: /agent <name> <input>[/]"
            )
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
        self.console.print(
            f"\n[cyan]Executing {agent_name}...[/]"
        )

        try:
            result = await agent_func(input_data)

            # Display result
            self.console.print(
                f"\n[bold green][{agent_name} Result][/]"
            )
            self.console.print(Panel(str(result), border_style="green"))

        except Exception as e:
            self.console.print(
                f"[red]Error executing {agent_name}: {e}[/]"
            )
