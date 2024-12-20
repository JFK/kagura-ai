from typing import AsyncGenerator, Dict, List, Optional

from litellm import acompletion
from litellm.utils import CustomStreamWrapper, ModelResponse


class LLM:
    def __init__(self, model: Optional[str] = None):
        self._model = model
        if not self._model:
            raise ValueError("llm_model is required. Please set LLM_MODEL env var.")

    @property
    def model(self) -> str:
        if not self._model:
            raise ValueError("Model is not set.")
        return self._model

    def _build_message(
        self, prompt: Optional[str], instructions: Optional[str] = None
    ) -> List[Dict]:
        messages = []
        if instructions:
            messages.append({"role": "system", "content": instructions})
        if prompt:
            messages.append({"role": "user", "content": prompt})
        return messages

    async def astream(
        self, prompt: Optional[str], instructions: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if not self.model:
            raise ValueError("Model is not set.")
        messages = self._build_message(prompt, instructions)
        try:
            # Call acompletion
            resp = await acompletion(model=self.model, messages=messages, stream=True)

            # Handle streaming response
            if isinstance(resp, CustomStreamWrapper):
                async for chunk in resp:
                    content = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if content:
                        yield content
            else:
                raise RuntimeError(
                    "Expected a streaming response, got a non-streaming object."
                )
        except Exception as e:
            raise RuntimeError(f"Error in astream: {str(e)}")

    async def ainvoke(
        self, prompt: Optional[str], instructions: Optional[str] = None
    ) -> str:
        if not self.model:
            raise ValueError("Model is not set.")
        messages = self._build_message(prompt, instructions)
        try:
            resp = await acompletion(model=self.model, messages=messages)
            if isinstance(resp, ModelResponse):
                return (
                    resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
            else:
                raise RuntimeError(
                    "Expected a non-streaming response, got a streaming object."
                )
        except Exception as e:
            raise RuntimeError(f"Error in ainvoke: {e}")

    async def achat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        if not self.model:
            raise ValueError("Model is not set.")
        try:
            resp = await acompletion(model=self.model, messages=messages, stream=True)
            if isinstance(resp, CustomStreamWrapper):
                async for chunk in resp:
                    content = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if content:
                        yield content
            else:
                raise RuntimeError(
                    "Expected a streaming response, got a non-streaming object."
                )
        except Exception as e:
            raise RuntimeError(f"Error in achat_stream: {e}")

    async def achat(self, messages: List[Dict]) -> str:
        if not self.model:
            raise ValueError("Model is not set.")
        try:
            resp = await acompletion(model=self.model, messages=messages)
            if isinstance(resp, ModelResponse):
                return (
                    resp.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
            else:
                raise RuntimeError(
                    "Expected a non-streaming response, got a streaming object."
                )
        except Exception as e:
            raise RuntimeError(f"Error in achat: {e}")
