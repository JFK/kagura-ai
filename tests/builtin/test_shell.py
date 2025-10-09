"""Tests for builtin shell agent."""

import pytest

from kagura.builtin.shell import shell


class TestShellAgent:
    """Tests for shell built-in agent."""

    @pytest.mark.asyncio
    async def test_shell_basic_command(self):
        """Test basic shell command execution."""
        result = await shell("echo 'test output'")

        assert isinstance(result, str)
        assert "test output" in result

    @pytest.mark.asyncio
    async def test_shell_ls_command(self):
        """Test ls command."""
        result = await shell("ls")

        assert isinstance(result, str)
        # Should list some files
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_shell_pwd_command(self):
        """Test pwd command."""
        result = await shell("pwd")

        assert isinstance(result, str)
        assert "/" in result  # Should contain path separator

    @pytest.mark.asyncio
    async def test_shell_with_working_dir(self, tmp_path):
        """Test shell command with custom working directory."""
        # Create test file
        test_file = tmp_path / "marker.txt"
        test_file.write_text("marker")

        result = await shell("ls", working_dir=str(tmp_path))

        assert "marker.txt" in result

    @pytest.mark.asyncio
    async def test_shell_command_failure(self):
        """Test shell command that fails raises RuntimeError."""
        with pytest.raises(RuntimeError, match="Command failed"):
            await shell("ls /this_directory_does_not_exist_xyz")
