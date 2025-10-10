"""Tests for preset agents"""
import pytest

from kagura.chat.preset import CodeReviewAgent, SummarizeAgent, TranslateAgent


@pytest.mark.asyncio
async def test_translate_agent():
    """Test TranslateAgent basic functionality"""
    result = await TranslateAgent("Hello World", target_language="ja")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_translate_agent_default_language():
    """Test TranslateAgent with default language (Japanese)"""
    result = await TranslateAgent("Good morning")
    assert isinstance(result, str)
    assert len(result) > 0


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
    assert isinstance(result, str)
    assert len(result) > 0
    assert len(result) < len(long_text)


@pytest.mark.asyncio
async def test_code_review_agent():
    """Test CodeReviewAgent"""
    code = """
def add(a, b):
    return a + b
"""
    result = await CodeReviewAgent(code, language="python")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_code_review_agent_default_language():
    """Test CodeReviewAgent with default language"""
    code = """
def divide(a, b):
    return a / b
"""
    result = await CodeReviewAgent(code)
    assert isinstance(result, str)
    # Should detect potential division by zero
    assert len(result) > 0
