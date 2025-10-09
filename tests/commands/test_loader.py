"""Tests for CommandLoader."""

import pytest
from pathlib import Path

from kagura.commands.command import Command
from kagura.commands.loader import CommandLoader


@pytest.fixture
def tmp_commands_dir(tmp_path):
    """Create temporary commands directory."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    return commands_dir


def test_loader_initialization_default():
    """Test loader initialization with default directory."""
    loader = CommandLoader()
    expected_dir = Path.home() / ".kagura" / "commands"
    assert loader.commands_dir == expected_dir


def test_loader_initialization_custom(tmp_commands_dir):
    """Test loader initialization with custom directory."""
    loader = CommandLoader(tmp_commands_dir)
    assert loader.commands_dir == tmp_commands_dir


def test_load_command_basic(tmp_commands_dir):
    """Test loading a basic command."""
    cmd_file = tmp_commands_dir / "test.md"
    cmd_file.write_text(
        """---
name: test-cmd
description: Test command
---

# Task
Execute test task
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    command = loader.load_command(cmd_file)

    assert command.name == "test-cmd"
    assert command.description == "Test command"
    assert "# Task" in command.template
    assert "Execute test task" in command.template


def test_load_command_full_metadata(tmp_commands_dir):
    """Test loading command with all metadata."""
    cmd_file = tmp_commands_dir / "full.md"
    cmd_file.write_text(
        """---
name: full-cmd
description: Full command with metadata
allowed_tools: [git, gh, bash]
model: gpt-4o
parameters:
  file: string
  count: int
author: test
version: 1.0
---

# Full Task
Execute full task with parameters
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    command = loader.load_command(cmd_file)

    assert command.name == "full-cmd"
    assert command.description == "Full command with metadata"
    assert command.allowed_tools == ["git", "gh", "bash"]
    assert command.model == "gpt-4o"
    assert command.parameters == {"file": "string", "count": "int"}
    assert command.metadata == {"author": "test", "version": 1.0}


def test_load_command_name_from_filename(tmp_commands_dir):
    """Test that command name defaults to filename if not in frontmatter."""
    cmd_file = tmp_commands_dir / "my-command.md"
    cmd_file.write_text(
        """---
description: Command without explicit name
---

# Task
Do something
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    command = loader.load_command(cmd_file)

    assert command.name == "my-command"  # From filename


def test_load_command_file_not_found(tmp_commands_dir):
    """Test loading non-existent file raises error."""
    loader = CommandLoader(tmp_commands_dir)
    nonexistent = tmp_commands_dir / "nonexistent.md"

    with pytest.raises(FileNotFoundError):
        loader.load_command(nonexistent)


def test_load_all_commands(tmp_commands_dir):
    """Test loading all commands from directory."""
    # Create multiple command files
    (tmp_commands_dir / "cmd1.md").write_text(
        """---
name: cmd1
description: First command
---
Task 1
"""
    )

    (tmp_commands_dir / "cmd2.md").write_text(
        """---
name: cmd2
description: Second command
---
Task 2
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    commands = loader.load_all()

    assert len(commands) == 2
    assert "cmd1" in commands
    assert "cmd2" in commands
    assert commands["cmd1"].description == "First command"
    assert commands["cmd2"].description == "Second command"


def test_load_all_directory_not_found():
    """Test load_all raises error if directory doesn't exist."""
    nonexistent_dir = Path("/nonexistent/directory")
    loader = CommandLoader(nonexistent_dir)

    with pytest.raises(FileNotFoundError):
        loader.load_all()


def test_load_all_skips_invalid_files(tmp_commands_dir, capsys):
    """Test that load_all skips invalid files and continues."""
    # Valid command
    (tmp_commands_dir / "valid.md").write_text(
        """---
name: valid
description: Valid command
---
Valid task
"""
    )

    # Invalid file (empty)
    (tmp_commands_dir / "invalid.md").write_text("")

    loader = CommandLoader(tmp_commands_dir)
    commands = loader.load_all()

    # Should load only the valid command
    assert len(commands) == 1
    assert "valid" in commands

    # Should print warning to stdout
    captured = capsys.readouterr()
    assert "Warning" in captured.out or "invalid" in captured.out.lower()


def test_get_command(tmp_commands_dir):
    """Test getting a loaded command by name."""
    (tmp_commands_dir / "test.md").write_text(
        """---
name: test-cmd
---
Task
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    loader.load_all()

    command = loader.get_command("test-cmd")
    assert command is not None
    assert command.name == "test-cmd"

    # Non-existent command
    assert loader.get_command("nonexistent") is None


def test_list_commands(tmp_commands_dir):
    """Test listing all loaded command names."""
    (tmp_commands_dir / "cmd1.md").write_text("---\nname: cmd1\n---\nTask")
    (tmp_commands_dir / "cmd2.md").write_text("---\nname: cmd2\n---\nTask")

    loader = CommandLoader(tmp_commands_dir)
    loader.load_all()

    commands_list = loader.list_commands()
    assert len(commands_list) == 2
    assert "cmd1" in commands_list
    assert "cmd2" in commands_list


def test_loader_repr(tmp_commands_dir):
    """Test string representation of loader."""
    loader = CommandLoader(tmp_commands_dir)

    repr_str = repr(loader)
    assert "CommandLoader" in repr_str
    assert str(tmp_commands_dir) in repr_str
    assert "commands=0" in repr_str

    # After loading
    (tmp_commands_dir / "test.md").write_text("---\nname: test\n---\nTask")
    loader.load_all()

    repr_str = repr(loader)
    assert "commands=1" in repr_str


def test_load_command_with_complex_template(tmp_commands_dir):
    """Test loading command with complex Markdown template."""
    cmd_file = tmp_commands_dir / "complex.md"
    cmd_file.write_text(
        """---
name: complex
description: Complex command
---

# Context

- Status: !`git status`
- Branch: !`git branch`

## Task

1. First step
2. Second step
3. Third step

```python
# Code example
def hello():
    print("Hello")
```

**Important**: Do this carefully!
"""
    )

    loader = CommandLoader(tmp_commands_dir)
    command = loader.load_command(cmd_file)

    assert "# Context" in command.template
    assert "!`git status`" in command.template
    assert "```python" in command.template
    assert "**Important**" in command.template
