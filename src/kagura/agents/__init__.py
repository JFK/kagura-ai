"""Built-in agents for Kagura AI

This module contains personal-use agents:
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
from .personal_assistant import PersonalAssistantPreset

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
    "PersonalAssistantPreset",
    "TranslatorPreset",
    # Function-based agents
    "CodeReviewAgent",
    "SummarizeAgent",
    "TranslateAgent",
]
