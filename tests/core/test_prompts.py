# tests/core/test_prompts.py

import pytest
from pydantic import BaseModel
from kagura.core.prompts import BasePrompt, BasePromptException


class TestResponseModel(BaseModel):
    summary: str


class TestBasePrompt:
    def test_prepare_prompt(self):
        prompt_template = "Summarize the following text:\n{TEXT}"
        prompt = BasePrompt(prompt_template)
        final_prompt = prompt.prepare_prompt(TEXT="This is a test.")
        assert "This is a test." in final_prompt

    def test_prepare_prompt_with_response_model(self):
        prompt_template = "Summarize the following text:\n{TEXT}"
        prompt = BasePrompt(prompt_template, response_model=TestResponseModel)
        final_prompt = prompt.prepare_prompt(TEXT="This is a test.")
        assert "Response JSON Schema" in final_prompt

    def test_parse_response_valid(self):
        prompt = BasePrompt("dummy", response_model=TestResponseModel)
        response_text = '{"summary": "This is a summary."}'
        result = prompt.parse_response(response_text)
        assert result.summary == "This is a summary."

    def test_parse_response_invalid_json(self):
        prompt = BasePrompt("dummy", response_model=TestResponseModel)
        response_text = '{"summary": "This is a summary."'
        with pytest.raises(BasePromptException):
            prompt.parse_response(response_text)

    def test_extract_json_from_text(self):
        prompt = BasePrompt("dummy")
        text = 'Here is the result:\n```json\n{"key": "value"}\n```'
        extracted = prompt._extract_json_from_text(text)
        assert extracted == '{"key": "value"}'

    def test_parse_response_invalid_model(self):
        prompt = BasePrompt("dummy", response_model=TestResponseModel)
        response_text = '{"invalid_field": "value"}'
        with pytest.raises(BasePromptException):
            prompt.parse_response(response_text)
