"""Tests for preset agents"""
import pytest

from kagura.agents.summarizer import SummarizeAgent
from kagura.agents.translate_func import CodeReviewAgent, TranslateAgent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_translate_agent():
    """Test TranslateAgent basic functionality"""
    result = await TranslateAgent("Hello World", target_language="ja")
    # Agent can return str (-> str annotation) or LLMResponse
    if isinstance(result, str):
        # Direct string response (-> str annotation)
        assert len(result) > 0
    else:
        # LLMResponse object
        assert hasattr(result, "content")
        assert isinstance(result.content, str)
        assert len(result.content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_translate_agent_default_language():
    """Test TranslateAgent with default language (Japanese)"""
    result = await TranslateAgent("Good morning")
    # Agent can return str (-> str annotation) or LLMResponse
    if isinstance(result, str):
        # Direct string response (-> str annotation)
        assert len(result) > 0
    else:
        # LLMResponse object
        assert hasattr(result, "content")
        assert isinstance(result.content, str)
        assert len(result.content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_summarize_agent():
    """Test SummarizeAgent"""
    long_text = (
        "Artificial intelligence (AI) is intelligence demonstrated by machines, "
        "as opposed to natural intelligence displayed by animals including humans. "
        "AI research has been defined as the field of study of intelligent agents, "
        "which refers to any system that perceives its environment and takes actions "
        "that maximize its chance of achieving its goals."
    )
    result = await SummarizeAgent(long_text, max_sentences=2)
    # Agent can return str (-> str annotation) or LLMResponse
    if isinstance(result, str):
        # Direct string response (-> str annotation)
        assert len(result) > 0
        assert len(result) < len(long_text)
    else:
        # LLMResponse object
        assert hasattr(result, "content")
        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert len(result.content) < len(long_text)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_review_agent():
    """Test CodeReviewAgent"""
    code = """
def add(a, b):
    return a + b
"""
    result = await CodeReviewAgent(code, language="python")
    # Agent can return str (-> str annotation) or LLMResponse
    if isinstance(result, str):
        # Direct string response (-> str annotation)
        assert len(result) > 0
    else:
        # LLMResponse object
        assert hasattr(result, "content")
        assert isinstance(result.content, str)
        assert len(result.content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_code_review_agent_default_language():
    """Test CodeReviewAgent with default language"""
    code = """
def divide(a, b):
    return a / b
"""
    result = await CodeReviewAgent(code)
    # Agent can return str (-> str annotation) or LLMResponse
    if isinstance(result, str):
        # Direct string response (-> str annotation)
        # Should detect potential division by zero
        assert len(result) > 0
    else:
        # LLMResponse object
        assert hasattr(result, "content")
        # Should detect potential division by zero
        assert len(result.content) > 0
