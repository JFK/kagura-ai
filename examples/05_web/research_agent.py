"""Research Agent - Comprehensive web research

This example demonstrates:
- Multi-step research workflow
- Combining search and scraping
- Synthesizing information from multiple sources
"""

import asyncio
from pydantic import BaseModel, Field
from kagura import agent, tool


class ResearchReport(BaseModel):
    """Structured research report"""
    topic: str = Field(description="Research topic")
    summary: str = Field(description="Executive summary (2-3 sentences)")
    key_findings: list[str] = Field(description="3-5 key findings")
    sources: list[str] = Field(description="URLs of sources used")
    confidence: str = Field(description="High/Medium/Low")


@tool
async def search_web(query: str) -> str:
    """Search the web and return top results"""
    # Simulated search results
    return f"""
Top results for: {query}
1. https://example.com/article1 - Overview of {query}
2. https://example.com/article2 - Latest research on {query}
3. https://example.com/article3 - Expert opinion on {query}
"""


@tool
async def scrape_url(url: str) -> str:
    """Scrape and extract text from URL"""
    # Simulated scraping
    return f"Content from {url}: Detailed information about the topic..."


@agent(tools=[search_web, scrape_url])
async def research_agent(topic: str) -> ResearchReport:
    """
    Conduct comprehensive research on: {{ topic }}

    Process:
    1. Search web for relevant sources
    2. Scrape top 3 sources
    3. Analyze and synthesize findings
    4. Create structured report

    Return a complete ResearchReport with all findings.
    """
    pass


@agent(tools=[search_web])
async def trend_analyzer(topic: str) -> str:
    """
    Analyze current trends for: {{ topic }}

    Use web search to find:
    - Recent developments
    - Popular discussions
    - Expert opinions
    - Future outlook

    Provide a trend analysis with key insights.
    """
    pass


@agent(tools=[search_web, scrape_url])
async def comparison_researcher(topic1: str, topic2: str) -> str:
    """
    Compare {{ topic1 }} vs {{ topic2 }}

    Research both topics and provide:
    - Similarities
    - Differences
    - Use cases for each
    - Recommendations

    Use web search and scraping for accurate information.
    """
    pass


async def main():
    print("Research Agent Demo")
    print("-" * 50)
    print("Note: Using simulated web data for demo")
    print()

    # Comprehensive research
    print("=== Comprehensive Research ===")
    topic = "Large Language Models"
    report = await research_agent(topic)

    print(f"\nTopic: {report.topic}")
    print(f"\nSummary:\n{report.summary}")
    print(f"\nKey Findings:")
    for i, finding in enumerate(report.key_findings, 1):
        print(f"{i}. {finding}")
    print(f"\nSources:")
    for source in report.sources:
        print(f"  - {source}")
    print(f"\nConfidence: {report.confidence}")

    # Trend analysis
    print("\n\n=== Trend Analysis ===")
    trend_topic = "AI Agent Frameworks"
    trends = await trend_analyzer(trend_topic)
    print(f"\nTrends for '{trend_topic}':")
    print(trends)

    # Comparison research
    print("\n\n=== Comparison Research ===")
    comparison = await comparison_researcher(
        "Python",
        "JavaScript"
    )
    print("\nPython vs JavaScript:")
    print(comparison)


if __name__ == "__main__":
    asyncio.run(main())
