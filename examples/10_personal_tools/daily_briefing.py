"""Daily Briefing Example - Personal Assistant Morning Routine

This example demonstrates Kagura AI's personal tools (news, weather) to create
a personalized daily briefing.

Usage:
    # No extra dependencies needed
    python examples/10_personal_tools/daily_briefing.py

    # Or customize
    python examples/10_personal_tools/daily_briefing.py --location "San Francisco" --topics "AI,startups"
"""

import asyncio
from datetime import datetime

import click
from kagura.agents import daily_news, weather_forecast


async def create_daily_briefing(
    location: str = "Tokyo",
    topics: list[str] | None = None,
    news_count: int = 5,
) -> str:
    """
    Generate personalized daily briefing

    Args:
        location: Location for weather forecast
        topics: News topics of interest (default: ["technology"])
        news_count: Number of news items per topic

    Returns:
        Formatted briefing text
    """
    if topics is None:
        topics = ["technology"]

    print(f"\n{'=' * 60}")
    print(f"📰 Daily Briefing - {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"{'=' * 60}\n")

    # Weather
    print("🌤️  Fetching weather...")
    weather = await weather_forecast(location)

    # News for each topic
    news_sections = []
    for topic in topics:
        print(f"📡 Fetching news: {topic}...")
        query = f"{topic} news (show {news_count} articles)"
        news = await daily_news(query)
        news_sections.append((topic, news))

    # Format briefing
    briefing = f"""
{'=' * 60}
📰 DAILY BRIEFING
{datetime.now().strftime('%A, %B %d, %Y')}
{'=' * 60}

🌤️  WEATHER ({location})
{'-' * 60}
{weather}

"""

    for topic, news in news_sections:
        briefing += f"""
📰 {topic.upper()} NEWS
{'-' * 60}
{news}

"""

    briefing += f"""
{'=' * 60}
Have a great day! ☀️
{'=' * 60}
"""

    return briefing


async def quick_briefing():
    """Quick briefing with default settings"""
    briefing = await create_daily_briefing(
        location="current",
        topics=["technology", "AI"],
        news_count=3,
    )
    print(briefing)


async def custom_briefing(location: str, topics: str):
    """Custom briefing with user settings"""
    topic_list = [t.strip() for t in topics.split(",")]
    briefing = await create_daily_briefing(
        location=location,
        topics=topic_list,
        news_count=5,
    )
    print(briefing)

    # Save to file
    filename = f"briefing_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(filename, "w") as f:
        f.write(briefing)
    print(f"\n💾 Saved to: {filename}")


@click.command()
@click.option(
    "--location",
    default="current",
    help="Location for weather (default: current location)",
)
@click.option(
    "--topics",
    default="technology,AI",
    help="Comma-separated news topics (default: technology,AI)",
)
@click.option(
    "--save",
    is_flag=True,
    help="Save briefing to file",
)
def main(location: str, topics: str, save: bool):
    """Generate your personalized daily briefing

    Examples:

        # Quick briefing (default settings)
        python daily_briefing.py

        # Custom location and topics
        python daily_briefing.py --location "San Francisco" --topics "AI,startups,crypto"

        # Save to file
        python daily_briefing.py --save
    """
    if save:
        asyncio.run(custom_briefing(location, topics))
    else:
        topic_list = [t.strip() for t in topics.split(",")]
        briefing_coro = create_daily_briefing(
            location=location,
            topics=topic_list,
            news_count=5,
        )
        briefing = asyncio.run(briefing_coro)
        print(briefing)


if __name__ == "__main__":
    main()
