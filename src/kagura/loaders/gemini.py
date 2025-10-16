"""Gemini API loader for multimodal content processing."""

from pathlib import Path
from typing import TYPE_CHECKING

from kagura.config.env import get_google_api_key

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

if TYPE_CHECKING:
    pass


class GeminiLoader:
    """Gemini API loader for processing multimodal content.

    Supports:
    - Images (PNG, JPG, JPEG, GIF, WEBP)
    - Audio (MP3, WAV, M4A)
    - Video (MP4, MOV, AVI)
    - PDF documents

    Examples:
        >>> loader = GeminiLoader(model="gemini-1.5-flash")
        >>> result = await loader.analyze_image("diagram.png", "Explain this diagram")
        >>> print(result)
        "This diagram shows..."

        >>> transcript = await loader.transcribe_audio("meeting.mp3")
        >>> print(transcript)
        "The meeting discussed..."
    """

    def __init__(
        self,
        model: str = "gemini-1.5-flash",
        api_key: str | None = None,
    ):
        """Initialize Gemini loader.

        Args:
            model: Gemini model to use (default: gemini-1.5-flash)
                   Options: gemini-1.5-flash, gemini-1.5-pro
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)

        Raises:
            ImportError: If google-generativeai is not installed
            ValueError: If API key is not provided
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai is not installed. "
                "Install it with: pip install google-generativeai"
            )

        self.model_name = model
        self.api_key = api_key or get_google_api_key()

        if not self.api_key:
            raise ValueError(
                "Google API key not found. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)

    async def analyze_image(
        self,
        image_path: Path | str,
        prompt: str = "Describe this image in detail.",
        language: str = "en",
    ) -> str:
        """Analyze image with Gemini Vision.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            language: Response language (en/ja)

        Returns:
            Analysis result text

        Raises:
            FileNotFoundError: If image file not found
            ValueError: If file is not a valid image
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        # Upload file to Gemini
        uploaded_file = genai.upload_file(str(path))

        # Add language instruction
        if language == "ja":
            prompt = f"{prompt}\n日本語で回答してください。"

        # Generate content
        response = await self.model.generate_content_async([prompt, uploaded_file])

        return response.text

    async def transcribe_audio(
        self,
        audio_path: Path | str,
        language: str = "ja",
    ) -> str:
        """Transcribe audio with Gemini.

        Args:
            audio_path: Path to audio file
            language: Transcription language (en/ja)

        Returns:
            Transcribed text

        Raises:
            FileNotFoundError: If audio file not found
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        uploaded_file = genai.upload_file(str(path))

        if language == "ja":
            prompt = "この音声を日本語で文字起こししてください。"
        else:
            prompt = "Transcribe this audio."

        response = await self.model.generate_content_async([prompt, uploaded_file])

        return response.text

    async def analyze_video(
        self,
        video_path: Path | str,
        prompt: str = "Summarize this video.",
        language: str = "en",
    ) -> str:
        """Analyze video with Gemini.

        Args:
            video_path: Path to video file
            prompt: Analysis prompt
            language: Response language (en/ja)

        Returns:
            Video analysis result

        Raises:
            FileNotFoundError: If video file not found
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {path}")

        uploaded_file = genai.upload_file(str(path))

        if language == "ja":
            prompt = f"{prompt}\n日本語で回答してください。"

        response = await self.model.generate_content_async([prompt, uploaded_file])

        return response.text

    async def analyze_pdf(
        self,
        pdf_path: Path | str,
        prompt: str = "Summarize this document.",
        language: str = "en",
    ) -> str:
        """Analyze PDF document with Gemini.

        Args:
            pdf_path: Path to PDF file
            prompt: Analysis prompt
            language: Response language (en/ja)

        Returns:
            PDF analysis result

        Raises:
            FileNotFoundError: If PDF file not found
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        uploaded_file = genai.upload_file(str(path))

        if language == "ja":
            prompt = f"{prompt}\n日本語で回答してください。"

        response = await self.model.generate_content_async([prompt, uploaded_file])

        return response.text

    async def process_file(
        self,
        file_path: Path | str,
        prompt: str | None = None,
        language: str = "en",
    ) -> str:
        """Process any supported file type automatically.

        Detects file type and uses appropriate method.

        Args:
            file_path: Path to file
            prompt: Optional custom prompt (uses default if None)
            language: Response language (en/ja)

        Returns:
            Processing result text

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file type is not supported
        """
        from kagura.loaders.file_types import FileType, detect_file_type

        path = Path(file_path)
        file_type = detect_file_type(path)

        if file_type == FileType.IMAGE:
            default_prompt = "Describe this image in detail."
            return await self.analyze_image(
                path, prompt or default_prompt, language=language
            )
        elif file_type == FileType.AUDIO:
            return await self.transcribe_audio(path, language=language)
        elif file_type == FileType.VIDEO:
            default_prompt = "Summarize this video."
            return await self.analyze_video(
                path, prompt or default_prompt, language=language
            )
        elif file_type == FileType.PDF:
            default_prompt = "Summarize this document."
            return await self.analyze_pdf(
                path, prompt or default_prompt, language=language
            )
        else:
            raise ValueError(
                f"Unsupported file type: {file_type}. "
                f"Supported types: IMAGE, AUDIO, VIDEO, PDF"
            )
