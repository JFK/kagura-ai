"""Built-in agents for Kagura AI

This module contains core agents:
- Code execution (calculations, data processing)
- Translation and summarization
- General chatbot

Note: v4.0 is MCP-first. Personal tools (news, weather, recipes, events)
      have been removed. Use MCP connectors for domain-specific functionality.

For user-generated custom agents, see ~/.kagura/agents/
"""

# Code execution
# Personal-use presets (builder-based)
from .chatbot import ChatbotPreset
from .code_execution import CodeExecutionAgent, execute_code

# Simple function-based agents
from .summarizer import SummarizeAgent
from .translate_func import CodeReviewAgent, TranslateAgent
from .translator import TranslatorPreset

__all__ = [
    # Code execution
    "CodeExecutionAgent",
    "execute_code",
    # Personal-use presets
    "ChatbotPreset",
    "TranslatorPreset",
    # Function-based agents
    "CodeReviewAgent",
    "SummarizeAgent",
    "TranslateAgent",
]
