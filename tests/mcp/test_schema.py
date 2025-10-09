"""Tests for JSON Schema generation"""
from pydantic import BaseModel

from kagura.mcp.schema import generate_json_schema, python_type_to_json_schema


def test_python_type_to_json_schema_basic_types():
    """Test basic Python type conversion"""
    assert python_type_to_json_schema(str) == {"type": "string"}
    assert python_type_to_json_schema(int) == {"type": "integer"}
    assert python_type_to_json_schema(float) == {"type": "number"}
    assert python_type_to_json_schema(bool) == {"type": "boolean"}


def test_python_type_to_json_schema_list():
    """Test list type conversion"""
    schema = python_type_to_json_schema(list[str])
    assert schema["type"] == "array"
    assert schema["items"] == {"type": "string"}


def test_python_type_to_json_schema_dict():
    """Test dict type conversion"""
    schema = python_type_to_json_schema(dict[str, int])
    assert schema["type"] == "object"
    assert schema["additionalProperties"] == {"type": "integer"}


def test_python_type_to_json_schema_pydantic():
    """Test Pydantic model conversion"""
    class User(BaseModel):
        name: str
        age: int

    schema = python_type_to_json_schema(User)
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]


def test_generate_json_schema_simple_function():
    """Test schema generation for simple function"""
    def my_func(name: str, age: int) -> str:
        pass

    schema = generate_json_schema(my_func)

    assert schema["type"] == "object"
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]
    assert schema["properties"]["name"] == {"type": "string"}
    assert schema["properties"]["age"] == {"type": "integer"}
    assert schema["required"] == ["name", "age"]


def test_generate_json_schema_optional_params():
    """Test schema generation with optional parameters"""
    def my_func(name: str, age: int = 18) -> str:
        pass

    schema = generate_json_schema(my_func)

    assert schema["required"] == ["name"]
    assert "age" not in schema["required"]


def test_generate_json_schema_no_type_hints():
    """Test schema generation without type hints"""
    def my_func(name, age):
        pass

    schema = generate_json_schema(my_func)

    assert schema["type"] == "object"
    assert schema["properties"]["name"] == {"type": "string"}
    assert schema["properties"]["age"] == {"type": "string"}


def test_generate_json_schema_complex_types():
    """Test schema generation with complex types"""
    def my_func(names: list[str], scores: dict[str, float]) -> dict[str, int]:
        pass

    schema = generate_json_schema(my_func)

    assert schema["properties"]["names"]["type"] == "array"
    assert schema["properties"]["names"]["items"] == {"type": "string"}
    assert schema["properties"]["scores"]["type"] == "object"
    assert schema["properties"]["scores"]["additionalProperties"] == {"type": "number"}
