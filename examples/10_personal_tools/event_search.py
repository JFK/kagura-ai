"""Event Search Example - Find Local Events

This example demonstrates how to use Kagura AI's event search tool to find
local events, concerts, meetups, and activities.

Usage:
    # No extra dependencies needed
    python examples/10_personal_tools/event_search.py

    # Or specify location and category
    python examples/10_personal_tools/event_search.py --location "San Francisco" --category "tech"
"""

import asyncio

import click
from kagura.agents import find_events


async def search_events(
    location: str = "current",
    category: str = "any",
    date: str = "today",
) -> str:
    """
    Search for local events

    Args:
        location: City or area
        category: Event category (tech, music, sports, arts, etc.)
        date: Date filter (today, this week, this weekend, etc.)

    Returns:
        Formatted event listings
    """
    print("\n🔍 Searching events...")
    print(f"   Location: {location}")
    print(f"   Category: {category}")
    print(f"   Date: {date}")

    # Build query
    query_parts = []
    if category != "any":
        query_parts.append(category)
    query_parts.append("events")
    if location != "current":
        query_parts.append(f"in {location}")
    query_parts.append(date)

    query = " ".join(query_parts)
    events = await find_events(query)

    output = f"""
{'=' * 60}
📅 EVENTS IN {location.upper()}
{'=' * 60}

Category: {category}
Date: {date}

{events}

{'=' * 60}
💡 Tip: Click event links for tickets and details!
{'=' * 60}
"""
    return output


async def weekend_planner(location: str = "current") -> str:
    """
    Find weekend activities

    Args:
        location: City or area

    Returns:
        Weekend event suggestions
    """
    print(f"\n🎉 Planning your weekend in {location}...")

    categories = ["music", "arts", "food", "sports"]
    weekend_events = []

    for category in categories:
        print(f"   Searching {category} events...")
        query = f"{category} events in {location} this weekend"
        events = await find_events(query)
        weekend_events.append((category, events))

    output = f"""
{'=' * 60}
🎉 WEEKEND PLANNER - {location.upper()}
{'=' * 60}

"""

    for category, events in weekend_events:
        output += f"""
{category.upper()} 🎵
{'─' * 60}
{events[:300]}...

"""

    output += f"""
{'=' * 60}
Have a great weekend! 🎊
{'=' * 60}
"""

    return output


async def tech_meetups(location: str = "current") -> str:
    """
    Find tech meetups and conferences

    Args:
        location: City or area

    Returns:
        Tech event listings
    """
    print(f"\n💻 Finding tech events in {location}...")

    query = f"tech meetups in {location} this week"
    events = await find_events(query)

    output = f"""
{'=' * 60}
💻 TECH EVENTS & MEETUPS
{'=' * 60}

Location: {location}
Time: This Week

{events}

{'=' * 60}
🤝 Great for networking and learning!
{'=' * 60}
"""
    return output


async def concert_finder(
    location: str = "current",
    genre: str = "any",
) -> str:
    """
    Find concerts and live music

    Args:
        location: City or area
        genre: Music genre (rock, jazz, classical, etc.)

    Returns:
        Concert listings
    """
    print(f"\n🎵 Finding concerts in {location}...")

    if genre != "any":
        query = f"{genre} concerts in {location} this month"
    else:
        query = f"concerts in {location} this month"

    events = await find_events(query)

    output = f"""
{'=' * 60}
🎵 CONCERTS & LIVE MUSIC
{'=' * 60}

Location: {location}
Genre: {genre}
Time: This Month

{events}

{'=' * 60}
🎫 Book tickets early for popular shows!
{'=' * 60}
"""
    return output


@click.command()
@click.option(
    "--location",
    default="current",
    help="City or area (default: current location)",
)
@click.option(
    "--category",
    default="any",
    help="Event category (tech, music, sports, arts, food, etc.)",
)
@click.option(
    "--date",
    default="today",
    help="Date filter (today, this week, this weekend, etc.)",
)
@click.option(
    "--weekend",
    is_flag=True,
    help="Plan your weekend activities",
)
@click.option(
    "--tech",
    is_flag=True,
    help="Find tech meetups and conferences",
)
@click.option(
    "--concerts",
    is_flag=True,
    help="Find concerts and live music",
)
@click.option(
    "--genre",
    help="Music genre for concerts (rock, jazz, classical, etc.)",
)
def main(
    location: str,
    category: str,
    date: str,
    weekend: bool,
    tech: bool,
    concerts: bool,
    genre: str | None,
):
    """Find local events, concerts, meetups, and activities

    Examples:

        # Find events in your area
        python event_search.py

        # Specific location and category
        python event_search.py --location "San Francisco" --category "tech"

        # This weekend's events
        python event_search.py --location "New York" --date "this weekend"

        # Plan your weekend
        python event_search.py --location "Los Angeles" --weekend

        # Tech meetups
        python event_search.py --location "Seattle" --tech

        # Find concerts
        python event_search.py --location "Austin" --concerts --genre "rock"
    """
    if weekend:
        result = asyncio.run(weekend_planner(location))
        print(result)
    elif tech:
        result = asyncio.run(tech_meetups(location))
        print(result)
    elif concerts:
        genre_str = genre or "any"
        result = asyncio.run(concert_finder(location, genre_str))
        print(result)
    else:
        result = asyncio.run(search_events(location, category, date))
        print(result)


if __name__ == "__main__":
    main()
