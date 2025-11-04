"""Vision analyzer for multimodal coding context.

Handles image analysis for coding-related tasks:
- Error screenshot analysis
- Architecture diagram interpretation
- Code extraction from images (OCR)
- UI mockup analysis
"""

import base64
import logging
from pathlib import Path
from typing import Any, Literal

from litellm import acompletion

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """Analyze images for coding context.

    Uses vision-capable LLMs to extract information from:
    - Error screenshots
    - Architecture diagrams
    - Code snippets in images
    - UI mockups

    Attributes:
        model: Vision-capable model ID
        temperature: LLM temperature
        max_tokens: Maximum response tokens
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ):
        """Initialize vision analyzer.

        Args:
            model: Vision-capable model ID (None = use gpt-4o default)
                Recommended:
                - OpenAI: "gpt-4o" (best vision quality)
                - Google: "gemini/gemini-2.0-flash-exp" (fast, free during preview)
                - Google: "gemini/gemini-2.5-flash" (production ready)
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum response tokens
        """
        import os

        # Default to Gemini (free during preview, excellent vision quality)
        if model is None:
            model = (
                os.getenv("CODING_MEMORY_VISION_MODEL") or "gemini/gemini-2.0-flash-exp"
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(f"VisionAnalyzer initialized: model={self.model}")

    def _load_image(self, image_source: str | bytes) -> str:
        """Load image and encode as base64.

        Args:
            image_source: File path (str) or raw bytes

        Returns:
            Base64-encoded image string

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is unsupported
        """
        if isinstance(image_source, bytes):
            return base64.b64encode(image_source).decode("utf-8")

        # File path
        image_path = Path(image_source)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        return base64.b64encode(image_bytes).decode("utf-8")

    async def _call_vision_llm(
        self,
        prompt: str,
        image_base64: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Call vision-capable LLM with image.

        Args:
            prompt: Text prompt describing task
            image_base64: Base64-encoded image
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max_tokens

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ]

        try:
            response = await acompletion(  # type: ignore
                model=model or self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            content = response.choices[0].message.content  # type: ignore
            if not content:
                raise ValueError("Empty response from vision LLM")

            logger.info(
                f"Vision LLM call successful: {response.usage.total_tokens} tokens"  # type: ignore
            )
            return content

        except Exception as e:
            logger.error(f"Vision LLM call failed: {e}")
            raise

    async def analyze_error_screenshot(
        self, image_source: str | bytes
    ) -> dict[str, Any]:
        """Extract error information from screenshot.

        Analyzes error screenshots to extract:
        - Error type and message
        - File path and line number
        - Stack trace key frames
        - Visible code context
        - Suggested cause

        Args:
            image_source: Path to screenshot or raw image bytes

        Returns:
            Dictionary with extracted error information:
                - error_type: str (e.g., "TypeError", "SyntaxError")
                - error_message: str (full error message)
                - file_path: str | None (if visible)
                - line_number: int | None (if visible)
                - stack_trace: str (key frames)
                - code_context: str (visible code around error)
                - suggested_cause: str (AI analysis)

        Example:
            >>> vision = VisionAnalyzer()
            >>> error_info = await vision.analyze_error_screenshot(
            ...     "screenshots/error_2025-01-15.png"
            ... )
            >>> print(error_info['error_type'])
            TypeError
            >>> print(error_info['suggested_cause'])
            Comparing timezone-aware and naive datetime objects
        """
        prompt = """Analyze this error screenshot from a coding session.

Extract the following information with high precision:

1. **Error Type**: Identify the error class
   (e.g., TypeError, SyntaxError, AttributeError)
   - If unclear, provide best guess with confidence level

2. **Error Message**: Extract the complete error message text
   - Include all relevant details
   - Note if truncated in screenshot

3. **File Path**: If visible, extract the full file path where error occurred
   - Format: /absolute/path/to/file.py or relative/path/file.py
   - If not visible, return null

4. **Line Number**: If visible, extract the line number
   - If not visible, return null

5. **Stack Trace**: Extract key frames from the stack trace
   - Focus on application code (not library internals)
   - Include function names and line numbers
   - If full trace not visible, extract what's shown

6. **Code Context**: Extract visible code around the error
   - Include relevant lines before/after error
   - Preserve indentation and formatting

7. **Suggested Cause**: Based on the error and context, suggest likely root cause
   - Be specific and actionable
   - Reference visible code patterns

Output format (structured YAML):
```yaml
error_type: "TypeError"
confidence: high  # high | medium | low
error_message: "Full error message text here"
file_path: "/path/to/file.py"  # or null
line_number: 42  # or null
stack_trace: |
  Traceback (most recent call last):
    File "main.py", line 15, in <module>
      result = process_data()
    File "utils.py", line 42, in process_data
      return compare(a, b)
code_context: |
  Line 40: def process_data():
  Line 41:     a = datetime.now()
  Line 42:     b = datetime.now(timezone.utc)
  Line 43:     return a < b  # Error here
suggested_cause: |
  Comparing timezone-aware (b) with naive (a) datetime.
  Python 3.11+ forbids this comparison for safety.
  Fix: Use datetime.now(timezone.utc) for both.
visible_ui_elements:
  - "IDE: VSCode (based on UI)"
  - "Terminal showing error output"
additional_notes: "Error occurred in interactive debugger session"
```

