"""Tests for type-based response parser"""

from typing import Optional

import pytest
from pydantic import BaseModel

from kagura.core.parser import (
    extract_json,
    parse_basic_type,
    parse_response,
)


# Test models
class Person(BaseModel):
    name: str
    age: int


class Address(BaseModel):
    street: str
    city: str
    zipcode: str


# Test extract_json
def test_extract_json_from_code_block():
    """Test JSON extraction from markdown code blocks"""
    text = '```json\n{"name": "Alice", "age": 30}\n```'
    result = extract_json(text)
    assert result == '{"name": "Alice", "age": 30}'


def test_extract_json_from_code_block_without_lang():
    """Test JSON extraction from code blocks without language marker"""
    text = '```\n{"name": "Bob"}\n```'
    result = extract_json(text)
    assert result == '{"name": "Bob"}'


def test_extract_json_from_text():
    """Test JSON extraction from plain text"""
    text = 'The person is {"name": "Charlie", "age": 25} and lives here.'
    result = extract_json(text)
    assert '"name": "Charlie"' in result


def test_extract_json_array():
    """Test JSON array extraction"""
    text = 'Here are the items: ["apple", "banana", "cherry"]'
    result = extract_json(text)
    assert result == '["apple", "banana", "cherry"]'


def test_extract_json_no_json():
    """Test extraction when no JSON present"""
    text = "Just plain text with no JSON"
    result = extract_json(text)
    assert result == text


# Test parse_basic_type
def test_parse_basic_type_int():
    """Test parsing integers"""
    assert parse_basic_type("42", int) == 42
    assert parse_basic_type("The answer is 42", int) == 42
    assert parse_basic_type("-10", int) == -10


def test_parse_basic_type_float():
    """Test parsing floats"""
    assert parse_basic_type("3.14", float) == 3.14
    assert parse_basic_type("The value is 2.5", float) == 2.5
    assert parse_basic_type("-1.5", float) == -1.5


def test_parse_basic_type_bool():
    """Test parsing booleans"""
    assert parse_basic_type("true", bool) is True
    assert parse_basic_type("True", bool) is True
    assert parse_basic_type("yes", bool) is True
    assert parse_basic_type("false", bool) is False
    assert parse_basic_type("False", bool) is False
    assert parse_basic_type("no", bool) is False


def test_parse_basic_type_str():
    """Test parsing strings"""
    assert parse_basic_type("hello", str) == "hello"
    assert parse_basic_type("  spaces  ", str) == "spaces"


def test_parse_basic_type_int_error():
    """Test integer parsing error"""
    with pytest.raises(ValueError, match="No integer found"):
        parse_basic_type("no numbers here", int)


def test_parse_basic_type_bool_error():
    """Test boolean parsing error"""
    with pytest.raises(ValueError, match="No boolean found"):
        parse_basic_type("maybe", bool)


# Test parse_response with basic types
def test_parse_response_str():
    """Test parsing string response"""
    result = parse_response("Hello, World!", str)
    assert result == "Hello, World!"


def test_parse_response_int():
    """Test parsing integer response"""
    result = parse_response("The count is 42", int)
    assert result == 42


def test_parse_response_float():
    """Test parsing float response"""
    result = parse_response("The value is 3.14", float)
    assert result == 3.14


def test_parse_response_bool():
    """Test parsing boolean response"""
    assert parse_response("The answer is true", bool) is True
    assert parse_response("false", bool) is False


# Test parse_response with Pydantic models
def test_parse_response_pydantic_model():
    """Test parsing Pydantic model from JSON"""
    response = '{"name": "Alice", "age": 30}'
    result = parse_response(response, Person)
    assert isinstance(result, Person)
    assert result.name == "Alice"
    assert result.age == 30


def test_parse_response_pydantic_model_in_code_block():
    """Test parsing Pydantic model from code block"""
    response = '```json\n{"name": "Bob", "age": 25}\n```'
    result = parse_response(response, Person)
    assert isinstance(result, Person)
    assert result.name == "Bob"
    assert result.age == 25


def test_parse_response_pydantic_model_with_text():
    """Test parsing Pydantic model with surrounding text"""
    response = 'Here is the person: {"name": "Charlie", "age": 35}'
    result = parse_response(response, Person)
    assert isinstance(result, Person)
    assert result.name == "Charlie"


def test_parse_response_pydantic_model_error():
    """Test Pydantic model parsing error"""
    response = '{"name": "Alice"}'  # Missing required field 'age'
    with pytest.raises(ValueError, match="Failed to validate"):
        parse_response(response, Person)


