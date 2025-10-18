"""Tests for personal assistant tools (v3.0)"""

import pytest

from kagura.agents import daily_news, find_events, search_recipes, weather_forecast


class TestDailyNews:
    """Test daily_news agent"""

    @pytest.mark.asyncio
    async def test_daily_news_callable(self):
        """Test that daily_news is callable"""
        assert callable(daily_news)
        assert hasattr(daily_news, "_is_agent")

    @pytest.mark.asyncio
    async def test_daily_news_is_agent(self):
        """Test that daily_news is decorated with @agent"""
        assert hasattr(daily_news, "_is_agent")
        assert daily_news._is_agent is True

    @pytest.mark.asyncio
    async def test_daily_news_default_topic(self):
        """Test daily_news with default topic"""
        # This would require mocking brave_web_search
        # For now, just verify function signature
        import inspect

        sig = inspect.signature(daily_news)
        assert "topic" in sig.parameters
        assert sig.parameters["topic"].default == "technology"

    @pytest.mark.asyncio
    async def test_daily_news_custom_count(self):
        """Test daily_news accepts count parameter"""
        import inspect

        sig = inspect.signature(daily_news)
        assert "count" in sig.parameters
        assert sig.parameters["count"].default == 5


class TestWeatherForecast:
    """Test weather_forecast agent"""

    @pytest.mark.asyncio
    async def test_weather_forecast_callable(self):
        """Test that weather_forecast is callable"""
        assert callable(weather_forecast)
        assert hasattr(weather_forecast, "_is_agent")

    @pytest.mark.asyncio
    async def test_weather_forecast_is_agent(self):
        """Test that weather_forecast is decorated with @agent"""
        assert hasattr(weather_forecast, "_is_agent")
        assert weather_forecast._is_agent is True

    @pytest.mark.asyncio
    async def test_weather_forecast_default_location(self):
        """Test weather_forecast with default location"""
        import inspect

        sig = inspect.signature(weather_forecast)
        assert "location" in sig.parameters
        assert sig.parameters["location"].default == "current"


class TestSearchRecipes:
    """Test search_recipes agent"""

    @pytest.mark.asyncio
    async def test_search_recipes_callable(self):
        """Test that search_recipes is callable"""
        assert callable(search_recipes)
        assert hasattr(search_recipes, "_is_agent")

    @pytest.mark.asyncio
    async def test_search_recipes_is_agent(self):
        """Test that search_recipes is decorated with @agent"""
        assert hasattr(search_recipes, "_is_agent")
        assert search_recipes._is_agent is True

    @pytest.mark.asyncio
    async def test_search_recipes_parameters(self):
        """Test search_recipes accepts ingredients and cuisine"""
        import inspect

        sig = inspect.signature(search_recipes)
        assert "ingredients" in sig.parameters
        assert "cuisine" in sig.parameters
        assert sig.parameters["cuisine"].default == "any"


class TestFindEvents:
    """Test find_events agent"""

    @pytest.mark.asyncio
    async def test_find_events_callable(self):
        """Test that find_events is callable"""
        assert callable(find_events)
        assert hasattr(find_events, "_is_agent")

    @pytest.mark.asyncio
    async def test_find_events_is_agent(self):
        """Test that find_events is decorated with @agent"""
        assert hasattr(find_events, "_is_agent")
        assert find_events._is_agent is True

    @pytest.mark.asyncio
    async def test_find_events_parameters(self):
        """Test find_events accepts location, category, date"""
        import inspect

        sig = inspect.signature(find_events)
        assert "location" in sig.parameters
        assert "category" in sig.parameters
        assert "date" in sig.parameters
        assert sig.parameters["category"].default == "any"
        assert sig.parameters["date"].default == "today"


class TestPersonalToolsIntegration:
    """Integration tests for personal tools"""

    @pytest.mark.asyncio
    async def test_all_tools_importable(self):
        """Test that all personal tools can be imported"""
        from kagura.agents import daily_news, find_events, search_recipes, weather_forecast

        assert daily_news is not None
        assert weather_forecast is not None
        assert search_recipes is not None
        assert find_events is not None

    @pytest.mark.asyncio
    async def test_all_tools_are_agents(self):
        """Test that all personal tools are decorated with @agent"""
        tools = [daily_news, weather_forecast, search_recipes, find_events]

        for tool in tools:
            assert hasattr(tool, "_is_agent")
            assert tool._is_agent is True
            assert callable(tool)