Be precise and thorough. If information is not visible, explicitly state null."""

        image_base64 = self._load_image(image_source)

        response = await self._call_vision_llm(
            prompt=prompt,
            image_base64=image_base64,
            temperature=0.1,  # Very low temp for precise extraction
            max_tokens=2048,
        )

        # TODO: Parse YAML response into structured dict
        # For now, return structured placeholder
        logger.info("Error screenshot analyzed")

        return {
            "error_type": "Unknown",
            "confidence": "low",
            "error_message": response[:200],
            "file_path": None,
            "line_number": None,
            "stack_trace": "See full response",
            "code_context": "",
            "suggested_cause": "Analysis in progress",
        }

    async def analyze_architecture_diagram(
        self, image_source: str | bytes
    ) -> dict[str, Any]:
        """Extract architectural insights from diagram.

        Analyzes architecture diagrams to understand:
        - System components
        - Component relationships
        - Data flow
        - Technology choices

        Args:
            image_source: Path to diagram or raw image bytes

        Returns:
            Dictionary with:
                - components: list[str] (identified components)
                - relationships: list[dict] (component connections)
                - data_flow: str (description of data flow)
                - technology_stack: list[str] (identified technologies)
                - architecture_pattern: str (e.g., "microservices", "MVC")
                - summary: str (high-level description)

        Example:
            >>> arch = await vision.analyze_architecture_diagram(
            ...     "docs/architecture.png"
            ... )
            >>> print(arch['architecture_pattern'])
            Layered architecture with API gateway
            >>> print(arch['components'])
            ['API Gateway', 'Auth Service', 'Database', 'Cache']
        """
        prompt = """Analyze this software architecture diagram.

Extract comprehensive architectural information:

1. **Components**: Identify all system components/services
   - Name each component clearly
   - Classify type (service, database, cache, queue, etc.)

2. **Relationships**: Identify connections between components
   - Direction of communication (A → B)
   - Type of connection (HTTP, gRPC, message queue, etc.)
   - Purpose of connection if labeled

3. **Data Flow**: Describe how data flows through the system
   - Entry points (user requests, events, etc.)
   - Processing steps
   - Storage/persistence points
   - Output/response path

4. **Technology Stack**: Identify specific technologies if labeled
   - Frameworks (FastAPI, React, etc.)
   - Databases (PostgreSQL, Redis, etc.)
   - Infrastructure (Kubernetes, AWS, etc.)

5. **Architecture Pattern**: Classify the overall pattern
   - Examples: Microservices, Monolith, Layered, Event-driven, CQRS
   - Note: Can be multiple patterns

6. **Key Design Decisions**: Infer architectural decisions
   - Why this structure?
   - What problems does it solve?
   - Potential trade-offs

Output format (structured YAML):
```yaml
components:
  - name: "API Gateway"
    type: "service"
    description: "Entry point for all client requests"
    technology: "Kong" # if visible

  - name: "Auth Service"
    type: "service"
    description: "Handles authentication and authorization"

  - name: "User Database"
    type: "database"
    technology: "PostgreSQL"

relationships:
  - from: "API Gateway"
    to: "Auth Service"
    connection_type: "HTTP/REST"
    purpose: "Token validation"

  - from: "Auth Service"
    to: "User Database"
    connection_type: "SQL"
    purpose: "User lookup"

data_flow: |
  1. Client request → API Gateway
  2. Gateway validates JWT via Auth Service
  3. Auth Service queries User Database
  4. Response flows back through gateway to client

technology_stack:
  - "FastAPI (API Gateway)"
  - "PostgreSQL (Database)"
  - "Redis (Cache)"
  - "Docker (Deployment)"

architecture_patterns:
  - "Microservices"
  - "API Gateway pattern"
  - "Database-per-service"

key_design_decisions:
  - decision: "Separate auth service"
    rationale: "Centralized authentication, reusable across services"
    trade_off: "Additional network hop for validation"

  - decision: "API Gateway"
    rationale: "Single entry point, simplified client logic"
    trade_off: "Potential bottleneck, needs high availability"

summary: |
  Microservices architecture with API Gateway pattern.
  Services communicate via HTTP/REST. Auth is centralized.
  PostgreSQL for persistence, Redis for caching.
  Designed for scalability and service independence.

confidence: high  # Based on diagram clarity
```

