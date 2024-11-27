# cli/chat/chat_manager.py
from kagura.core.agent import Agent
from kagura.core.memory import MessageHistory

from ..ui import ConsoleManager


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
        if not skip_history:
            await self.message_history.add_message("user", message)

        messages = await self.message_history.get_messages()

        response_text = await self.console.astream_display_typing(
            self.chat_agent.llm.achat_stream, messages=messages
        )

        if not skip_history:
            await self.message_history.add_message("assistant", response_text)
        return response_text
