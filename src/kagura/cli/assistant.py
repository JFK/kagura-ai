# cli/assistant.py
from .chat import ChatManager
from .commands import CommandRegistry
from .ui import ConsoleManager


# cli/assistant.py
class KaguraAIAssistant:
    def __init__(self, window_size: int = 20):
        self.console_manager = ConsoleManager()
        self.chat_manager = ChatManager(self.console_manager)
        self.message_history = None
        self.command_registry = None  # Initialize later after message_history is ready

    async def initialize(self):
        await self.chat_manager.initialize()
        self.message_history = self.chat_manager.message_history
        self.command_registry = CommandRegistry(
            self.console_manager, self.message_history
        )

    async def arun(self) -> None:
        await self.initialize()
        await self.console_manager.display_welcome_message()

        await self.chat_manager.process_message("Hi", skip_history=True)

        while True:
            try:
                prompt = await self.console_manager.console.multiline_input("")
                if not prompt.strip():
                    continue

                if prompt.startswith("/"):
                    command, args = self._extract_command(prompt)
                    if command == "/exit":
                        break
                    await self.command_registry.execute_command(command, args)
                else:
                    await self.chat_manager.process_message(prompt)

            except Exception as e:
                await self.console_manager.display_error(e)
                break

        await self.cleanup()

    async def cleanup(self):
        if self.message_history:
            await self.message_history.close()
        self.console_manager.console.print("\n[yellow]Leaving Kagura AI...[/yellow]")

    def _extract_command(self, prompt: str) -> tuple[str, str]:
        command_parts = prompt[1:].split(maxsplit=1)
        return f"/{command_parts[0]}", (
            command_parts[1] if len(command_parts) > 1 else ""
        )
