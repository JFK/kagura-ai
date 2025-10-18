"""Event finder agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-mini", tools=[brave_web_search])
async def find_events(
    location: str, category: str = "any", date: str = "today"
) -> str:
    """Find events in {{ location }} on {{ date }} ({{ category }} category)

    Search for local events and format as actionable information.

    Instructions:
    1. Search for "{{ location }} events {{ date }}" or "things to do in {{ location }}"
    2. Filter by category if specified:
       - Music/concerts
       - Sports
       - Arts/culture
       - Food/dining
       - Festivals
       - Networking/meetups
    3. Handle date specifications:
       - "today", "tomorrow", "this weekend", "this week"
       - Specific dates like "October 20"
    4. Format each event with:
       - **Event Name** in bold
       - Date and time
       - Venue/location details
       - Brief description (1-2 sentences)
       - Ticket/registration link (if available)
       - Price (if mentioned)
    5. Return 5-10 relevant events
    6. Sort by: Date proximity, relevance, popularity

    Example output format:
    ```
    # Events in {{ location|title }} ({{ date|title }})

    1. **Tech Conference 2025**
       📅 October 20, 2025 | 10:00 AM - 6:00 PM
       📍 Kumamoto Convention Center
       💡 Annual technology conference with speakers from top companies
       🎫 [Register here](https://...) | ¥5,000

    2. **Weekend Food Market**
       📅 October 19-20 | 9:00 AM - 5:00 PM
       📍 Central Park, Kumamoto
       🍽️ Local food vendors, live music, family-friendly
       🎫 Free entry

    3. **Jazz Night at Blue Note**
       ...
    ```

    Be specific about times, locations, and how to attend.
    Mention if events are free, family-friendly, or require registration.
    """
    ...
