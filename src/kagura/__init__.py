"""
Kagura AI 2.0 - Python-First AI Agent Framework

Example:
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await hello("World")
"""
from .builder import AgentBuilder
from .core.decorators import agent, tool, workflow
from .presets import ChatbotPreset, CodeReviewPreset, ResearchPreset
from .version import __version__

__all__ = [
    "agent",
    "tool",
    "workflow",
    "AgentBuilder",
    "ChatbotPreset",
    "CodeReviewPreset",
    "ResearchPreset",
    "__version__",
]
