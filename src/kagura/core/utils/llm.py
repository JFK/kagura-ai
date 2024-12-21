from typing import AsyncGenerator, Dict, List

from litellm import acompletion
from litellm.utils import ModelResponse, Choices


class LLM:
    def __init__(self, model: str):
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @classmethod
    async def generate(
        cls, model: str = "", prompt: str = "", instructions: str = ""
    ) -> str:
        llm = cls(model)
        llm_response = await llm.ainvoke(prompt or "", instructions or "")
        return llm_response or ""

    @classmethod
    async def generate_stream(
        cls, model: str = "", prompt: str = "", instructions: str = ""
    ) -> AsyncGenerator[str, None]:
        llm = cls(model)
        async for chunk in llm.astream(prompt or "", instructions or ""):
            yield chunk

    def _build_message(self, prompt: str, instructions: str = "") -> List[Dict]:
        messages = []
        if instructions is None and instructions == "":
            messages.append({"role": "system", "content": prompt})
        else:
            messages.append({"role": "system", "content": instructions})
            messages.append({"role": "user", "content": prompt})
        return messages

    async def astream(
        self, prompt: str, instructions: str = ""
    ) -> AsyncGenerator[str, None]:
        messages = self._build_message(prompt, instructions)
        try:
            resp = await acompletion(model=self._model, messages=messages, stream=True)
            if isinstance(resp, AsyncGenerator):
                async for chunk in resp:
                    c = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if c is not None:
                        yield c
        except Exception as e:
            raise RuntimeError(f"Error in astream: {e}")

    async def ainvoke(self, prompt: str, instructions: str = "") -> str:
        messages = self._build_message(prompt, instructions)
        try:
            resp = await acompletion(model=self._model, messages=messages)
            if isinstance(resp, ModelResponse) and isinstance(resp.choices[0], Choices):
                return resp.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Error in ainvoke: {e}")
        return ""

    async def achat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        try:
            resp = await acompletion(model=self._model, messages=messages, stream=True)
            if isinstance(resp, AsyncGenerator):
                async for chunk in resp:
                    c = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )
                    if c is not None:
                        yield c
        except Exception as e:
            raise RuntimeError(f"Error in achat_stream: {e}")

    async def achat(self, messages: List[Dict]) -> str:
        try:
            resp = await acompletion(model=self._model, messages=messages)
            if isinstance(resp, ModelResponse) and isinstance(resp.choices[0], Choices):
                return resp.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Error in achat: {e}")
        return ""
