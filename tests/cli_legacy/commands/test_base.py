# tests/cli/commands/test_base.py
import pytest
from unittest.mock import Mock, AsyncMock
from kagura.cli.commands.base import CommandHandler, CommandRegistry
from kagura.cli.ui import ConsoleManager
from kagura.core.memory import MessageHistory


# CommandHandler のテスト
class TestCommandHandler:
    @pytest.fixture
    def console_manager(self):
        console_manager = Mock(spec=ConsoleManager)
        console_manager.console = Mock()
        return console_manager

    @pytest.fixture
    def message_history(self):
        return Mock(spec=MessageHistory)

    def test_command_handler_initialization(self, console_manager, message_history):
        # 具象クラスを作成してテスト
        class ConcreteHandler(CommandHandler):
            async def handle(self, args: str) -> None:
                pass

        handler = ConcreteHandler(console_manager, message_history)
        assert handler.console == console_manager.console
        assert handler.message_history == message_history


# CommandRegistry のテスト
class TestCommandRegistry:
    @pytest.fixture
    def console_manager(self):
        console_manager = Mock(spec=ConsoleManager)
        console_manager.console = Mock()
        return console_manager

    @pytest.fixture
    def message_history(self):
        return Mock(spec=MessageHistory)

    @pytest.fixture
    def registry(self, console_manager, message_history):
        return CommandRegistry(console_manager, message_history)

    def test_registry_initialization(self, registry, console_manager, message_history):
        assert registry._console_manager == console_manager
        assert registry._message_history == message_history
        assert registry._console == console_manager.console
        # デフォルトハンドラーが登録されていることを確認
        assert "/help" in registry._handlers
        assert "/history" in registry._handlers
        assert "/clear" in registry._handlers
        assert "/system" in registry._handlers
        assert "/agents" in registry._handlers

    def test_register_handler(self, registry, console_manager):
        # テスト用のハンドラーを作成
        class TestHandler(CommandHandler):
            async def handle(self, args: str) -> None:
                pass

        handler = TestHandler(console_manager)
        registry.register_handler("/test", handler)
        assert registry._handlers["/test"] == handler

    @pytest.mark.asyncio
    async def test_execute_command_with_valid_command(self, registry, console_manager):
        # テスト用のハンドラーを作成
        mock_handler = Mock(spec=CommandHandler)
        mock_handler.handle = AsyncMock()
        registry.register_handler("/test", mock_handler)

        await registry.execute_command("/test", "arg1 arg2")
        mock_handler.handle.assert_awaited_once_with("arg1 arg2")

    @pytest.mark.asyncio
    async def test_execute_command_with_invalid_command(self, registry):
        # ヘルプハンドラーのモックを事前に作成して登録
        mock_help_handler = Mock(spec=CommandHandler)
        mock_help_handler.handle = AsyncMock()
        registry._handlers["/help"] = mock_help_handler

        # 存在しないコマンドを実行
        await registry.execute_command("/invalid", "")

        # エラーログの確認
        registry._console.log_error.assert_called_once_with("Unknown command: /invalid")

        # ヘルプハンドラーが呼び出されたことを確認
        mock_help_handler.handle.assert_awaited_once_with("")
