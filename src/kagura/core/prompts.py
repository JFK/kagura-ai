import json
import re
import textwrap
import uuid
from typing import Optional, Type

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel


class BasePromptException(Exception):
    pass


class BasePrompt:
    def __init__(
        self,
        prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> None:
        self._prompt = prompt
        self._template = None
        if response_model is not None and issubclass(response_model, BaseModel):
            self._response_model = response_model
            self.output_parser = PydanticOutputParser(pydantic_object=response_model)
        else:
            self.output_parser = None

    @property
    def template(self) -> str:
        if self._template is None:
            self._template = self._prompt
        return self._template

    @template.setter
    def template(self, value: str) -> None:
        self._template = value

    def _clean_and_validate_json(self, text: str) -> str:
        extracted_json = self._extract_json_from_text(text)
        try:
            json_obj = json.loads(extracted_json)
            return json.dumps(json_obj)
        except json.JSONDecodeError:
            raise BasePromptException(f"Invalid JSON: {text}")

    def _extract_json_from_text(self, text: str) -> str:
        json_patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```python\s*(\{.*?\})\s*```",
            r"```.*?\s*(\{.*?\})\s*```",
            r"\{.*\}",
            r"\[.*\]",
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                return matches[0]
        return text

    def generate_json_schema_replace_pattern(self) -> str:
        unique_id = str(uuid.uuid4()).replace("-", "")
        return f"__JSON_SCHEMA_{unique_id}__"

    def prepare_prompt(self, **kwargs) -> str:
        if self.output_parser is not None:
            self.template = None
            template_footer = textwrap.dedent(
                """
                Response JSON Schema:
                {__json_schema__}
                """
            )
            json_schema_replace_pattern = self.generate_json_schema_replace_pattern()
            template_footer = template_footer.replace(
                "__json_schema__", json_schema_replace_pattern
            )
            self.template += f"\n\n{template_footer}"
            kwargs[json_schema_replace_pattern] = (
                self.output_parser.get_format_instructions()
            )
        prompt = PromptTemplate.from_template(self.template)
        return prompt.format(**kwargs)

    def parse_response(self, response: str) -> BaseModel:
        if self.output_parser is None:
            raise ValueError("Output parser is not defined")
        response = self._clean_and_validate_json(response)
        try:
            return self.output_parser.parse(response)
        except Exception as e:
            raise BasePromptException(f"Failed to parse response: {str(e)}")
