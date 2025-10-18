"""Daily news agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-mini", tools=[brave_web_search])
async def daily_news(topic: str = "technology", count: int = 5) -> str:
    """Get today's latest news on {{ topic }}

    Search for recent news articles and format as a clean, readable summary.

    Instructions:
    1. Search for "{{ topic }} news today" or "latest {{ topic }}"
    2. Focus on articles from the past 24 hours
    3. Format as markdown list with:
       - **Title** in bold
       - Source name
       - Brief 1-2 sentence summary
       - Link to full article
    4. Return {{ count }} most relevant and recent articles
    5. If topic is not specified, default to "technology"

    Example output format:
    ```
    # Today's {{ topic|title }} News

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
