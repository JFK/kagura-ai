# Personal Tools Examples

Examples demonstrating Kagura AI's built-in personal assistant tools (v3.0 feature).

## 📋 Overview

Kagura AI v3.0 includes 4 built-in personal tools:
- **`daily_news`** - Get curated news by topic
- **`weather_forecast`** - Check weather for any location
- **`search_recipes`** - Find recipes by ingredients/cuisine
- **`find_events`** - Discover local events and activities

These examples show how to use these tools to build personal assistant workflows.

---

## 📦 Installation

```bash
# Install personal tools dependencies (optional, for rich formatting)
pip install -e "examples/[personal]"

# Or run without extra dependencies (basic functionality works)
python examples/10_personal_tools/daily_briefing.py
```

---

## 🚀 Examples

### 1. Daily Briefing (`daily_briefing.py`)

Create personalized morning briefings with news and weather.

**Features**:
- Weather forecast for your location
- Curated news by topics of interest
- Save briefings to file
- Customizable topics and location

**Run**:
```bash
# Quick briefing (default settings)
python examples/10_personal_tools/daily_briefing.py

# Custom location and topics
python examples/10_personal_tools/daily_briefing.py \
    --location "San Francisco" \
    --topics "AI,startups,crypto"

# Save to file
python examples/10_personal_tools/daily_briefing.py --save
```

**Key Code**:
```python
from kagura.agents import daily_news, weather_forecast

# Get weather
weather = await weather_forecast("Tokyo")

# Get news
tech_news = await daily_news("technology", count=5)
ai_news = await daily_news("AI", count=5)

# Combine into briefing
briefing = f"""
WEATHER: {weather}

TECH NEWS:
{tech_news}

AI NEWS:
{ai_news}
"""
```

---

### 2. Recipe Finder (`recipe_finder.py`)

Find recipes based on ingredients you have or dietary preferences.

**Features**:
- Search by ingredients
- Filter by cuisine type
- Dietary restrictions (vegan, gluten-free, etc.)
- Meal planning
- Quick dinner ideas

**Run**:
```bash
# Find recipes with specific ingredients
python examples/10_personal_tools/recipe_finder.py \
    --ingredients "chicken,rice,vegetables"

# Filter by cuisine
python examples/10_personal_tools/recipe_finder.py \
    --ingredients "pasta,tomatoes" \
    --cuisine Italian

# Dietary restrictions
python examples/10_personal_tools/recipe_finder.py \
    --ingredients "tofu,vegetables" \
    --dietary vegan

# Generate meal plan
python examples/10_personal_tools/recipe_finder.py --meal-plan

# Quick dinner ideas
python examples/10_personal_tools/recipe_finder.py --quick

# Interactive mode
python examples/10_personal_tools/recipe_finder.py
```

**Key Code**:
```python
from kagura.agents import search_recipes

# Search by ingredients
recipes = await search_recipes(
    "chicken, rice, broccoli",
    cuisine="Asian"
)

# Dietary preferences
vegan_recipes = await search_recipes(
    "tofu, vegetables",
    cuisine="any"
)
```

---

### 3. Event Search (`event_search.py`)

Discover local events, concerts, meetups, and activities.

**Features**:
- Search by location and category
- Date filtering (today, this week, weekend)
- Weekend activity planner
- Tech meetup finder
- Concert search by genre

**Run**:
```bash
# Find events in your area
python examples/10_personal_tools/event_search.py

# Specific location and category
python examples/10_personal_tools/event_search.py \
    --location "San Francisco" \
    --category "tech"

# This weekend's events
python examples/10_personal_tools/event_search.py \
    --location "New York" \
    --date "this weekend"

# Plan your weekend
python examples/10_personal_tools/event_search.py \
    --location "Los Angeles" \
    --weekend

# Tech meetups
python examples/10_personal_tools/event_search.py \
    --location "Seattle" \
    --tech

# Find concerts
python examples/10_personal_tools/event_search.py \
    --location "Austin" \
    --concerts --genre "rock"
```

**Key Code**:
```python
from kagura.agents import find_events

# Find tech events
tech_events = await find_events(
    location="San Francisco",
    category="tech",
    date="this week"
)

# Weekend activities
weekend = await find_events(
    location="New York",
    category="any",
    date="this weekend"
)

# Concerts
concerts = await find_events(
    location="Austin",
    category="concerts rock",
    date="this month"
)
```

