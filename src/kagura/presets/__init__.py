"""Agent Builder Presets - Pre-configured agent templates."""

from .chatbot import ChatbotPreset
from .code_review import CodeReviewPreset
from .content_writer import ContentWriterPreset
from .data_analyst import DataAnalystPreset
from .learning_tutor import LearningTutorPreset
from .personal_assistant import PersonalAssistantPreset
from .project_manager import ProjectManagerPreset
from .research import ResearchPreset
from .technical_support import TechnicalSupportPreset
from .translator import TranslatorPreset

__all__ = [
    # Existing presets
    "ChatbotPreset",
    "CodeReviewPreset",
    "ResearchPreset",
    # New presets (RFC-026)
    "TranslatorPreset",
    "DataAnalystPreset",
    "PersonalAssistantPreset",
    "ContentWriterPreset",
    "TechnicalSupportPreset",
    "LearningTutorPreset",
    "ProjectManagerPreset",
]
