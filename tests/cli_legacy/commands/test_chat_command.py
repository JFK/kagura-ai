# tests/cli/commands/test_chat_command.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from kagura.cli.commands.chat_command import ChatManager, KaguraChat
from kagura.cli.ui import ConsoleManager
from kagura.core.agent import Agent
from kagura.core.memory import MessageHistory


class TestChatManager:
    @pytest.fixture
    def console_manager(self):
        console_manager = Mock(spec=ConsoleManager)
        console_manager.console = Mock()
        console_manager.console.astream_display_typing = AsyncMock(
            return_value="Test response"
        )
        return console_manager

    @pytest.fixture
    def mock_message_history(self):
        history = Mock(spec=MessageHistory)
        history.get_messages = AsyncMock(
            return_value=[{"role": "system", "content": "Test instructions"}]
        )
        history.add_message = AsyncMock()
        history.clear = AsyncMock()
        history.close = AsyncMock()
        return history

    @pytest.fixture
    def chat_manager(self, console_manager, mock_message_history):
        with (
            patch("kagura.core.agent.Agent.assigner") as mock_assigner,
            patch(
                "kagura.core.memory.MessageHistory.factory",
                return_value=mock_message_history,
            ),
        ):
            mock_agent = Mock(spec=Agent)
            mock_agent.instructions = "Test instructions"
            mock_agent.llm = Mock()
            mock_agent.llm.achat_stream = AsyncMock(return_value="Test response")
            mock_assigner.return_value = mock_agent

            return ChatManager(console_manager)

    # テストクラスの最後に以下を追加
    @pytest.fixture(autouse=True)
    async def cleanup_redis(self):
        yield
        # Redisのクリーンアップ
        from kagura.core.memory import MemoryBackend

        backend = MemoryBackend()
        await backend.close()

    @pytest.mark.asyncio
    async def test_process_message(self, chat_manager, mock_message_history):
        # 初期化
        await chat_manager.initialize()
        await chat_manager.message_history.clear()

        # 初期状態の確認
        initial_messages = await chat_manager.message_history.get_messages()
        print(initial_messages)
        assert len(initial_messages) == 1  # システムプロンプトのみ
        assert initial_messages[0]["role"] == "system"

        # メッセージ処理後の状態をセット
        mock_message_history.get_messages.return_value = [
            {"role": "system", "content": "Test instructions"},
            {"role": "user", "content": "Hello"},
        ]

        # プロセスメッセージの実行
        response = await chat_manager.process_message("Hello")
        assert response == "Test response"

    @pytest.mark.asyncio
    async def test_process_message_skip_history(
        self, chat_manager, mock_message_history
    ):
        # 初期化
        await chat_manager.initialize()

        # スキップモードでメッセージを処理
        mock_message_history.get_messages.return_value = [
            {"role": "system", "content": "Test instructions"}
        ]

        response = await chat_manager.process_message("Hello", skip_history=True)
        assert response == "Test response"

        # add_messageが呼ばれていないことを確認
        mock_message_history.add_message.assert_not_called()


class TestKaguraChat:
    @pytest.fixture
    def mock_message_history(self):
        history = Mock(spec=MessageHistory)
        history.get_messages = AsyncMock(
            return_value=[{"role": "system", "content": "Test instructions"}]
        )
        history.add_message = AsyncMock()
        history.clear = AsyncMock()
        history.close = AsyncMock()
        return history

    @pytest.fixture
    def kagura_chat(self):
        chat = KaguraChat()
        chat.console_manager = Mock(spec=ConsoleManager)
        chat.console_manager.console = Mock()
        chat.console_manager.display_welcome_message = AsyncMock()
        return chat

    @pytest.mark.asyncio
    async def test_initialization(self, kagura_chat, mock_message_history):
        with (
            patch("kagura.core.agent.Agent.assigner") as mock_assigner,
            patch(
                "kagura.core.memory.MessageHistory.factory",
                return_value=mock_message_history,
            ),
        ):
            mock_agent = Mock(spec=Agent)
            mock_agent.instructions = "Test instructions"
            mock_agent.llm = Mock()
            mock_agent.llm.achat_stream = AsyncMock(return_value="Test response")
            mock_assigner.return_value = mock_agent

            await kagura_chat.initialize()
            assert kagura_chat.message_history == mock_message_history
            assert kagura_chat.command_registry is not None

    @pytest.mark.asyncio
    async def test_cleanup(self, kagura_chat, mock_message_history):
        with (
            patch("kagura.core.agent.Agent.assigner") as mock_assigner,
            patch(
                "kagura.core.memory.MessageHistory.factory",
                return_value=mock_message_history,
            ),
        ):
            mock_agent = Mock(spec=Agent)
            mock_agent.instructions = "Test instructions"
            mock_agent.llm = Mock()
            mock_agent.llm.achat_stream = AsyncMock(return_value="Test response")
            mock_assigner.return_value = mock_agent

            await kagura_chat.initialize()
            await kagura_chat.cleanup()

            mock_message_history.close.assert_awaited_once()
            kagura_chat.console_manager.console.print.assert_called_with(
                "\n[yellow]Leaving Kagura AI...[/yellow]"
            )