Be thorough and precise. If unclear, note assumptions."""

        image_base64 = self._load_image(image_source)

        response = await self._call_vision_llm(
            prompt=prompt,
            image_base64=image_base64,
            temperature=0.3,  # Moderate temp for interpretation
            max_tokens=3072,
        )

        # TODO: Parse YAML response
        logger.info("Architecture diagram analyzed")

        return {
            "components": [],
            "relationships": [],
            "data_flow": response[:300],
            "technology_stack": [],
            "architecture_pattern": "Unknown",
            "summary": response,
        }

    async def extract_code_from_image(
        self, image_source: str | bytes, language: str | None = None
    ) -> dict[str, Any]:
        """Extract code from image (OCR + understanding).

        Extracts code snippets from screenshots or photos, preserving:
        - Syntax and structure
        - Comments
        - Indentation

        Args:
            image_source: Path to image or raw bytes
            language: Programming language hint (helps accuracy)

        Returns:
            Dictionary with:
                - code: str (extracted code)
                - language: str (detected/specified language)
                - confidence: str (extraction confidence)
                - issues: list[str] (OCR issues or ambiguities)

        Example:
            >>> code_data = await vision.extract_code_from_image(
            ...     "photo_of_whiteboard.jpg", language="python"
            ... )
            >>> print(code_data['code'])
            def calculate_total(items):
                return sum(item.price for item in items)
        """
        lang_hint = f" (Language: {language})" if language else ""
        prompt = f"""Extract the code from this image{lang_hint}.

Requirements:
1. **Preserve exact formatting**: Maintain indentation, line breaks, spacing
2. **Include comments**: Capture all visible comments
3. **Handle OCR ambiguities**: Note unclear characters (e.g., 0 vs O, 1 vs l)
4. **Detect language**: If not specified, identify programming language
5. **Complete extraction**: Get all visible code, even if partial

Output format (structured YAML):
```yaml
code: |
  def calculate_total(items):
      \"\"\"Calculate total price of items.\"\"\"
      return sum(item.price for item in items)

language: "Python"  # Detected or confirmed language

confidence: high  # high | medium | low
  # Based on image quality, code visibility

issues:
  - "Line 3: Character might be '1' or 'l' (assumed 'l')"
  - "Possible truncation at bottom of image"

context: |
  Code appears to be from a function definition.
  Part of a larger module (import statements visible above).

syntax_valid: true  # or false if obvious syntax errors
```

Be meticulous. Better to note ambiguity than guess wrong."""

        image_base64 = self._load_image(image_source)

        response = await self._call_vision_llm(
            prompt=prompt,
            image_base64=image_base64,
            temperature=0.0,  # Zero temp for exact extraction
            max_tokens=2048,
        )

        # TODO: Parse YAML and validate extracted code
        logger.info("Code extracted from image")

        return {
            "code": response,
            "language": language or "unknown",
            "confidence": "medium",
            "issues": [],
        }

    async def analyze_ui_mockup(
        self,
        image_source: str | bytes,
        analysis_type: Literal["layout", "components", "implementation"] = "layout",
    ) -> dict[str, Any]:
        """Analyze UI mockup for implementation guidance.

        Helps convert UI mockups into implementation plans.

        Args:
            image_source: Path to mockup or raw bytes
            analysis_type:
                - "layout": Focus on structure and positioning
                - "components": Identify UI components needed
                - "implementation": Suggest implementation approach

        Returns:
            Dictionary with analysis results based on type

        Example:
            >>> ui_analysis = await vision.analyze_ui_mockup(
            ...     "mockup/dashboard.png", analysis_type="components"
            ... )
            >>> for component in ui_analysis['components']:
            ...     print(f"{component['name']}: {component['suggestion']}")
            Navigation Bar: Use React component with sticky positioning
            Data Table: Consider TanStack Table or AG Grid
        """
        if analysis_type == "layout":
            prompt = """Analyze this UI mockup focusing on layout structure.

Identify:
1. Layout pattern (grid, flexbox, absolute positioning)
2. Component hierarchy (parent-child relationships)
3. Spacing and alignment patterns
4. Responsive considerations (if evident)

Output as structured YAML with CSS/layout suggestions."""

        elif analysis_type == "components":
            prompt = """Analyze this UI mockup to identify required components.

For each UI element:
1. Component name (descriptive)
2. Component type (button, input, table, etc.)
3. Suggested library/framework component
4. Props/configuration needed

Output as structured YAML with implementation suggestions."""

        else:  # implementation
            prompt = """Analyze this UI mockup for full implementation guidance.

Provide:
1. Component breakdown (hierarchy and structure)
2. Suggested technology stack
3. State management requirements
4. API/data requirements
5. Implementation order (which components first)

Output as structured YAML with actionable implementation plan."""

        image_base64 = self._load_image(image_source)

        response = await self._call_vision_llm(
            prompt=prompt,
            image_base64=image_base64,
            temperature=0.4,  # Moderate creativity for suggestions
            max_tokens=2048,
        )

        logger.info(f"UI mockup analyzed: {analysis_type} analysis")

        return {
            "analysis_type": analysis_type,
            "results": response,
            "confidence": "medium",
        }
