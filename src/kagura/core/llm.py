"""LLM integration using LiteLLM"""
from typing import Any, Optional
import litellm
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM configuration"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0


async def call_llm(
    prompt: str,
    config: LLMConfig,
    **kwargs: Any
) -> str:
    """
    Call LLM with given prompt.

    Args:
        prompt: The prompt to send
        config: LLM configuration
        **kwargs: Additional LiteLLM parameters

    Returns:
        LLM response text
    """
    response = await litellm.acompletion(
        model=config.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        top_p=config.top_p,
        **kwargs
    )

    content = response.choices[0].message.content  # type: ignore
    return content if content else ""
