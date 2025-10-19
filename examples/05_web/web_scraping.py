"""Web Scraping - Extract content from web pages

This example demonstrates:
- Scraping web pages with BeautifulSoup
- Using tools for web content extraction
- Processing HTML content with AI
"""

import asyncio

from kagura import agent, tool


@tool
async def scrape_webpage(url: str) -> str:
    """Scrape text content from a webpage

    Args:
        url: URL to scrape

    Returns:
        Extracted text content

    Note:
        Real implementation would use requests + BeautifulSoup
    """
    # This would use actual web scraping
    # For demo purposes, we'll simulate
    try:
        # In real implementation:
        # import requests
        # from bs4 import BeautifulSoup
        #
        # response = requests.get(url)
        # soup = BeautifulSoup(response.content, 'html.parser')
        # text = soup.get_text()
        # return text

        # Simulated content
        if "wikipedia" in url.lower():
            return """
            Python (programming language)
            Python is a high-level, interpreted programming language.
            Created by Guido van Rossum in 1991.
            Known for its clear syntax and readability.
            Used for web development, data science, AI, and more.
            """
        else:
            return f"Content from {url}: This is sample text content."

    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


@agent(tools=[scrape_webpage])
async def web_summarizer(url: str) -> str:
    """
    Summarize the content at this URL: {{ url }}

    Use scrape_webpage to get content, then provide:
    - Main topic (1 line)
    - Key points (3-5 bullets)
    - Target audience
    """
    pass


@agent(tools=[scrape_webpage])
async def web_qa(url: str, question: str) -> str:
    """
    Answer this question based on content at {{ url }}:
    {{ question }}

    Scrape the webpage and answer based on its content.
    """
    pass


@agent(tools=[scrape_webpage])
async def content_extractor(url: str, extract_type: str) -> str:
    """
    Extract {{ extract_type }} from {{ url }}

    Types: links, emails, phone_numbers, dates, names
    Return as a structured list.
    """
    pass


async def main():
    print("Web Scraping Demo")
    print("-" * 50)
    print("Note: Using simulated content for demo")
    print()

    # Example URLs
    test_urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://www.example.com/blog/article"
    ]

    # Summarize web pages
    print("=== Web Page Summaries ===")
    for url in test_urls[:1]:  # Just first one for demo
        summary = await web_summarizer(url)
        print(f"\nURL: {url}")
        print(f"Summary:\n{summary}")

    # Answer questions about web content
    print("\n\n=== Q&A from Web Content ===")
    url = test_urls[0]
    questions = [
        "When was Python created?",
        "What is Python known for?",
        "What are common uses of Python?"
    ]

    for question in questions:
        answer = await web_qa(url, question)
        print(f"\nQ: {question}")
        print(f"A: {answer}")

    # Extract specific information
    print("\n\n=== Information Extraction ===")
    extraction = await content_extractor(url, "dates")
    print(f"Extracted dates from {url}:")
    print(extraction)


if __name__ == "__main__":
    asyncio.run(main())
