# cli/commands/chat_command.py
import asyncio
import sys

import click

from kagura.core.agent import Agent
from kagura.core.memory import MessageHistory

from ..ui import ConsoleManager
from . import CommandRegistry


class ChatManager:
    def __init__(self, console_manager: ConsoleManager):
        self.message_history = None
        self.chat_agent = Agent.assigner("chat")
        self.console = console_manager.console

    async def initialize(self):
        self.message_history = await MessageHistory.factory(
            system_prompt=self.chat_agent.instructions
        )

    async def process_message(self, message: str, skip_history: bool = False) -> str:
        if self.message_history is None:
            raise ValueError("Message history is not initialized")

        if not skip_history:
            await self.message_history.add_message("user", message)

        messages = await self.message_history.get_messages()

        response_text = await self.console.astream_display_typing(
            self.chat_agent.llm.achat_stream, messages=messages
        )

        if not skip_history:
            await self.message_history.add_message("assistant", response_text)
        return response_text


class KaguraChat:
    def __init__(self, window_size: int = 20):
        self.console_manager = ConsoleManager()
        self.chat_manager = ChatManager(self.console_manager)
        self.message_history = None
        self.command_registry = None  # Initialize later after message_history is ready

    async def initialize(self):
        await self.chat_manager.initialize()
        if self.chat_manager.message_history is None:
            raise ValueError("Message history is not initialized")
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
                    if self.command_registry is None:
                        raise ValueError("Command registry is not initialized")
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


@click.command()
def chat():
    """Start interactive chat with Kagura AI"""
    try:
        chat = KaguraChat()
        asyncio.run(chat.arun())
    except KeyboardInterrupt:
        print("\nShutting down Kagura AI...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
