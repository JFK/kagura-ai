"""Daily news agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-nano", tools=[brave_web_search], stream=True)
async def daily_news(query: str) -> str:
    """Get today's latest news based on user query: {{ query }}

    User preferences (from kagura init):
    - Preferred topics: {{ user_news_topics }}
    - Language: {{ user_language }}

    Extract topic from the query and search for recent news articles.

    Instructions:
    1. Parse the query to extract topic (e.g., "tech news" → technology)
    2. If no specific topic in query, use preferred topics: {{ user_news_topics }}
    3. If user_news_topics is empty, default to "technology"
    3. Search for "[topic] news today" or "latest [topic] news"
    4. Focus on articles from the past 24 hours
    5. Format as markdown list with:
       - **Title** in bold
       - Source name
       - Brief 1-2 sentence summary
       - Link to full article
    6. Return 5-8 most relevant and recent articles

    Example output format:
    ```
    # Today's Tech News

    1. **Article Title Here**
       Source: TechCrunch
       Summary: Brief description of the article...
       [Read more](https://...)

    2. **Another Article**
       Source: The Verge
       ...
    ```

    Be concise but informative. Focus on the most important and recent news.
    """
    ...
