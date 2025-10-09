"""Tests for builtin file agents."""

import pytest

from kagura.builtin.file import file_search, grep_content


class TestFileAgents:
    """Tests for file built-in agents."""

    @pytest.mark.asyncio
    async def test_file_search_basic(self, tmp_path):
        """Test file_search finds files."""
        # Create test files
        (tmp_path / "test1.py").write_text("# test file 1")
        (tmp_path / "test2.py").write_text("# test file 2")
        (tmp_path / "other.txt").write_text("other file")

        result = await file_search(
            pattern="test", directory=str(tmp_path), file_type="*.py"
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert any("test1.py" in f for f in result)
        assert any("test2.py" in f for f in result)

    @pytest.mark.asyncio
    async def test_file_search_no_matches(self, tmp_path):
        """Test file_search with no matches returns empty list."""
        result = await file_search(
            pattern="nonexistent", directory=str(tmp_path), file_type="*.xyz"
        )

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_file_search_all_types(self, tmp_path):
        """Test file_search with wildcard file type."""
        (tmp_path / "file1.py").write_text("content")
        (tmp_path / "file2.txt").write_text("content")

        result = await file_search(
            pattern="file", directory=str(tmp_path), file_type="*"
        )

        assert isinstance(result, list)
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_grep_content_finds_matches(self, tmp_path):
        """Test grep_content finds pattern in files."""
        # Create test files with content
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"

        file1.write_text("This has TODO: fix this\nAnother line")
        file2.write_text("No todos here")
        file3.write_text("TODO: another task\nTODO: second task")

        result = await grep_content(
            pattern="TODO", files=[str(file1), str(file2), str(file3)]
        )

        assert isinstance(result, dict)
        # file1 and file3 should have matches
        assert str(file1) in result
        assert str(file3) in result
        # file2 should not have matches
        assert str(file2) not in result

        # Check match counts
        assert len(result[str(file1)]) == 1
        assert len(result[str(file3)]) == 2

    @pytest.mark.asyncio
    async def test_grep_content_no_matches(self, tmp_path):
        """Test grep_content with no matches returns empty dict."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("No pattern here")

        result = await grep_content(pattern="NONEXISTENT", files=[str(file1)])

        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_grep_content_nonexistent_file(self):
        """Test grep_content with nonexistent file."""
        result = await grep_content(
            pattern="test", files=["/nonexistent/file/path.txt"]
        )

        # Should return empty dict (no matches)
        assert isinstance(result, dict)
        assert len(result) == 0
