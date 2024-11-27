# cli/commands/base.py
from abc import ABC, abstractmethod
from typing import Dict

from kagura.core.memory import MessageHistory

from ..ui import ConsoleManager


class CommandHandler(ABC):
    def __init__(
        self, console_manager: ConsoleManager, message_history: MessageHistory = None
    ):
        self.console = console_manager.console
        self.message_history = message_history

    @abstractmethod
    async def handle(self, args: str) -> None:
        """Handle command execution"""
        pass


class CommandRegistry:
    def __init__(
        self, console_manager: ConsoleManager, message_history: MessageHistory
    ):
        self._handlers: Dict[str, CommandHandler] = {}
        self._console_manager = console_manager
        self._message_history = message_history
        self._console = console_manager.console
        self._register_default_handlers()

    def _register_default_handlers(self):
        from . import (ClearCommandHandler, HelpCommandHandler,
                       HistoryCommandHandler)

        self.register_handler("/help", HelpCommandHandler(self._console_manager))
        self.register_handler(
            "/history",
            HistoryCommandHandler(self._console_manager, self._message_history),
        )
        self.register_handler(
            "/clear", ClearCommandHandler(self._console_manager, self._message_history)
        )

    def register_handler(self, command: str, handler: CommandHandler):
        self._handlers[command] = handler

    async def execute_command(self, command: str, args: str) -> None:
        handler = self._handlers.get(command)
        if handler:
            await handler.handle(args)
        else:
            self._console.log_error(f"Unknown command: {command}")
            handler = self._handlers.get("/help")
            await handler.handle("")
