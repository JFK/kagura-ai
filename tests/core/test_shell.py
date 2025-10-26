"""Tests for ShellExecutor."""

import pytest

from kagura.core.shell import (
    SecurityError,
    ShellExecutor,
    ShellResult,
    UserCancelledError,
)


class TestShellExecutor:
    """Tests for ShellExecutor class."""

    @pytest.mark.asyncio
    async def test_exec_basic_command(self):
        """Test basic command execution."""
        executor = ShellExecutor()
        result = await executor.exec("echo 'hello world'")

        assert result.success
        assert "hello world" in result.stdout
        assert result.return_code == 0

    @pytest.mark.asyncio
    async def test_exec_with_error(self):
        """Test command that fails."""
        executor = ShellExecutor()
        result = await executor.exec("ls /nonexistent_directory_xyz")

        assert not result.success
        assert result.return_code != 0
        assert result.stderr != ""

    @pytest.mark.asyncio
    async def test_validate_command_allowed(self):
        """Test command validation with whitelist."""
        executor = ShellExecutor(allowed_commands=["echo", "ls"])

        # Should pass
        assert executor.validate_command("echo hello")
        assert executor.validate_command("ls -la")

    @pytest.mark.asyncio
    async def test_validate_command_not_allowed(self):
        """Test command validation rejects non-whitelisted commands."""
        executor = ShellExecutor(allowed_commands=["echo", "ls"])

        # Should raise SecurityError (for a safe but non-whitelisted command)
        with pytest.raises(SecurityError, match="Command not allowed"):
            executor.validate_command("python3 --version")

    @pytest.mark.asyncio
    async def test_validate_command_blocked(self):
        """Test command validation with blacklist."""
        # Test with empty whitelist to focus on blacklist
        executor = ShellExecutor(
            allowed_commands=None,
            blocked_commands={"sudo": "exact", "rm -rf /": "pattern"},
        )

        # Should raise SecurityError for blocked commands
        with pytest.raises(SecurityError, match="Blocked command"):
            executor.validate_command("sudo rm -rf /")

        with pytest.raises(SecurityError, match="Blocked command"):
            executor.validate_command("echo test && rm -rf / && echo done")

    @pytest.mark.asyncio
    async def test_validate_command_empty(self):
        """Test validation rejects empty command."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Empty command"):
            executor.validate_command("")

    @pytest.mark.asyncio
    async def test_timeout(self):
        """Test command timeout enforcement."""
        executor = ShellExecutor(
            timeout=1,
            allowed_commands=["sleep"],  # Allow sleep for this test
        )

        with pytest.raises(TimeoutError, match="timed out"):
            await executor.exec("sleep 10")

    @pytest.mark.asyncio
    async def test_working_directory(self, tmp_path):
        """Test command execution in specific working directory."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        executor = ShellExecutor(working_dir=tmp_path)
        result = await executor.exec("ls")

        assert result.success
        assert "test.txt" in result.stdout


class TestShellResult:
    """Tests for ShellResult class."""

    def test_success_property(self):
        """Test success property."""
        result_success = ShellResult(
            return_code=0, stdout="output", stderr="", command="echo test"
        )
        result_failed = ShellResult(
            return_code=1, stdout="", stderr="error", command="false"
        )

        assert result_success.success
        assert not result_failed.success

    def test_str_representation(self):
        """Test string representation."""
        result_success = ShellResult(
            return_code=0, stdout="success output", stderr="", command="cmd"
        )
        result_failed = ShellResult(
            return_code=1, stdout="", stderr="error output", command="cmd"
        )

        assert str(result_success) == "success output"
        assert str(result_failed) == "error output"

    def test_repr(self):
        """Test repr representation."""
        result = ShellResult(
            return_code=0, stdout="output", stderr="", command="test_cmd"
        )

        repr_str = repr(result)
        assert "success" in repr_str
        assert "test_cmd" in repr_str


class TestSecurityErrors:
    """Tests for security error handling."""

    def test_security_error_raised(self):
        """Test SecurityError can be raised and caught."""
        with pytest.raises(SecurityError):
            raise SecurityError("Test security violation")

    def test_user_cancelled_error_raised(self):
        """Test UserCancelledError can be raised and caught."""
        with pytest.raises(UserCancelledError):
            raise UserCancelledError("Test user cancellation")


class TestShellExecutorSecurityPolicy:
    """Test security policy validation with precise command matching (RFC-027)."""

    @pytest.mark.asyncio
    async def test_blocked_command_in_path_allowed(self, tmp_path):
        """Path containing blocked command name should be allowed."""
        # Create path with "dd" in it (common in temp paths like dnddt_test)
        test_dir = tmp_path / "dnddt_test_directory"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("# test")

        executor = ShellExecutor(working_dir=tmp_path)

        # Should not raise SecurityError - "dd" is in path, not command
        result = await executor.exec(f'find {test_dir} -name "*.py"')
        assert result.success
        assert "test.py" in result.stdout

    @pytest.mark.asyncio
    async def test_blocked_command_name_rejected(self):
        """Command 'dd' itself should be blocked."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command: dd"):
            await executor.exec("dd if=/dev/zero of=/tmp/test bs=1M count=1")

    @pytest.mark.asyncio
    async def test_dangerous_pattern_rejected(self):
        """Dangerous patterns should be blocked."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command pattern: rm -rf /"):
            await executor.exec("rm -rf / --no-preserve-root")

    @pytest.mark.asyncio
    async def test_eval_command_blocked(self):
        """eval command should be blocked."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command: eval"):
            await executor.exec('eval "echo malicious"')

    @pytest.mark.asyncio
    async def test_allowed_command_with_dd_in_args(self):
        """Allowed command with 'dd' in arguments should work."""
        executor = ShellExecutor()

        # 'echo' is allowed, 'dd' appears only in arguments
        result = await executor.exec('echo "added some text"')
        assert result.success
        assert "added some text" in result.stdout

    @pytest.mark.asyncio
    async def test_source_command_blocked(self):
        """source command should be blocked."""
        executor = ShellExecutor()

        with pytest.raises(SecurityError, match="Blocked command: source"):
            await executor.exec("source /tmp/malicious.sh")
