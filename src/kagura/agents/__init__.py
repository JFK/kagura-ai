"""Built-in agents for Kagura AI

This module contains all framework-provided agents, including:
- Code execution agents
- Preset agents (translator, chatbot, etc.)
- Utility agents

For user-generated custom agents, see ~/.kagura/agents/
"""

# Code execution
# Preset agents (builder-based)
from .chatbot import ChatbotPreset
from .code_execution import CodeExecutionAgent, execute_code
from .code_review import CodeReviewPreset
from .content_writer import ContentWriterPreset
from .data_analyst import DataAnalystPreset
from .learning_tutor import LearningTutorPreset
from .personal_assistant import PersonalAssistantPreset
from .project_manager import ProjectManagerPreset
from .research import ResearchPreset

# Simple function-based agents
from .summarizer import SummarizeAgent
from .technical_support import TechnicalSupportPreset
from .translate_func import CodeReviewAgent, TranslateAgent
from .translator import TranslatorPreset

__all__ = [
    # Code execution
    "CodeExecutionAgent",
    "execute_code",
    # Presets (builder-based)
    "ChatbotPreset",
    "CodeReviewPreset",
    "ContentWriterPreset",
    "DataAnalystPreset",
    "LearningTutorPreset",
    "PersonalAssistantPreset",
    "ProjectManagerPreset",
    "ResearchPreset",
    "TechnicalSupportPreset",
    "TranslatorPreset",
    # Simple function-based agents
    "CodeReviewAgent",
    "SummarizeAgent",
    "TranslateAgent",
]
