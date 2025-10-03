# tests/core/test_models.py

import pytest
from pydantic import BaseModel

from kagura.core.models import Models, TypeMappingError, map_type


class TestModels:
    def setup_method(self):
        self.models = Models(language="en")

    def test_map_type_basic(self):
        assert map_type("str") == str
        assert map_type("int") == int
        assert map_type("float") == float
        assert map_type("bool") == bool

    @pytest.mark.skip()
    def test_map_type_generic(self):
        list_str_type = map_type("List[str]")
        assert list_str_type.__origin__ == list
        assert list_str_type.__args__[0] == str

        optional_int_type = map_type("Optional[int]")
        assert True if isinstance(optional_int_type.__origin__, None) else False
        assert optional_int_type.__args__[0] == int

    def test_map_type_custom(self):
        class CustomType(BaseModel):
            field: str

        registered_models = {"CustomType": CustomType}
        mapped_type = map_type("CustomType", registered_models)
        assert mapped_type == CustomType

    def test_map_type_invalid(self):
        with pytest.raises(TypeMappingError):
            map_type("InvalidType")

    def test_generate_state_model(self):
        state_fields = [
            {
                "name": "field1",
                "type": "str",
                "description": [{"language": "en", "text": "Field 1"}],
            },
            {
                "name": "field2",
                "type": "int",
                "description": [{"language": "en", "text": "Field 2"}],
            },
        ]
        state_model = self.models.generate_state_model(state_fields)
        assert "field1" in state_model.model_fields
        assert "field2" in state_model.model_fields

        instance = state_model(field1="value1", field2=42)
        assert instance.field1 == "value1"
        assert instance.field2 == 42

    def test_create_custom_models(self):
        custom_models = [
            {
                "name": "CustomModel",
                "fields": [
                    {
                        "name": "name",
                        "type": "str",
                        "description": [{"language": "en", "text": "Name"}],
                    },
                    {
                        "name": "value",
                        "type": "int",
                        "description": [{"language": "en", "text": "Value"}],
                    },
                ],
            }
        ]
        registered_models = self.models.create_custom_models(custom_models)
        assert "CustomModel" in registered_models
        CustomModel = registered_models["CustomModel"]
        instance = CustomModel(name="test", value=123)
        assert instance.name == "test"
        assert instance.value == 123

    def test_generate_response_fields_model(self):
        state_fields = [
            {
                "name": "field1",
                "type": "str",
                "description": [{"language": "en", "text": "Field 1"}],
            },
            {
                "name": "field2",
                "type": "int",
                "description": [{"language": "en", "text": "Field 2"}],
            },
        ]
        response_fields = ["field1"]
        response_model = self.models.generate_response_fields_model(
            state_fields, response_fields, {}
        )
        assert "field1" in response_model.model_fields
        assert "field2" not in response_model.model_fields
