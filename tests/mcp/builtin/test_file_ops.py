"""Tests for file_ops MCP tools."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kagura.mcp.builtin.file_ops import dir_list, file_read, file_write, shell_exec


class TestFileRead:
    """Test file_read MCP tool."""

    def test_file_read_success(self) -> None:
        """Test reading a file successfully."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            result = file_read(temp_path)
            assert result == "Hello, World!"
        finally:
            Path(temp_path).unlink()

    def test_file_read_with_encoding(self) -> None:
        """Test reading a file with specific encoding."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write("日本語テスト")
            temp_path = f.name

        try:
            result = file_read(temp_path, encoding="utf-8")
            assert result == "日本語テスト"
        finally:
            Path(temp_path).unlink()

    def test_file_read_not_found(self) -> None:
        """Test reading a non-existent file returns error."""
        result = file_read("/nonexistent/file/path.txt")
        assert "Error reading file" in result

    def test_file_read_permission_error(self) -> None:
        """Test reading a file with permission error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            # Change permissions to make it unreadable
            Path(temp_path).chmod(0o000)

            result = file_read(temp_path)
            assert "Error reading file" in result
        finally:
            # Restore permissions and cleanup
            try:
                Path(temp_path).chmod(0o644)
                Path(temp_path).unlink()
            except Exception:
                pass


class TestFileWrite:
    """Test file_write MCP tool."""

    def test_file_write_success(self) -> None:
        """Test writing to a file successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = str(Path(tmpdir) / "test.txt")

            result = file_write(file_path, "Test content")

            # Verify return message
            assert "Wrote 12 characters" in result
            assert file_path in result

            # Verify file content
            assert Path(file_path).read_text() == "Test content"

    def test_file_write_overwrite(self) -> None:
        """Test overwriting an existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Original content")
            temp_path = f.name

        try:
            result = file_write(temp_path, "New content")

            assert "Wrote 11 characters" in result
            assert Path(temp_path).read_text() == "New content"
        finally:
            Path(temp_path).unlink()

    def test_file_write_japanese(self) -> None:
        """Test writing Japanese characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = str(Path(tmpdir) / "japanese.txt")

            result = file_write(file_path, "日本語テスト", encoding="utf-8")

            # "日本語テスト" is 6 characters
            assert "Wrote 6 characters" in result
            assert Path(file_path).read_text(encoding="utf-8") == "日本語テスト"

    def test_file_write_error(self) -> None:
        """Test writing to an invalid path returns error."""
        result = file_write("/invalid/nonexistent/path/file.txt", "content")
        assert "Error writing file" in result


class TestDirList:
    """Test dir_list MCP tool."""

    def test_dir_list_all_files(self) -> None:
        """Test listing all files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("test")
            (Path(tmpdir) / "file2.py").write_text("test")
            (Path(tmpdir) / "file3.md").write_text("test")

            result = dir_list(tmpdir, pattern="*")

            # Parse JSON result
            files = json.loads(result)
            assert isinstance(files, list)
            assert len(files) == 3
            assert "file1.txt" in files
            assert "file2.py" in files
            assert "file3.md" in files

    def test_dir_list_with_pattern(self) -> None:
        """Test listing files with a glob pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.txt").write_text("test")
            (Path(tmpdir) / "test2.txt").write_text("test")
            (Path(tmpdir) / "test3.py").write_text("test")

            result = dir_list(tmpdir, pattern="*.txt")

            files = json.loads(result)
            assert len(files) == 2
            assert "test1.txt" in files
            assert "test2.txt" in files
            assert "test3.py" not in files

    def test_dir_list_recursive(self) -> None:
        """Test listing files recursively."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            (Path(tmpdir) / "file1.md").write_text("test")
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file2.md").write_text("test")

            result = dir_list(tmpdir, pattern="**/*.md")

            files = json.loads(result)
            assert len(files) == 2
            # Both files should be found recursively

    def test_dir_list_empty_directory(self) -> None:
        """Test listing an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = dir_list(tmpdir, pattern="*")

            files = json.loads(result)
            assert isinstance(files, list)
            assert len(files) == 0

    def test_dir_list_nonexistent_path(self) -> None:
        """Test listing a non-existent directory returns error or empty list."""
        result = dir_list("/nonexistent/directory/path")

        parsed = json.loads(result)
        # Implementation returns either error dict or empty list
        if isinstance(parsed, dict):
            assert "error" in parsed
        elif isinstance(parsed, list):
            # Some implementations may return empty list for non-existent path
            assert len(parsed) == 0

    def test_dir_list_sorted(self) -> None:
        """Test that file list is sorted alphabetically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in non-alphabetical order
            (Path(tmpdir) / "zebra.txt").write_text("test")
            (Path(tmpdir) / "alpha.txt").write_text("test")
            (Path(tmpdir) / "beta.txt").write_text("test")

            result = dir_list(tmpdir, pattern="*")

            files = json.loads(result)
            assert files == sorted(files)
            assert files == ["alpha.txt", "beta.txt", "zebra.txt"]


class TestShellExec:
    """Test shell_exec MCP tool."""

    @pytest.mark.asyncio
    async def test_shell_exec_success(self) -> None:
        """Test executing a shell command successfully."""
        from dataclasses import dataclass

        @dataclass
        class ExecResult:
            """Mock exec result."""

            stdout: str
            stderr: str

        mock_executor = AsyncMock()
        mock_executor.exec.return_value = ExecResult(stdout="Command output", stderr="")

        # ShellExecutor is imported dynamically inside the function
        with patch("kagura.core.shell.ShellExecutor", return_value=mock_executor):
            result = await shell_exec("echo test")

            assert result == "Command output"
            mock_executor.exec.assert_called_once_with("echo test")

    @pytest.mark.asyncio
    async def test_shell_exec_stderr(self) -> None:
        """Test shell command that outputs to stderr."""
        from dataclasses import dataclass

        @dataclass
        class ExecResult:
            """Mock exec result."""

            stdout: str
            stderr: str

        mock_executor = AsyncMock()
        mock_executor.exec.return_value = ExecResult(stdout="", stderr="Error message")

        # ShellExecutor is imported dynamically inside the function
        with patch("kagura.core.shell.ShellExecutor", return_value=mock_executor):
            result = await shell_exec("invalid_command")

            assert result == "Error message"

    @pytest.mark.asyncio
    async def test_shell_exec_import_error(self) -> None:
        """Test shell_exec handles ImportError gracefully."""
        # ShellExecutor is imported dynamically inside the function
        with patch(
            "kagura.core.shell.ShellExecutor",
            side_effect=ImportError("Module not found"),
        ):
            result = await shell_exec("test command")

            assert "Error executing command" in result
