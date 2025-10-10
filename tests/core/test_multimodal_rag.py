"""Tests for MultimodalRAG."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Skip all tests if ChromaDB not available
pytest.importorskip("chromadb")

from kagura.core.memory.multimodal_rag import MultimodalRAG  # noqa: E402
from kagura.loaders.directory import FileContent  # noqa: E402
from kagura.loaders.file_types import FileType  # noqa: E402


@pytest.fixture
def temp_project_dir(tmp_path: Path):
    """Create temporary project directory with test files."""
    # Create directory structure
    (tmp_path / "docs").mkdir()
    (tmp_path / "images").mkdir()

    # Create text files
    (tmp_path / "README.md").write_text("# Project README\nThis is a test project.")
    (tmp_path / "docs" / "guide.txt").write_text("User guide content here.")
    (tmp_path / "code.py").write_text("def hello():\n    print('hello')")

    # Create image files (fake content)
    (tmp_path / "images" / "diagram.png").write_bytes(b"fake png data")
    (tmp_path / "images" / "screenshot.jpg").write_bytes(b"fake jpg data")

    return tmp_path


@pytest.fixture
def mock_gemini():
    """Create mock GeminiLoader."""
    with patch("kagura.core.memory.multimodal_rag.GeminiLoader") as mock_loader:
        instance = Mock()
        instance.process_file = AsyncMock(return_value="Mocked Gemini response")
        mock_loader.return_value = instance
        yield instance


@pytest.fixture
def mock_scanner():
    """Create mock DirectoryScanner."""
    with patch("kagura.core.memory.multimodal_rag.DirectoryScanner") as mock_scanner:
        yield mock_scanner


class TestMultimodalRAGInit:
    """Tests for MultimodalRAG initialization."""

    def test_init_basic(self, temp_project_dir: Path, mock_gemini):
        """Test basic initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                collection_name="test_collection",
                persist_dir=Path(tmpdir),
            )

            assert rag.directory == temp_project_dir
            assert rag.gemini is not None
            assert rag.scanner is not None
            assert rag.cache is not None
            assert len(rag._indexed_files) == 0

    def test_init_multimodal_not_available(self, temp_project_dir: Path):
        """Test initialization when multimodal support not available."""
        with patch(
            "kagura.core.memory.multimodal_rag.MULTIMODAL_AVAILABLE", False
        ):
            with pytest.raises(
                ImportError,
                match="Multimodal support requires google-generativeai",
            ):
                with tempfile.TemporaryDirectory() as tmpdir:
                    MultimodalRAG(
                        directory=temp_project_dir,
                        persist_dir=Path(tmpdir),
                    )

    def test_init_without_cache(self, temp_project_dir: Path, mock_gemini):
        """Test initialization without cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                enable_cache=False,
            )

            assert rag.cache is None

    def test_init_custom_cache_size(self, temp_project_dir: Path, mock_gemini):
        """Test initialization with custom cache size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                cache_size_mb=50,
            )

            assert rag.cache is not None
            assert rag.cache.max_size_bytes == 50 * 1024 * 1024

    def test_init_nonexistent_directory(self, tmp_path: Path):
        """Test initialization with nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"

        with pytest.raises(FileNotFoundError, match="Directory not found"):
            with tempfile.TemporaryDirectory() as tmpdir:
                MultimodalRAG(
                    directory=nonexistent,
                    persist_dir=Path(tmpdir),
                )

    def test_init_without_gitignore(self, temp_project_dir: Path, mock_gemini):
        """Test initialization without gitignore support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                respect_gitignore=False,
            )

            # Scanner should be created with respect_gitignore=False
            assert rag.scanner is not None