---

## 🎯 Common Use Cases

### Morning Routine Automation

```python
import asyncio
from kagura.agents import daily_news, weather_forecast

async def morning_routine():
    # Parallel execution for speed
    weather, tech_news, market_news = await asyncio.gather(
        weather_forecast("current"),
        daily_news("technology", count=3),
        daily_news("stock market", count=3),
    )

    print(f"☀️ Weather: {weather}")
    print(f"📰 Tech: {tech_news}")
    print(f"💹 Markets: {market_news}")

asyncio.run(morning_routine())
```

### Meal Planning

```python
from kagura.agents import search_recipes

async def weekly_meal_plan():
    meals = {
        "Monday": await search_recipes("chicken, vegetables"),
        "Tuesday": await search_recipes("pasta, tomatoes"),
        "Wednesday": await search_recipes("fish, rice"),
        "Thursday": await search_recipes("beef, potatoes"),
        "Friday": await search_recipes("pizza"),
    }

    for day, recipes in meals.items():
        print(f"\n{day}:\n{recipes}")
```

### Weekend Planning

```python
from kagura.agents import find_events, weather_forecast

async def plan_weekend(location: str):
    # Check weather first
    weather = await weather_forecast(location)
    print(f"Weekend Weather: {weather}")

    # Find activities
    if "rain" not in weather.lower():
        # Outdoor events
        events = await find_events(location, "outdoor", "this weekend")
    else:
        # Indoor events
        events = await find_events(location, "museums", "this weekend")

    print(f"\nSuggested Events:\n{events}")
```

---

## 🔧 Customization

All personal tools are customizable. Here's how to modify or extend them:

### Custom News Agent

```python
from kagura import agent

@agent(tools=["web_search"])
async def my_news_aggregator(topic: str, sources: list[str]) -> str:
    '''Get news about {{ topic }} from specific sources:
    {% for source in sources %}
    - {{ source }}
    {% endfor %}

    Use web_search(query) to find recent articles.
    '''

news = await my_news_aggregator(
    "AI",
    sources=["TechCrunch", "The Verge", "Ars Technica"]
)
```

### Custom Recipe Search

```python
from kagura import agent

@agent(tools=["web_search"])
async def healthy_recipe_finder(
    calories: int,
    protein_grams: int,
) -> str:
    '''Find healthy recipes with:
    - Max {{ calories }} calories
    - Min {{ protein_grams }}g protein

    Use web_search(query) to find recipes matching these requirements.
    '''

recipes = await healthy_recipe_finder(calories=500, protein_grams=30)
```

---

## 💡 Tips

**Best Practices**:
- Use `asyncio.gather()` to fetch multiple tools in parallel
- Cache frequent queries (weather, news) to reduce API calls
- Combine tools for richer experiences (news + weather)
- Save briefings to track over time

**Performance**:
```python
# Sequential (slow)
weather = await weather_forecast("Tokyo")
news = await daily_news("tech")

# Parallel (fast)
weather, news = await asyncio.gather(
    weather_forecast("Tokyo"),
    daily_news("tech")
)
```

**Scheduling**:
Use cron or Task Scheduler to run daily:
```bash
# Linux/Mac crontab
0 7 * * * cd /path/to/kagura && python examples/10_personal_tools/daily_briefing.py --save
```

---

## 📚 Learn More

- [Personal Tools API](../../docs/api/agents.md)
- [Built-in Tools](../../docs/en/api/tools.md)
- [Custom Agents](../../docs/en/guides/custom-agents.md)
- [Chat Interface](../../docs/chat-guide.md) - Use these tools interactively

---

## 🎮 Interactive Chat

You can also use these tools in Kagura's interactive chat:

```bash
kagura chat
```

```
[You] > What's the weather in Tokyo?

[AI] > (Uses weather_forecast tool)
      🌤️ Tokyo: Partly cloudy, 22°C...

[You] > Find me a recipe with chicken and rice

[AI] > (Uses search_recipes tool)
      🍳 Found these recipes...

[You] > Any tech events in San Francisco this week?

[AI] > (Uses find_events tool)
      📅 Tech events in SF...
```

These tools are automatically available in chat mode!

---

**Built with ❤️ for your daily routine**
