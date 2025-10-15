"""
YouTube Video Summarizer Agent

Summarizes YouTube videos by extracting transcripts and metadata.
Uses built-in YouTube tools for transcript and metadata extraction.
"""

from kagura import agent
from kagura.tools.youtube import get_youtube_metadata, get_youtube_transcript


@agent(
    model="gpt-4o",
    temperature=0.7,
    tools=[get_youtube_transcript, get_youtube_metadata],
)
async def youtube_video_summarizer(video_url: str, language: str = "en") -> str:
    """Summarize a YouTube video.

    Given a YouTube video URL, this agent:
    1. Extracts the video transcript (in specified language)
    2. Gets video metadata (title, author, etc.)
    3. Provides a comprehensive summary

    User request: {{ video_url }}
    Language: {{ language }}

    Available tools:
    - get_youtube_transcript(video_url, lang): Get video transcript
    - get_youtube_metadata(video_url): Get video metadata (title, author, etc.)

    Instructions:
    1. First, get the video metadata to understand the context
    2. Then, get the transcript. Try the specified language first ({{ language }})
       - If {{ language }} fails, the tool will automatically try other available languages
       - This is normal for videos that only have transcripts in specific languages
    3. Analyze the transcript and metadata
    4. Provide a comprehensive summary including:
       - Video title and author
       - Main topics covered
       - Key points and takeaways
       - Duration and other relevant info
    5. If transcript is not available at all, provide summary based on metadata only

    Format the summary in clear, readable markdown.
    If the video is in Japanese, provide the summary in Japanese.
    """
    ...
