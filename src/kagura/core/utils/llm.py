import os
from typing import AsyncGenerator, Dict, List

from litellm import acompletion


class LLM:
    def __init__(self, model: str = None):
        self.model = model or os.getenv("LLM_MODEL")
        if not self.model:
            raise ValueError("llm_model is required. Please set LLM_MODEL env var.")

    @classmethod
    async def generate(
        cls, model: str = None, prompt: str = None, instructions: str = None
    ) -> str:
        llm = cls(model)
        llm_response = await llm.ainvoke(prompt, instructions)
        return llm_response

    @classmethod
    async def generate_stream(
        cls, model: str = None, prompt: str = None, instructions: str = None
    ) -> AsyncGenerator[str, None]:
        llm = cls(model)
        async for chunk in llm.astream(prompt, instructions):
            yield chunk

    def _build_message(self, prompt: str, instructions: str = None) -> List[Dict]:
        messages = []
        if instructions is None and instructions == "":
            messages.append({"role": "system", "content": prompt})
        else:
            messages.append({"role": "system", "content": instructions})
            messages.append({"role": "user", "content": prompt})
        return messages

    async def astream(
        self, prompt: str, instructions: str = None
    ) -> AsyncGenerator[str, None]:
        messages = self._build_message(prompt, instructions)
        resp = await acompletion(model=self.model, messages=messages, stream=True)
        async for chunk in resp:
            c = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if c is not None:
                yield c

    async def ainvoke(self, prompt: str, instructions: str = None) -> str:
        messages = self._build_message(prompt, instructions)
        resp = await acompletion(model=self.model, messages=messages)
        response = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return response

    async def achat_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        resp = await acompletion(model=self.model, messages=messages, stream=True)
        async for chunk in resp:
            c = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if c is not None:
                yield c

    async def achat(self, messages: List[Dict]) -> str:
        resp = await acompletion(model=self.model, messages=messages)
        return resp.get("choices", [{}])[0].get("message", {}).get("content", "")
