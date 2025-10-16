"""
Smart autocomplete for Kagura Chat
"""

from typing import Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class KaguraCompleter(Completer):
    """
    Smart autocomplete for Kagura chat.

    Provides completion for:
    - Slash commands (/translate, /summarize, etc.)
    - Agent names (@agent_name)
    - Tool names (!tool_name)
    """

    def __init__(self, session: "ChatSession") -> None:  # type: ignore  # noqa: F821
        """
        Initialize completer.

        Args:
            session: ChatSession instance for accessing agents/tools
        """
        self.session = session

        # Slash commands
        # (removed /translate, /summarize, /review - use natural language instead)
        self.slash_commands = [
            "/help",
            "/exit",
            "/quit",
            "/clear",
            "/save",
            "/load",
            "/agent",
            "/agents",
        ]

    def get_completions(
        self,
        document: Document,
        complete_event: "CompleteEvent",  # type: ignore  # noqa: F821
    ) -> Iterable[Completion]:
        """
        Get completions for the current input.

        Args:
            document: Current document
            complete_event: Completion event

        Yields:
            Completion objects
        """
        text = document.text_before_cursor

        # Slash commands
        if text.startswith("/"):
            for cmd in self.slash_commands:
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display_meta=self._get_command_description(cmd),
                    )

        # Agent names (@agent_name)
        elif text.startswith("@"):
            for agent_name in self.session.custom_agents.keys():
                suggestion = f"@{agent_name}"
                if suggestion.startswith(text):
                    # Get agent description
                    agent_func = self.session.custom_agents[agent_name]
                    desc = self._get_first_line(agent_func.__doc__)
                    yield Completion(
                        suggestion, start_position=-len(text), display_meta=desc
                    )

        # Tool names (!tool_name) - placeholder for future tool support
        elif text.startswith("!"):
            # TODO: Add tool registry integration when available
            pass

    def _get_command_description(self, cmd: str) -> str:
        """
        Get description for a slash command.

        Args:
            cmd: Command name

        Returns:
            Command description
        """
        descriptions = {
            "/help": "Show detailed help and examples",
            "/exit": "Exit chat",
            "/quit": "Exit chat",
            "/clear": "Clear conversation history",
            "/save": "Save current session for later",
            "/load": "Load a saved session",
            "/agent": "List or use custom agents",
            "/agents": "List or use custom agents",
        }
        return descriptions.get(cmd, "")

    def _get_first_line(self, text: str | None) -> str:
        """
        Get first non-empty line from text.

        Args:
            text: Input text

        Returns:
            First non-empty line or empty string
        """
        if not text:
            return ""
        for line in text.strip().split("\n"):
            if line.strip():
                return line.strip()
        return ""
