"""
Built-in tools for Kagura AI
"""

from .brave_search import brave_news_search, brave_web_search
from .youtube import get_youtube_metadata, get_youtube_transcript

__all__ = [
    # YouTube
    "get_youtube_transcript",
    "get_youtube_metadata",
    # Brave Search
    "brave_web_search",
    "brave_news_search",
]
