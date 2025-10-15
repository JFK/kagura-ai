"""
Utility functions for chat session
"""

from typing import Any


def extract_response_content(response: Any) -> str:
    """
    Extract string content from various response types.

    Handles:
    - LLMResponse objects (extracts .content)
    - Plain strings
    - Other objects (converts to string)

    Args:
        response: Response object from agent or LLM

    Returns:
        String content
    """
    # Check if it's an LLMResponse object
    if hasattr(response, "content"):
        content = response.content
        # Content might also be an LLMResponse (nested)
        if hasattr(content, "content"):
            return str(content.content)
        return str(content)

    # Plain string or other type
    return str(response)
