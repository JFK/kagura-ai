"""Built-in agents for Kagura AI

This module contains personal-use agents:
- Daily tools (news, weather, recipes, events)
- Code execution (calculations, data processing)
- Translation and summarization
- Personal assistant
- General chatbot

For user-generated custom agents, see ~/.kagura/agents/
"""

# Code execution
# Personal-use presets (builder-based)
from .chatbot import ChatbotPreset
from .code_execution import CodeExecutionAgent, execute_code

# Daily personal tools (NEW in v3.0)
from .events import find_events
from .news import daily_news
from .personal_assistant import PersonalAssistantPreset
from .recipes import search_recipes

# Simple function-based agents
from .summarizer import SummarizeAgent
from .translate_func import CodeReviewAgent, TranslateAgent
from .translator import TranslatorPreset
from .weather import weather_forecast

__all__ = [
    # Code execution
    "CodeExecutionAgent",
    "execute_code",
    # Personal daily tools (v3.0)
    "daily_news",
    "weather_forecast",
    "search_recipes",
    "find_events",
    # Personal-use presets
    "ChatbotPreset",
    "PersonalAssistantPreset",
    "TranslatorPreset",
    # Function-based agents
    "CodeReviewAgent",
    "SummarizeAgent",
    "TranslateAgent",
]
