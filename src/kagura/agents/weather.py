"""Weather forecast agent for personal assistant use."""

from kagura import agent
from kagura.tools.brave_search import brave_web_search


@agent(model="gpt-5-nano", tools=[brave_web_search], stream=True)
async def weather_forecast(query: str) -> str:
    """Get weather forecast based on user query: {{ query }}

    User preferences (from kagura init):
    - Default location: {{ user_location }}
    - Language: {{ user_language }}

    Extract location from the query and search for weather information.

    Instructions:
    1. Parse query to extract location (e.g., "weather in Tokyo" → Tokyo)
    2. If no location specified in query, use {{ user_location }} as default
    3. If user_location is empty, ask user for location
    3. Search for "[location] weather today" or "[location] weather forecast"
    3. Include the following information:
       - **Current conditions**: Temperature, weather (sunny/rainy/etc.)
       - **Today's forecast**: High/low temperatures
       - **Tomorrow's forecast**: Brief overview
       - **Precipitation**: Chance of rain
       - **Helpful tips**: Umbrella needed? Clothing suggestions?
    4. Format as clean, readable text (not overly technical)
    5. Use local units (Celsius for most countries, Fahrenheit for US if detected)

    Example output format:
    ```
    # Weather Forecast

    **Current Conditions** (as of [time]):
    - Temperature: 24°C
    - Conditions: Partly cloudy
    - Humidity: 65%

    **Today's Forecast**:
    - High: 31°C, Low: 21°C
    - Precipitation: 30% chance in evening
    - Conditions: Sunny, turning cloudy

    **Tomorrow**:
    - High: 28°C, Low: 20°C
    - Chance of rain: 60% afternoon

    **Tips**:
    - 💧 Bring an umbrella for tonight
    - 👕 Light clothing recommended, but bring a cardigan for evening
    ```

    Be helpful and conversational. Think about what a person would
    actually want to know.
    """
    ...