# Test parse_response with list types
def test_parse_response_list_str_from_json():
    """Test parsing list[str] from JSON"""
    response = '["apple", "banana", "cherry"]'
    result = parse_response(response, list[str])
    assert result == ["apple", "banana", "cherry"]


def test_parse_response_list_int_from_json():
    """Test parsing list[int] from JSON"""
    response = "[1, 2, 3, 4, 5]"
    result = parse_response(response, list[int])
    assert result == [1, 2, 3, 4, 5]


def test_parse_response_list_str_from_text():
    """Test parsing list[str] from comma-separated text"""
    response = "apple, banana, cherry"
    result = parse_response(response, list[str])
    assert "apple" in result
    assert "banana" in result
    assert "cherry" in result


def test_parse_response_list_str_from_newlines():
    """Test parsing list[str] from newline-separated text"""
    response = "apple\nbanana\ncherry"
    result = parse_response(response, list[str])
    assert "apple" in result
    assert "banana" in result
    assert "cherry" in result


def test_parse_response_list_pydantic():
    """Test parsing list of Pydantic models"""
    response = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
    result = parse_response(response, list[Person])
    assert len(result) == 2
    assert result[0].name == "Alice"
    assert result[0].age == 30
    assert result[1].name == "Bob"
    assert result[1].age == 25


# Test parse_response with Optional types
def test_parse_response_optional_str():
    """Test parsing Optional[str]"""
    result = parse_response("Hello", Optional[str])
    assert result == "Hello"


def test_parse_response_optional_int():
    """Test parsing Optional[int]"""
    result = parse_response("42", Optional[int])
    assert result == 42


def test_parse_response_optional_none():
    """Test parsing Optional returns None on error"""
    result = parse_response("invalid json {", Optional[Person])
    assert result is None


def test_parse_response_optional_pydantic():
    """Test parsing Optional[Pydantic]"""
    response = '{"name": "Alice", "age": 30}'
    result = parse_response(response, Optional[Person])
    assert isinstance(result, Person)
    assert result.name == "Alice"


# Test integration with @agent decorator
@pytest.mark.asyncio
async def test_agent_with_int_return_type():
    """Test @agent with int return type"""
    from unittest.mock import AsyncMock, patch

    from kagura import agent

    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "The count is 42"

        @agent
        async def count_words(text: str) -> int:
            """Count words in: {{ text }}"""
            pass

        result = await count_words("hello world")
        assert isinstance(result, int)
        assert result == 42


@pytest.mark.asyncio
async def test_agent_with_pydantic_return_type():
    """Test @agent with Pydantic model return type"""
    from unittest.mock import AsyncMock, patch

    from kagura import agent

    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"name": "Alice", "age": 30}'

        @agent
        async def extract_person(text: str) -> Person:
            """Extract person from: {{ text }}"""
            pass

        result = await extract_person("Alice is 30 years old")
        assert isinstance(result, Person)
        assert result.name == "Alice"
        assert result.age == 30


@pytest.mark.asyncio
async def test_agent_with_list_return_type():
    """Test @agent with list return type"""
    from unittest.mock import AsyncMock, patch

    from kagura import agent

    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '["apple", "banana", "cherry"]'

        @agent
        async def extract_items(text: str) -> list[str]:
            """Extract items from: {{ text }}"""
            pass

        result = await extract_items("I like apple, banana, and cherry")
        assert isinstance(result, list)
        assert "apple" in result
        assert "banana" in result
        assert "cherry" in result


@pytest.mark.asyncio
async def test_agent_with_str_return_type():
    """Test @agent with str return type (no parsing)"""
    from unittest.mock import AsyncMock, patch

    from kagura import agent

    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Hello, World!"

        @agent
        async def greet(name: str) -> str:
            """Say hello to {{ name }}"""
            pass

        result = await greet("World")
        assert isinstance(result, str)
        assert result == "Hello, World!"


@pytest.mark.asyncio
async def test_agent_with_optional_return_type():
    """Test @agent with Optional return type"""
    from unittest.mock import AsyncMock, patch

    from kagura import agent

    with patch("kagura.core.decorators.call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"name": "Alice", "age": 30}'

        @agent
        async def maybe_extract(text: str) -> Optional[Person]:
            """Try to extract person from: {{ text }}"""
            pass

        result = await maybe_extract("Alice is 30")
        assert isinstance(result, Person)
        assert result.name == "Alice"
