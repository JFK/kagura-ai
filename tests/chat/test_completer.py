"""
Tests for KaguraCompleter
"""

import pytest
from prompt_toolkit.document import Document

from kagura.chat.completer import KaguraCompleter
from kagura.chat.session import ChatSession


class TestKaguraCompleter:
    """Test suite for KaguraCompleter"""

    @pytest.fixture
    def session(self) -> ChatSession:
        """Create a test chat session"""
        return ChatSession()

    @pytest.fixture
    def completer(self, session: ChatSession) -> KaguraCompleter:
        """Create a test completer"""
        return KaguraCompleter(session)

    def test_slash_command_completion(self, completer: KaguraCompleter) -> None:
        """Test completion for slash commands"""
        # Test /help
        document = Document("/h")
        completions = list(completer.get_completions(document, None))  # type: ignore

        assert len(completions) > 0
        assert any(c.text == "/help" for c in completions)

    def test_slash_command_exact_match(self, completer: KaguraCompleter) -> None:
        """Test exact match for slash command"""
        document = Document("/help")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Should still show /help
        assert any(c.text == "/help" for c in completions)

    def test_slash_command_multiple_matches(self, completer: KaguraCompleter) -> None:
        """Test multiple matches for slash commands"""
        document = Document("/")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Should show all slash commands (8 commands after removing presets)
        assert len(completions) >= 7
        commands = [c.text for c in completions]
        assert "/help" in commands
        assert "/exit" in commands
        assert "/clear" in commands
        assert "/save" in commands
        assert "/load" in commands

    def test_agent_completion(self) -> None:
        """Test completion for agent names"""
        # Create session with custom agents
        session = ChatSession()

        # Mock a custom agent
        async def test_agent(input: str) -> str:
            """Test agent description"""
            return "test"

        test_agent._is_agent = True  # type: ignore
        session.custom_agents["test_agent"] = test_agent

        completer = KaguraCompleter(session)

        # Test @agent completion
        document = Document("@test")
        completions = list(completer.get_completions(document, None))  # type: ignore

        assert len(completions) > 0
        assert any(c.text == "@test_agent" for c in completions)

    def test_no_completion_for_regular_text(self, completer: KaguraCompleter) -> None:
        """Test that regular text doesn't trigger completion"""
        document = Document("hello world")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Should return empty for regular text
        assert len(completions) == 0

    def test_completion_display_meta(self, completer: KaguraCompleter) -> None:
        """Test that completions have display metadata"""
        document = Document("/help")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Check that help command has description
        help_completion = next(c for c in completions if c.text == "/help")
        # display_meta can be string or FormattedText
        meta = help_completion.display_meta
        if hasattr(meta, "__str__"):
            assert "help" in str(meta).lower()
        else:
            assert "help" in meta.lower()

    def test_empty_input(self, completer: KaguraCompleter) -> None:
        """Test completion with empty input"""
        document = Document("")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Should return empty
        assert len(completions) == 0

    def test_slash_only(self, completer: KaguraCompleter) -> None:
        """Test completion with just slash"""
        document = Document("/")
        completions = list(completer.get_completions(document, None))  # type: ignore

        # Should show all commands (8 after removing presets)
        assert len(completions) >= 7
