"""Tests for Gemini loader."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kagura.loaders.gemini import GEMINI_AVAILABLE

# Skip all tests if Gemini is not available
pytestmark = pytest.mark.skipif(
    not GEMINI_AVAILABLE, reason="google-generativeai not installed"
)


@pytest.fixture
def mock_genai():
    """Mock google.generativeai module."""
    with patch("kagura.loaders.gemini.genai") as mock:
        # Mock upload_file
        mock.upload_file = MagicMock(return_value="mock_uploaded_file")

        # Mock GenerativeModel
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Mock response text"
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock.GenerativeModel = MagicMock(return_value=mock_model)

        yield mock


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary test file."""
    test_file = tmp_path / "test.png"
    test_file.write_text("mock image data")
    return test_file


class TestGeminiLoaderInit:
    """Tests for GeminiLoader initialization."""

    def test_init_with_api_key(self, mock_genai):
        """Test initialization with explicit API key."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        assert loader.api_key == "test_key"
        # Default model from GOOGLE_AI_DEFAULT_MODEL env var (without gemini/ prefix)
        assert loader.model_name == "gemini-2.0-flash-exp"

    def test_init_with_env_var(self, mock_genai, monkeypatch):
        """Test initialization with environment variable."""
        from kagura.loaders.gemini import GeminiLoader

        monkeypatch.setenv("GOOGLE_API_KEY", "env_test_key")
        loader = GeminiLoader()
        assert loader.api_key == "env_test_key"

    def test_init_without_api_key(self, mock_genai, monkeypatch):
        """Test initialization without API key raises error."""
        from kagura.loaders.gemini import GeminiLoader

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Google API key not found"):
            GeminiLoader()

    def test_init_custom_model(self, mock_genai):
        """Test initialization with custom model."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(model="gemini-2.5-pro", api_key="test_key")
        assert loader.model_name == "gemini-2.5-pro"


class TestGeminiLoaderAnalyzeImage:
    """Tests for analyze_image method."""

    @pytest.mark.asyncio
    async def test_analyze_image(self, mock_genai, temp_test_file):
        """Test image analysis."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        result = await loader.analyze_image(temp_test_file, "Describe this")

        assert result == "Mock response text"
        mock_genai.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_image_japanese(self, mock_genai, temp_test_file):
        """Test image analysis in Japanese."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        result = await loader.analyze_image(
            temp_test_file, "この画像を説明", language="ja"
        )

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_analyze_image_file_not_found(self, mock_genai):
        """Test image analysis with non-existent file."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        with pytest.raises(FileNotFoundError):
            await loader.analyze_image("nonexistent.png", "Describe this")


class TestGeminiLoaderTranscribeAudio:
    """Tests for transcribe_audio method."""

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, mock_genai, tmp_path):
        """Test audio transcription."""
        from kagura.loaders.gemini import GeminiLoader

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("mock audio data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.transcribe_audio(audio_file)

        assert result == "Mock response text"
        mock_genai.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_english(self, mock_genai, tmp_path):
        """Test audio transcription in English."""
        from kagura.loaders.gemini import GeminiLoader

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("mock audio data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.transcribe_audio(audio_file, language="en")

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, mock_genai):
        """Test audio transcription with non-existent file."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        with pytest.raises(FileNotFoundError):
            await loader.transcribe_audio("nonexistent.mp3")


class TestGeminiLoaderAnalyzeVideo:
    """Tests for analyze_video method."""

    @pytest.mark.asyncio
    async def test_analyze_video(self, mock_genai, tmp_path):
        """Test video analysis."""
        from kagura.loaders.gemini import GeminiLoader

        video_file = tmp_path / "test.mp4"
        video_file.write_text("mock video data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.analyze_video(video_file, "Summarize this video")

        assert result == "Mock response text"
        mock_genai.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_video_file_not_found(self, mock_genai):
        """Test video analysis with non-existent file."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        with pytest.raises(FileNotFoundError):
            await loader.analyze_video("nonexistent.mp4", "Summarize this")


class TestGeminiLoaderAnalyzePDF:
    """Tests for analyze_pdf method."""

    @pytest.mark.asyncio
    async def test_analyze_pdf(self, mock_genai, tmp_path):
        """Test PDF analysis."""
        from kagura.loaders.gemini import GeminiLoader

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("mock pdf data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.analyze_pdf(pdf_file, "Summarize this document")

        assert result == "Mock response text"
        mock_genai.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_pdf_file_not_found(self, mock_genai):
        """Test PDF analysis with non-existent file."""
        from kagura.loaders.gemini import GeminiLoader

        loader = GeminiLoader(api_key="test_key")
        with pytest.raises(FileNotFoundError):
            await loader.analyze_pdf("nonexistent.pdf", "Summarize this")


class TestGeminiLoaderProcessFile:
    """Tests for process_file method."""

    @pytest.mark.asyncio
    async def test_process_image_file(self, mock_genai, tmp_path):
        """Test automatic image file processing."""
        from kagura.loaders.gemini import GeminiLoader

        image_file = tmp_path / "test.png"
        image_file.write_text("mock image data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.process_file(image_file)

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_process_audio_file(self, mock_genai, tmp_path):
        """Test automatic audio file processing."""
        from kagura.loaders.gemini import GeminiLoader

        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("mock audio data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.process_file(audio_file)

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_process_video_file(self, mock_genai, tmp_path):
        """Test automatic video file processing."""
        from kagura.loaders.gemini import GeminiLoader

        video_file = tmp_path / "test.mp4"
        video_file.write_text("mock video data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.process_file(video_file)

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_process_pdf_file(self, mock_genai, tmp_path):
        """Test automatic PDF file processing."""
        from kagura.loaders.gemini import GeminiLoader

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("mock pdf data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.process_file(pdf_file)

        assert result == "Mock response text"

    @pytest.mark.asyncio
    async def test_process_unsupported_file(self, mock_genai, tmp_path):
        """Test processing unsupported file type."""
        from kagura.loaders.gemini import GeminiLoader

        text_file = tmp_path / "test.txt"
        text_file.write_text("plain text")

        loader = GeminiLoader(api_key="test_key")
        with pytest.raises(ValueError, match="Unsupported file type"):
            await loader.process_file(text_file)

    @pytest.mark.asyncio
    async def test_process_file_with_custom_prompt(self, mock_genai, tmp_path):
        """Test file processing with custom prompt."""
        from kagura.loaders.gemini import GeminiLoader

        image_file = tmp_path / "test.png"
        image_file.write_text("mock image data")

        loader = GeminiLoader(api_key="test_key")
        result = await loader.process_file(image_file, prompt="Custom prompt")

        assert result == "Mock response text"