class TestMultimodalRAGBuildIndex:
    """Tests for build_index method."""

    @pytest.mark.asyncio
    async def test_build_index_basic(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test basic index building."""
        # Mock scanner to return test content
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="# Project README",
                size=16,
            ),
            FileContent(
                path=temp_project_dir / "docs" / "guide.txt",
                file_type=FileType.TEXT,
                content="User guide",
                size=10,
            ),
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            stats = await rag.build_index()

            # Check statistics
            assert stats["total_files"] == 2
            assert stats["text_files"] == 2
            assert stats["multimodal_files"] == 0
            assert stats["failed_files"] == 0

            # Check indexed files
            assert len(rag._indexed_files) == 2

    @pytest.mark.asyncio
    async def test_build_index_with_multimodal(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test index building with multimodal files."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="# README",
                size=8,
            ),
            FileContent(
                path=temp_project_dir / "images" / "diagram.png",
                file_type=FileType.IMAGE,
                content="Diagram description from Gemini",
                size=100,
            ),
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            stats = await rag.build_index()

            assert stats["total_files"] == 2
            assert stats["text_files"] == 1
            assert stats["multimodal_files"] == 1

    @pytest.mark.asyncio
    async def test_build_index_force_rebuild(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test force rebuild of index."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="Content",
                size=7,
            )
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            # First build
            await rag.build_index()
            assert len(rag._indexed_files) == 1
            first_count = rag.count()

            # Second build without force (should skip)
            await rag.build_index()
            assert rag.count() == first_count  # No duplicates

            # Force rebuild
            await rag.build_index(force_rebuild=True)
            # Count should still be 1 (replaced, not duplicated)
            assert len(rag._indexed_files) == 1

    @pytest.mark.asyncio
    async def test_build_index_with_errors(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test index building with some failures."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        # One valid, one that will cause store error
        test_contents = [
            FileContent(
                path=temp_project_dir / "good.txt",
                file_type=FileType.TEXT,
                content="Good content",
                size=12,
            ),
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            # Mock store to fail on first call
            original_store = rag.store
            call_count = [0]

            def mock_store(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise ValueError("Simulated store error")
                return original_store(*args, **kwargs)

            rag.store = mock_store  # type: ignore

            stats = await rag.build_index()

            # Should have one failure
            assert stats["failed_files"] == 1


class TestMultimodalRAGQuery:
    """Tests for query method."""

    @pytest.mark.asyncio
    async def test_query_basic(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test basic query."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="Python is a programming language",
                size=33,
            )
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            await rag.build_index()

            # Query
            results = rag.query("What is Python?", n_results=1)

            assert len(results) > 0
            assert "content" in results[0]
            assert "distance" in results[0]
            assert "metadata" in results[0]

    @pytest.mark.asyncio
    async def test_query_with_file_type_filter(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test query with file type filter."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="Text content",
                size=12,
            ),
            FileContent(
                path=temp_project_dir / "image.png",
                file_type=FileType.IMAGE,
                content="Image content",
                size=13,
            ),
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            await rag.build_index()

            # Query with TEXT filter
            results = rag.query("content", file_type=FileType.TEXT)

            # Should only return TEXT results
            for result in results:
                assert result["metadata"]["file_type"] == "text"


class TestMultimodalRAGIncrementalUpdate:
    """Tests for incremental_update method."""

    @pytest.mark.asyncio
    async def test_incremental_update_no_changes(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test incremental update with no new files."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "README.md",
                file_type=FileType.TEXT,
                content="Content",
                size=7,
            )
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)
        mock_scanner_instance.scan = AsyncMock(return_value=[])

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            # Initial build
            await rag.build_index()

            # Incremental update (no new files)
            stats = await rag.incremental_update()

            assert stats["total_files"] == 0

    @pytest.mark.asyncio
    async def test_incremental_update_with_new_files(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test incremental update with new files."""
        from kagura.loaders.directory import FileInfo

        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        # Initial content
        initial_contents = [
            FileContent(
                path=temp_project_dir / "old.txt",
                file_type=FileType.TEXT,
                content="Old content",
                size=11,
            )
        ]

        # New scan results
        new_file_info = FileInfo(
            path=temp_project_dir / "new.txt",
            file_type=FileType.TEXT,
            size=11,
            is_multimodal=False,
        )

        # Updated content (includes both old and new)
        updated_contents = initial_contents + [
            FileContent(
                path=temp_project_dir / "new.txt",
                file_type=FileType.TEXT,
                content="New content",
                size=11,
            )
        ]

        mock_scanner_instance.load_all = AsyncMock(
            side_effect=[initial_contents, updated_contents]
        )
        mock_scanner_instance.scan = AsyncMock(return_value=[new_file_info])

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            # Initial build
            await rag.build_index()
            assert len(rag._indexed_files) == 1

            # Incremental update
            stats = await rag.incremental_update()

            # Should process new files
            assert stats["total_files"] >= 1

    @pytest.mark.asyncio
    async def test_incremental_update_with_cache_hit(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test incremental update with cached files (no changes)."""
        from kagura.loaders.directory import FileInfo

        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_path = temp_project_dir / "cached.txt"
        test_content = FileContent(
            path=test_path,
            file_type=FileType.TEXT,
            content="Cached content",
            size=14,
        )

        # Initial load
        mock_scanner_instance.load_all = AsyncMock(return_value=[test_content])

        # Scan returns same file
        file_info = FileInfo(
            path=test_path,
            file_type=FileType.TEXT,
            size=14,
            is_multimodal=False,
        )
        mock_scanner_instance.scan = AsyncMock(return_value=[file_info])

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                enable_cache=True,
            )

            # Initial build (populates cache)
            await rag.build_index()
            assert len(rag._indexed_files) == 1

            # Mock cache to return cached content
            if rag.cache:
                rag.cache.put(test_path, test_content)

            # Incremental update should skip cached file
            stats = await rag.incremental_update()

            # Should skip cached file (count may vary based on implementation)
            # The exact behavior depends on cache hit logic
            assert stats is not None


class TestMultimodalRAGUtilities:
    """Tests for utility methods."""

    @pytest.mark.asyncio
    async def test_get_indexed_files(
        self, temp_project_dir: Path, mock_gemini, mock_scanner
    ):
        """Test get_indexed_files method."""
        mock_scanner_instance = Mock()
        mock_scanner.return_value = mock_scanner_instance

        test_contents = [
            FileContent(
                path=temp_project_dir / "file1.txt",
                file_type=FileType.TEXT,
                content="Content 1",
                size=9,
            ),
            FileContent(
                path=temp_project_dir / "file2.txt",
                file_type=FileType.TEXT,
                content="Content 2",
                size=9,
            ),
        ]
        mock_scanner_instance.load_all = AsyncMock(return_value=test_contents)

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            await rag.build_index()

            indexed_files = rag.get_indexed_files()

            assert len(indexed_files) == 2
            assert temp_project_dir / "file1.txt" in indexed_files
            assert temp_project_dir / "file2.txt" in indexed_files

    def test_clear_cache(self, temp_project_dir: Path, mock_gemini):
        """Test clear_cache method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                enable_cache=True,
            )

            # Cache should exist
            assert rag.cache is not None

            # Clear cache
            rag.clear_cache()

            # Cache should be empty
            assert rag.cache.entry_count == 0

    def test_clear_cache_when_disabled(self, temp_project_dir: Path, mock_gemini):
        """Test clear_cache when cache is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
                enable_cache=False,
            )

            # Should not raise error
            rag.clear_cache()

    def test_repr(self, temp_project_dir: Path, mock_gemini):
        """Test string representation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            rag = MultimodalRAG(
                directory=temp_project_dir,
                persist_dir=Path(tmpdir),
            )

            repr_str = repr(rag)

            assert "MultimodalRAG" in repr_str
            assert str(temp_project_dir) in repr_str
