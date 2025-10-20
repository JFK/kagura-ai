"""Tests for personal assistant tools (v3.0)"""

import pytest

from kagura.agents import daily_news, find_events, search_recipes, weather_forecast
from kagura.testing.mocking import LLMMock


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
    async def test_daily_news_signature(self):
        """Test daily_news has correct signature"""
        import inspect

        sig = inspect.signature(daily_news)
        assert "query" in sig.parameters
        # Single str parameter for router compatibility
        params = list(sig.parameters.keys())
        assert params == ["query"]

    @pytest.mark.asyncio
    async def test_daily_news_has_docstring(self):
        """Test that daily_news has comprehensive docstring"""
        assert daily_news.__doc__ is not None
        assert len(daily_news.__doc__) > 100
        assert "news" in daily_news.__doc__.lower()

    @pytest.mark.asyncio
    async def test_daily_news_has_agent_config(self):
        """Test that daily_news has agent configuration"""
        assert hasattr(daily_news, "_agent_config")
        assert daily_news._agent_config is not None

    @pytest.mark.asyncio
    async def test_daily_news_has_template(self):
        """Test that daily_news has prompt template"""
        assert hasattr(daily_news, "_agent_template")
        assert daily_news._agent_template is not None

    @pytest.mark.asyncio
    async def test_daily_news_model_configuration(self):
        """Test that daily_news uses correct model"""
        assert hasattr(daily_news, "_agent_config")
        config = daily_news._agent_config
        assert config.model == "gpt-5-nano"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_daily_news_execution_tech(self):
        """Test daily_news execution with tech query"""
        with LLMMock("# Today's Tech News\n\n1. **AI Breakthrough**\nMocked news"):
            result = await daily_news("tech news")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_daily_news_execution_general(self):
        """Test daily_news execution with general query"""
        with LLMMock("# Latest News\n\n1. **Breaking Story**\nMocked content"):
            result = await daily_news("latest news")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_daily_news_execution_specific_topic(self):
        """Test daily_news execution with specific topic"""
        with LLMMock("# Sports News\n\n1. **Game Result**\nMocked sports"):
            result = await daily_news("sports news")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_daily_news_execution_non_english(self):
        """Test daily_news execution with non-English query"""
        with LLMMock("# テクノロジーニュース\n\n1. **AI進歩**\nモック"):
            result = await daily_news("テクノロジーニュース")
            assert result is not None
            assert isinstance(result, str)


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
    async def test_weather_forecast_signature(self):
        """Test weather_forecast has correct signature"""
        import inspect

        sig = inspect.signature(weather_forecast)
        assert "query" in sig.parameters
        params = list(sig.parameters.keys())
        assert params == ["query"]

    @pytest.mark.asyncio
    async def test_weather_forecast_has_docstring(self):
        """Test that weather_forecast has comprehensive docstring"""
        assert weather_forecast.__doc__ is not None
        assert len(weather_forecast.__doc__) > 100
        assert "weather" in weather_forecast.__doc__.lower()

    @pytest.mark.asyncio
    async def test_weather_forecast_has_agent_config(self):
        """Test that weather_forecast has agent configuration"""
        assert hasattr(weather_forecast, "_agent_config")
        assert weather_forecast._agent_config is not None

    @pytest.mark.asyncio
    async def test_weather_forecast_has_template(self):
        """Test that weather_forecast has prompt template"""
        assert hasattr(weather_forecast, "_agent_template")
        assert weather_forecast._agent_template is not None

    @pytest.mark.asyncio
    async def test_weather_forecast_model_configuration(self):
        """Test that weather_forecast uses correct model"""
        assert hasattr(weather_forecast, "_agent_config")
        config = weather_forecast._agent_config
        assert config.model == "gpt-5-nano"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_forecast_execution_city(self):
        """Test weather_forecast execution with city query"""
        with LLMMock("# Weather Forecast\n\n**Current**: 24°C, Sunny"):
            result = await weather_forecast("weather in Tokyo")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_forecast_execution_simple(self):
        """Test weather_forecast execution with simple query"""
        with LLMMock("# Weather\n\n**Today**: Clear, 28°C"):
            result = await weather_forecast("weather")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_forecast_execution_forecast(self):
        """Test weather_forecast execution with forecast query"""
        with LLMMock("# 5-Day Forecast\n\nWeek ahead looks sunny"):
            result = await weather_forecast("weather forecast for this week")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_weather_forecast_execution_non_english(self):
        """Test weather_forecast execution with non-English query"""
        with LLMMock("# 天気予報\n\n**現在**: 晴れ、24°C"):
            result = await weather_forecast("東京の天気")
            assert result is not None
            assert isinstance(result, str)


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
    async def test_search_recipes_signature(self):
        """Test search_recipes has correct signature"""
        import inspect

        sig = inspect.signature(search_recipes)
        assert "query" in sig.parameters
        params = list(sig.parameters.keys())
        assert params == ["query"]

    @pytest.mark.asyncio
    async def test_search_recipes_has_docstring(self):
        """Test that search_recipes has comprehensive docstring"""
        assert search_recipes.__doc__ is not None
        assert len(search_recipes.__doc__) > 100
        assert "recipe" in search_recipes.__doc__.lower()

    @pytest.mark.asyncio
    async def test_search_recipes_has_agent_config(self):
        """Test that search_recipes has agent configuration"""
        assert hasattr(search_recipes, "_agent_config")
        assert search_recipes._agent_config is not None

    @pytest.mark.asyncio
    async def test_search_recipes_has_template(self):
        """Test that search_recipes has prompt template"""
        assert hasattr(search_recipes, "_agent_template")
        assert search_recipes._agent_template is not None

    @pytest.mark.asyncio
    async def test_search_recipes_model_configuration(self):
        """Test that search_recipes uses correct model"""
        assert hasattr(search_recipes, "_agent_config")
        config = search_recipes._agent_config
        assert config.model == "gpt-5-nano"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_recipes_execution_ingredient(self):
        """Test search_recipes execution with ingredient query"""
        with LLMMock("# Recipe Suggestions\n\n1. **Chicken Teriyaki**"):
            result = await search_recipes("chicken recipes")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_recipes_execution_cuisine(self):
        """Test search_recipes execution with cuisine query"""
        with LLMMock("# Italian Recipes\n\n1. **Pasta Carbonara**"):
            result = await search_recipes("Italian pasta")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_recipes_execution_specific(self):
        """Test search_recipes execution with specific query"""
        with LLMMock("# Dessert Recipes\n\n1. **Chocolate Cake**"):
            result = await search_recipes("chocolate dessert recipes")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_recipes_execution_non_english(self):
        """Test search_recipes execution with non-English query"""
        with LLMMock("# レシピ提案\n\n1. **照り焼きチキン**"):
            result = await search_recipes("鶏肉のレシピ")
            assert result is not None
            assert isinstance(result, str)


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
    async def test_find_events_signature(self):
        """Test find_events has correct signature"""
        import inspect

        sig = inspect.signature(find_events)
        assert "query" in sig.parameters
        params = list(sig.parameters.keys())
        assert params == ["query"]

    @pytest.mark.asyncio
    async def test_find_events_has_docstring(self):
        """Test that find_events has comprehensive docstring"""
        assert find_events.__doc__ is not None
        assert len(find_events.__doc__) > 100
        assert "event" in find_events.__doc__.lower()

    @pytest.mark.asyncio
    async def test_find_events_has_agent_config(self):
        """Test that find_events has agent configuration"""
        assert hasattr(find_events, "_agent_config")
        assert find_events._agent_config is not None

    @pytest.mark.asyncio
    async def test_find_events_has_template(self):
        """Test that find_events has prompt template"""
        assert hasattr(find_events, "_agent_template")
        assert find_events._agent_template is not None

    @pytest.mark.asyncio
    async def test_find_events_model_configuration(self):
        """Test that find_events uses correct model"""
        assert hasattr(find_events, "_agent_config")
        config = find_events._agent_config
        assert config.model == "gpt-5-nano"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_events_execution_location(self):
        """Test find_events execution with location query"""
        with LLMMock("# Events in Tokyo\n\n1. **Tech Conference**"):
            result = await find_events("events in Tokyo")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_events_execution_category(self):
        """Test find_events execution with category query"""
        with LLMMock("# Music Events\n\n1. **Concert Tonight**"):
            result = await find_events("music events")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_events_execution_date(self):
        """Test find_events execution with date query"""
        with LLMMock("# This Weekend\n\n1. **Festival**"):
            result = await find_events("events this weekend")
            assert result is not None
            assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_find_events_execution_non_english(self):
        """Test find_events execution with non-English query"""
        with LLMMock("# 東京のイベント\n\n1. **テックカンファレンス**"):
            result = await find_events("東京のイベント")
            assert result is not None
            assert isinstance(result, str)


class TestPersonalToolsIntegration:
    """Integration tests for personal tools"""

    @pytest.mark.asyncio
    async def test_all_tools_importable(self):
        """Test that all personal tools can be imported"""
        from kagura.agents import (
            daily_news,
            find_events,
            search_recipes,
            weather_forecast,
        )

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
