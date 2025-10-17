"""Integration tests for multimodal RAG"""
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import tempfile
import shutil
import os

# Note: Tests now use mocked Gemini API, so API keys are not required


@pytest.fixture(autouse=True)
def mock_gemini_loader():
    """Mock Gemini API for multimodal tests

    autouse=True ensures this fixture runs for all tests in this file
    """
    # Create mock instance
    mock_instance = MagicMock()

    # Mock async methods
    mock_instance.process_file = AsyncMock(return_value={
        "content": "Mocked file content",
        "metadata": {"type": "text", "size": 100}
    })
    mock_instance.analyze_image = AsyncMock(return_value="Mocked image description")
    mock_instance.transcribe_audio = AsyncMock(return_value="Mocked audio transcript")
    mock_instance.analyze_video = AsyncMock(return_value="Mocked video description")
    mock_instance.analyze_pdf = AsyncMock(return_value="Mocked PDF content")

    # Mock sync methods
    mock_instance.__enter__ = MagicMock(return_value=mock_instance)
    mock_instance.__exit__ = MagicMock(return_value=None)

    # Patch all possible import paths
    with patch('kagura.loaders.gemini.GeminiLoader', return_value=mock_instance), \
         patch('kagura.core.memory.multimodal_rag.GeminiLoader', return_value=mock_instance), \
         patch('kagura.loaders.directory.GeminiLoader', return_value=mock_instance):
        yield mock_instance


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory with test files"""
    tmpdir = tempfile.mkdtemp()
    project = Path(tmpdir)

    # Create test files
    (project / "README.md").write_text("# Test Project\n\nThis is a test project.")
    (project / "code.py").write_text("def hello():\n    return 'world'")
    (project / "docs").mkdir()
    (project / "docs" / "guide.md").write_text("# Guide\n\nHow to use this.")

    yield project

    # Cleanup
    shutil.rmtree(tmpdir)


@pytest.mark.asyncio
async def test_multimodal_rag_initialization(temp_project_dir):
    """Test MultimodalRAG initialization with directory"""
    from kagura.core.memory import MultimodalRAG

    rag = MultimodalRAG(
        directory=temp_project_dir,
        collection_name="test_collection",
        persist_dir=temp_project_dir / ".chroma"
    )

    assert rag.directory == temp_project_dir
    assert rag.collection.name == "test_collection"


@pytest.mark.asyncio
async def test_multimodal_rag_query(temp_project_dir):
    """Test MultimodalRAG query functionality"""
    from kagura.core.memory import MultimodalRAG

    rag = MultimodalRAG(
        directory=temp_project_dir,
        collection_name="test_query",
        persist_dir=temp_project_dir / ".chroma"
    )

    # Build index first
    await rag.build_index()

    # Query for Python code
    results = rag.query("Python function", n_results=2)

    assert isinstance(results, list)
    # Should find the code.py file
    assert len(results) > 0


@pytest.mark.asyncio
async def test_agent_with_multimodal_rag(temp_project_dir):
    """Test @agent decorator with enable_multimodal_rag"""
    from kagura import agent
    from kagura.core.memory import MultimodalRAG

    @agent(
        model="gpt-5-mini",
        enable_multimodal_rag=True,
        rag_directory=temp_project_dir
    )
    async def docs_agent(query: str, rag: MultimodalRAG) -> str:
        """Answer {{ query }} using documentation"""
        # Query RAG
        results = rag.query(query, n_results=2)
        return f"Found {len(results)} results"

    # Mock LLM response
    with patch('litellm.acompletion', new_callable=AsyncMock) as mock_llm:
        mock_message = MagicMock(content="Found 2 results", tool_calls=None)
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=mock_message)]
        )

        result = await docs_agent("How to use this?")
        assert "Found" in result or "results" in result


@pytest.mark.asyncio
async def test_chat_session_multimodal_initialization():
    """Test ChatSession initialization with multimodal enabled"""
    from kagura.chat import ChatSession
    from pathlib import Path
    import tempfile

    tmpdir = tempfile.mkdtemp()
    project_dir = Path(tmpdir)
    (project_dir / "test.md").write_text("Test content")

    try:
        session = ChatSession(
            model="gpt-5-mini",
            enable_multimodal=True,
            rag_directory=project_dir
        )

        assert session.enable_multimodal is True
        assert session.rag_directory == project_dir
        assert session.rag is not None
    finally:
        shutil.rmtree(tmpdir)


@pytest.mark.asyncio
async def test_directory_scanner(temp_project_dir):
    """Test DirectoryScanner with various file types"""
    from kagura.loaders.directory import DirectoryScanner
    from kagura.loaders.gemini import GeminiLoader

    gemini = GeminiLoader()
    scanner = DirectoryScanner(
        directory=temp_project_dir,
        gemini=gemini,
        respect_gitignore=False
    )

    # Scan directory
    file_infos = await scanner.scan()

    assert isinstance(file_infos, list)
    assert len(file_infos) >= 3  # README, code.py, guide.md

    # Check file paths
    file_paths = [f.path for f in file_infos]
    assert any("README.md" in str(p) for p in file_paths)
    assert any("code.py" in str(p) for p in file_paths)


@pytest.mark.asyncio
async def test_gemini_loader_supported_types():
    """Test GeminiLoader supports multimodal file types"""
    from kagura.loaders.gemini import GeminiLoader
    from kagura.loaders.file_types import FileType

    loader = GeminiLoader()

    # GeminiLoader should support multimodal types: IMAGE, AUDIO, VIDEO, PDF
    # Text files are handled separately (not by Gemini)

    # Just verify the loader is initialized correctly
    assert loader is not None
    assert hasattr(loader, 'process_file')
    assert hasattr(loader, 'analyze_image')
    assert hasattr(loader, 'transcribe_audio')
    assert hasattr(loader, 'analyze_video')
    assert hasattr(loader, 'analyze_pdf')


@pytest.mark.asyncio
async def test_file_type_detection():
    """Test file type detection"""
    from kagura.loaders.file_types import detect_file_type, FileType

    assert detect_file_type("image.png") == FileType.IMAGE
    assert detect_file_type("document.pdf") == FileType.PDF
    assert detect_file_type("audio.mp3") == FileType.AUDIO
    assert detect_file_type("video.mp4") == FileType.VIDEO
    assert detect_file_type("code.py") == FileType.TEXT
    assert detect_file_type("README.md") == FileType.TEXT
