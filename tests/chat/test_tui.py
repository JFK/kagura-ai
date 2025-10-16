"""Tests for 2-column TUI."""

import pytest

from kagura.chat.tui import TwoColumnChatUI


class TestTwoColumnChatUI:
    """Tests for TwoColumnChatUI class."""

    def test_initialization(self):
        """Test TUI can be initialized."""
        tui = TwoColumnChatUI()

        assert tui is not None
        assert tui.model == "gpt-4o-mini"
        assert tui.memory is not None
        assert tui.app is not None

    def test_output_area_exists(self):
        """Test output area is properly configured."""
        tui = TwoColumnChatUI()

        assert tui.output_area is not None
        assert tui.output_area.read_only is True
        # scrollbar is a constructor param, not an attribute
        assert tui.output_area.wrap_lines is True

    def test_input_buffer_exists(self):
        """Test input buffer is properly configured."""
        tui = TwoColumnChatUI()

        assert tui.input_buffer is not None
        # multiline is a Filter object, not a bool
        assert tui.input_buffer.multiline is not None

    def test_welcome_message(self):
        """Test welcome message is rendered."""
        tui = TwoColumnChatUI()
        welcome = tui._render_welcome()

        assert "Welcome to Kagura Chat" in welcome
        assert "2-Column UI" in welcome
        assert "Features:" in welcome

    def test_help_message(self):
        """Test help message is rendered."""
        tui = TwoColumnChatUI()
        help_text = tui._render_help()

        assert "Help" in help_text
        assert "/exit" in help_text
        assert "/clear" in help_text

    def test_append_output(self):
        """Test appending text to output area."""
        tui = TwoColumnChatUI()

        initial_len = len(tui.output_area.text)
        tui.append_output("Test message\n")

        assert len(tui.output_area.text) > initial_len
        assert "Test message" in tui.output_area.text

    def test_auto_scroll_enabled_by_default(self):
        """Test auto-scroll is enabled by default."""
        tui = TwoColumnChatUI()

        assert tui.auto_scroll_enabled is True

    def test_key_bindings_created(self):
        """Test key bindings are properly set up."""
        tui = TwoColumnChatUI()

        assert tui.app.key_bindings is not None

    def test_session_dir_created(self):
        """Test session directory is created."""
        tui = TwoColumnChatUI()

        assert tui.session_dir.exists()
        assert tui.session_dir.is_dir()

    def test_custom_model(self):
        """Test custom model can be specified."""
        tui = TwoColumnChatUI(model="gpt-4o")

        assert tui.model == "gpt-4o"
