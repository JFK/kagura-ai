"""Tests for REPL module"""
import pytest
import os
import tempfile
from io import StringIO
from unittest.mock import patch, MagicMock
from kagura.cli.repl import KaguraREPL


class TestKaguraREPL:
    """Tests for KaguraREPL class"""

    def test_repl_initialization(self):
        """Test REPL initializes correctly"""
        repl = KaguraREPL()
        assert repl.agents == {}
        assert repl.history == []

    def test_show_help(self):
        """Test help command displays correctly"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.show_help()

    def test_show_agents_empty(self):
        """Test showing agents when none are defined"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.show_agents()

    def test_show_agents_with_agents(self):
        """Test showing agents when some are defined"""
        repl = KaguraREPL()

        # Define a mock agent
        def mock_agent():
            pass

        mock_agent._is_agent = True
        repl.agents["test_agent"] = mock_agent

        # Should not raise any exceptions
        repl.show_agents()

    def test_execute_help_command(self):
        """Test /help command execution"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.execute_command("/help")

    def test_execute_agents_command(self):
        """Test /agents command execution"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.execute_command("/agents")

    def test_execute_clear_command(self):
        """Test /clear command execution"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.execute_command("/clear")

    def test_execute_unknown_command(self):
        """Test unknown command handling"""
        repl = KaguraREPL()
        # Should not raise any exceptions
        repl.execute_command("/unknown")

    def test_execute_simple_code(self):
        """Test executing simple Python code"""
        repl = KaguraREPL()
        code = "x = 42"
        # Should not raise any exceptions
        repl.execute_code(code)

    def test_execute_code_with_syntax_error(self):
        """Test handling syntax errors in code"""
        repl = KaguraREPL()
        code = "x = "
        # Should not raise any exceptions, but print error
        repl.execute_code(code)

    def test_execute_code_with_runtime_error(self):
        """Test handling runtime errors in code"""
        repl = KaguraREPL()
        code = "x = 1 / 0"
        # Should not raise any exceptions, but print error
        repl.execute_code(code)

    def test_execute_code_defines_function(self):
        """Test executing code that defines a function"""
        repl = KaguraREPL()
        code = """
def test_func():
    return 42
"""
        repl.execute_code(code)

    def test_history_tracking(self):
        """Test that history is tracked correctly"""
        repl = KaguraREPL()
        assert len(repl.history) == 0

        repl.history.append("x = 1")
        repl.history.append("y = 2")

        assert len(repl.history) == 2
        assert repl.history[0] == "x = 1"
        assert repl.history[1] == "y = 2"

    def test_execute_code_with_print(self):
        """Test executing code with print statements"""
        repl = KaguraREPL()
        code = 'print("Hello, World!")'
        # Should not raise any exceptions
        repl.execute_code(code)

    def test_execute_code_with_console(self):
        """Test executing code that uses console"""
        repl = KaguraREPL()
        code = 'console.print("[green]Test[/green]")'
        # Should not raise any exceptions
        repl.execute_code(code)

    def test_agent_registration(self):
        """Test that agents are registered when defined"""
        repl = KaguraREPL()

        # Simulate defining an agent with _is_agent attribute
        code = """
def my_agent():
    return "test"
my_agent._is_agent = True
"""
        repl.execute_code(code)

        # Agent should be registered
        assert "my_agent" in repl.agents
        assert callable(repl.agents["my_agent"])

    def test_dotenv_loading(self):
        """Test that .env file is loaded on initialization"""
        with patch('kagura.cli.repl.load_dotenv') as mock_load_dotenv:
            with patch('readline.read_history_file'):
                with patch('readline.set_history_length'):
                    repl = KaguraREPL()

                    # Verify load_dotenv was called
                    mock_load_dotenv.assert_called_once()

    def test_history_file_loading(self):
        """Test that history file is loaded on initialization"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_history', delete=False) as f:
            history_file = f.name
            # Write some history
            f.write("command1\n")
            f.write("command2\n")

        try:
            with patch('os.path.expanduser', return_value=history_file):
                with patch('readline.read_history_file') as mock_read:
                    with patch('readline.set_history_length') as mock_set_length:
                        repl = KaguraREPL()

                        # Verify history file was read
                        mock_read.assert_called_once_with(history_file)
                        # Verify history length was set to 1000
                        mock_set_length.assert_called_once_with(1000)
        finally:
            os.unlink(history_file)

    def test_history_file_loading_missing_file(self):
        """Test that missing history file doesn't cause errors"""
        with patch('os.path.expanduser', return_value='/nonexistent/history'):
            with patch('readline.set_history_length'):
                # Should not raise any exceptions
                repl = KaguraREPL()
                assert repl.history_file == '/nonexistent/history'

    def test_history_file_saving(self):
        """Test that history file is saved"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_history', delete=False) as f:
            history_file = f.name

        try:
            with patch('os.path.expanduser', return_value=history_file):
                with patch('readline.read_history_file'):
                    with patch('readline.set_history_length'):
                        repl = KaguraREPL()

                with patch('readline.write_history_file') as mock_write:
                    repl._save_history()
                    mock_write.assert_called_once_with(history_file)
        finally:
            os.unlink(history_file)
