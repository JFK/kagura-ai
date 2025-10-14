"""Research Assistant - Automated research workflow

This example demonstrates:
- Multi-step research pipeline
- Web search and scraping simulation
- Report generation
- Citation management
"""

import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from kagura import agent, tool, LLMConfig
from kagura.core.memory import MemoryRAG


# Research models
class Source(BaseModel):
    """Research source"""
    url: str = Field(description="Source URL")
    title: str = Field(description="Source title")
    summary: str = Field(description="Brief summary")
    relevance_score: float = Field(description="0-1 relevance score")


class ResearchPlan(BaseModel):
    """Research plan"""
    topic: str = Field(description="Research topic")
    search_queries: list[str] = Field(description="List of search queries")
    key_questions: list[str] = Field(description="Key questions to answer")
    estimated_sources_needed: int = Field(description="Number of sources needed")


class ResearchReport(BaseModel):
    """Final research report"""
    topic: str
    executive_summary: str
    key_findings: list[str]
    detailed_analysis: str
    sources: list[Source]
    recommendations: list[str]


# Research tools
@tool
async def web_search(query: str) -> str:
    """Search the web for research sources"""
    # Simulated search results
    return f"""
Search results for: {query}
1. https://example.com/article1 - {query} Overview
2. https://example.com/paper2 - Research on {query}
3. https://example.com/analysis3 - {query} Analysis
"""


@tool
async def scrape_article(url: str) -> str:
    """Scrape and extract article content"""
    # Simulated content
    return f"Article content from {url}: Detailed information about the topic..."


@tool
async def extract_citations(text: str) -> str:
    """Extract citations and references from text"""
    # Simulated citation extraction
    return "Found 5 citations: [1] Smith et al. 2023, [2] Jones 2022..."


# Memory for research materials
research_memory = MemoryRAG(agent_name="research_assistant")

# Config
config = LLMConfig(model="gpt-4o-mini", temperature=0.7)


# Research agents
@agent(config=config)
async def research_planner(topic: str) -> ResearchPlan:
    """
    Create a research plan for: {{ topic }}

    Return structured plan with:
    - Topic
    - 3-5 search queries
    - Key questions to answer
    - Estimated sources needed
    """
    pass


@agent(config=config, tools=[web_search])
async def source_finder(query: str, num_sources: int) -> list[dict]:
    """
    Find {{ num_sources }} sources for: {{ query }}

    Use web_search tool and return list of sources with:
    - URL
    - Title
    - Brief summary
    - Relevance score (0-1)
    """
    pass


@agent(config=config, tools=[scrape_article])
async def content_analyzer(url: str, research_question: str) -> str:
    """
    Analyze {{ url }} for: {{ research_question }}

    Scrape the article and extract relevant information.
    Return: Key findings, quotes, and insights.
    """
    pass


@agent(config=config)
async def report_writer(
    topic: str,
    findings: list[str],
    sources: list[str]
) -> ResearchReport:
    """
    Write research report on: {{ topic }}

    Findings:
    {% for finding in findings %}
    - {{ finding }}
    {% endfor %}

    Sources:
    {% for source in sources %}
    - {{ source }}
    {% endfor %}

    Return comprehensive ResearchReport with:
    - Executive summary
    - Key findings (synthesized)
    - Detailed analysis
    - Source list
    - Recommendations
    """
    pass


# Research workflow
async def conduct_research(topic: str) -> ResearchReport:
    """Execute full research workflow"""
    print(f"\n{'=' * 60}")
    print(f"Starting research on: {topic}")
    print(f"{'=' * 60}")

    # Step 1: Create research plan
    print("\n[Step 1] Creating research plan...")
    plan = await research_planner(topic)
    print(f"✓ Plan created with {len(plan.search_queries)} queries")
    print(f"  Questions: {', '.join(plan.key_questions[:2])}...")

    # Step 2: Find sources
    print("\n[Step 2] Finding sources...")
    all_sources = []
    for query in plan.search_queries[:2]:  # Limit for demo
        sources = await source_finder(query, 2)
        all_sources.extend(sources)
        print(f"✓ Found {len(sources)} sources for '{query}'")

    # Step 3: Analyze sources
    print("\n[Step 3] Analyzing sources...")
    findings = []
    for i, source in enumerate(all_sources[:3], 1):  # Limit for demo
        url = source.get("url", f"https://example.com/source{i}")
        analysis = await content_analyzer(url, plan.key_questions[0])
        findings.append(analysis)

        # Store in memory
        await research_memory.store(
            content=analysis,
            metadata={"source": url, "topic": topic}
        )
        print(f"✓ Analyzed source {i}/{len(all_sources[:3])}")

    # Step 4: Generate report
    print("\n[Step 4] Generating report...")
    source_refs = [s.get("url", "") for s in all_sources]
    report = await report_writer(topic, findings, source_refs)
    print("✓ Report generated")

    return report


async def main():
    print("Research Assistant - Automated Research Workflow")
    print("=" * 60)

    # Research topics
    topics = [
        "Impact of AI on software development",
        "Future of quantum computing"
    ]

    for topic in topics:
        # Conduct research
        report = await conduct_research(topic)

        # Display report
        print(f"\n{'=' * 60}")
        print(f"RESEARCH REPORT: {report.topic}")
        print(f"{'=' * 60}")

        print(f"\nExecutive Summary:")
        print(report.executive_summary)

        print(f"\nKey Findings ({len(report.key_findings)}):")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"{i}. {finding}")

        print(f"\nRecommendations ({len(report.recommendations)}):")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")

        print(f"\nSources ({len(report.sources)}):")
        for source in report.sources:
            print(f"- {source.title} ({source.url})")

        print()

    print("=" * 60)
    print("Research Assistant Features:")
    print("- Automated research planning")
    print("- Source discovery and validation")
    print("- Content analysis and synthesis")
    print("- Professional report generation")
    print("- Citation management")


if __name__ == "__main__":
    asyncio.run(main())
