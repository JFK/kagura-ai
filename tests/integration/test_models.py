from typing import List, Optional

import pytest
from pydantic import BaseModel, Field

from kagura.core.models import (
    CheckStateError,
    ModelRegistry,
    Models,
    TypeMappingError,
    map_type,
    validate_required_state_fields,
)


class TestModels:
    def setup_method(self):
        """各テストの前に実行"""
        ModelRegistry.clear()
        self.models = Models(language="en")  # テストは英語で実施

    def teardown_method(self):
        """各テストの後に実行"""
        ModelRegistry.clear()

    def test_create_custom_models(self):
        """カスタムモデルの作成テスト"""
        custom_models = [
            {
                "name": "TestCustomModel",
                "fields": [
                    {
                        "name": "name",
                        "type": "str",
                        "description": [{"language": "en", "text": "Name field"}],
                    },
                    {
                        "name": "value",
                        "type": "int",
                        "default": 0,
                        "description": [{"language": "en", "text": "Value field"}],
                    },
                    {
                        "name": "tags",
                        "type": "List[str]",
                        "description": [{"language": "en", "text": "Tags list"}],
                    },
                ],
            }
        ]

        registered_models = self.models.create_custom_models(custom_models)
        assert "TestCustomModel" in registered_models

        TestCustomModel = registered_models["TestCustomModel"]
        model_instance = TestCustomModel(name="test", value=42, tags=["tag1", "tag2"])
        assert model_instance.name == "test"
        assert model_instance.value == 42
        assert model_instance.tags == ["tag1", "tag2"]

    def test_map_type(self):
        """型マッピングのテスト"""
        # 基本型のテスト
        assert map_type("str") == str
        assert map_type("int") == int
        assert map_type("bool") == bool

        # ジェネリック型のテスト
        list_type = map_type("List[str]")
        assert list_type.__origin__ == list
        assert list_type.__args__[0] == str

        # カスタムモデルのテスト
        class CustomType(BaseModel):
            field: str

        registered_models = {"CustomType": CustomType}
        mapped_type = map_type("CustomType", registered_models)
        assert mapped_type == CustomType

        # 無効な型のテスト
        with pytest.raises(TypeMappingError):
            map_type("InvalidType")

    def test_validate_required_state_fields(self):
        """必須フィールドの検証テスト"""

        class TestState(BaseModel):
            field1: str
            field2: Optional[str] = None

        state = TestState(field1="test")

        # 存在するフィールドの検証
        validate_required_state_fields(state, ["field1"])

        # 存在しないフィールドの検証
        with pytest.raises(CheckStateError):
            validate_required_state_fields(state, ["field3"])

    def test_generate_state_model(self):
        """状態モデルの生成テスト"""
        state_fields = [
            {
                "name": "input_text",
                "type": "str",
                "description": [{"language": "en", "text": "Input text"}],
            },
            {
                "name": "output_text",
                "type": "str",
                "default": "",
                "description": [{"language": "en", "text": "Output text"}],
            },
        ]

        state_model = self.models.generate_state_model(state_fields)
        assert "input_text" in state_model.model_fields
        assert "output_text" in state_model.model_fields

        # モデルインスタンスの作成テスト
        instance = state_model(input_text="test")
        assert instance.input_text == "test"
        assert instance.output_text == ""
        assert instance.SUCCESS == True

    def test_check_state_error(self):
        """エラー状態のチェックテスト"""

        class TestState(BaseModel):
            ERROR_MESSAGE: Optional[str] = None
            SUCCESS: bool = True

        # エラーなしの状態
        state = TestState()
        checked_state = self.models.check_state_error(state)
        assert checked_state.SUCCESS == True
        assert checked_state.ERROR_MESSAGE is None

        # エラーありの状態
        state = TestState(ERROR_MESSAGE="Test error")
        checked_state = self.models.check_state_error(state)
        assert checked_state.SUCCESS == False
        assert checked_state.ERROR_MESSAGE == "Test error"

    def test_convert_model_data(self):
        """モデルデータの変換テスト"""

        class ItemModel(BaseModel):
            name: str
            value: int

        ModelRegistry.register("ItemModel", ItemModel)

        data = {"items": [{"name": "item1", "value": 1}, {"name": "item2", "value": 2}]}

        converted = self.models.convert_model_data(data, ModelRegistry)
        assert all(isinstance(item, ItemModel) for item in converted["items"])
        assert converted["items"][0].name == "item1"
        assert converted["items"][1].value == 2

    def test_model_registry_operations(self):
        """ModelRegistryの操作テスト"""

        # モデルの登録テスト
        class TestModel(BaseModel):
            field1: str
            field2: int

        ModelRegistry.register("TestModel", TestModel)

        # モデルの取得テスト
        retrieved_model = ModelRegistry.get("TestModel")
        assert retrieved_model == TestModel

        # フィールドの取得テスト
        fields = ModelRegistry.get_fields("TestModel")
        assert "field1" in fields
        assert "field2" in fields

        # カスタムモデルフィールドのチェック
        assert ModelRegistry.is_custom_model_field("field1") == "TestModel"
        assert ModelRegistry.is_custom_model_field("non_existent") is None

        # クリア操作のテスト
        ModelRegistry.clear()
        assert ModelRegistry.get("TestModel") is None
