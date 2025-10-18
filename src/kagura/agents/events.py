"""Event finder agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-nano", tools=[brave_web_search], stream=True)
async def find_events(query: str) -> str:
    """Find events based on user query: {{ query }}

    User preferences (from kagura init):
    - Default location: {{ user_location }}
    - Language: {{ user_language }}

    Extract location, category, and date from the query.

    Instructions:
    1. Parse query to extract location, category, date
       - "events in Tokyo" → Tokyo (any category, today)
    2. If no location specified in query, use {{ user_location }} as default
    3. If user_location is empty, search for "events today" (general)
       - "concerts this weekend" → concerts (any location, weekend)
       - "熊本のイベント" → Kumamoto
    2. Search for "[location] events [date]" or "things to do in [location]"
    3. Filter by category if mentioned:
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
    # Event Listings

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
