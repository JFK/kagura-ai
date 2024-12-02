from datetime import datetime
from typing import (Any, Callable, Deque, Dict, FrozenSet, List, Optional, Set,
                    Tuple, Type, Union, get_args, get_origin)

from pydantic import BaseModel, Field, create_model
from tzlocal import get_localzone

TIMEZONE = get_localzone()
CURRENT_DATE = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
CURRENT_TIME = datetime.now(TIMEZONE).strftime("%H:%M:%S")
AGENT = "AGENT"


class TypeMappingError(Exception):
    pass


class CheckStateError(Exception):
    pass


class GenerateStateError(Exception):
    pass


class BaseResponseModel(BaseModel):
    ERROR_MESSAGE: Optional[str] = None
    SUCCESS: bool = True
    COMPLETED: bool = False
    AGENT: Optional[Any] = None
    CURRENT_DATE: Optional[str] = CURRENT_DATE
    CURRENT_TIME: Optional[str] = CURRENT_TIME
    QUERY: Optional[str] = None


class ModelRegistry:
    _models: Dict[str, Type[BaseModel]] = {}
    _model_fields: Dict[str, Set[str]] = {}

    @classmethod
    def register(cls, name: str, model: Type[BaseModel]) -> None:
        """
        Register a custom model and store its field information.
        """
        cls._models[name] = model
        # Retrieve the model fields
        cls._model_fields[name] = set(model.model_fields.keys())

    @classmethod
    def get(cls, name: str) -> Type[BaseModel]:
        return cls._models.get(name)

    @classmethod
    def get_fields(cls, name: str) -> Set[str]:
        """
        Retrieve the field names of a custom model.
        """
        return cls._model_fields.get(name, set())

    @classmethod
    def is_custom_model_field(cls, field_name: str) -> Optional[str]:
        """
        Check if the specified field name belongs to a custom model.

        Args:
            field_name: Field name to check

        Returns:
            Optional[str]: Model name if the field belongs to a custom model, None otherwise
        """
        for model_name, fields in cls._model_fields.items():
            if field_name in fields:
                return model_name
        return None

    @classmethod
    def clear(cls) -> None:
        cls._models.clear()
        cls._model_fields.clear()


StateModel = ModelRegistry.get("StateModel")


def get_custom_model(name: str) -> Type[BaseModel]:
    return ModelRegistry.get(name)


def convert_typing_to_builtin(obj):
    origin = get_origin(obj)

    if origin is list:
        # typing.List の場合、再帰的に処理
        args = get_args(obj)
        return [convert_typing_to_builtin(arg) for arg in args]
    elif origin is dict:
        # typing.Dict の場合、再帰的に処理
        args = get_args(obj)
        # args はキーと値の型情報なので、具体的な値を取得するためには追加の処理が必要
        # ここでは簡略化のために空の辞書を返す
        return {}
    elif isinstance(obj, dict):
        # 辞書の場合、各キーと値を再帰的に処理
        return {k: convert_typing_to_builtin(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # リストの場合、各要素を再帰的に処理
        return [convert_typing_to_builtin(elem) for elem in obj]
    else:
        # その他の型はそのまま返す
        return obj


def validate_required_state_fields(
    state: BaseModel, required_fields: List[str]
) -> None:
    for field in required_fields:
        if not hasattr(state, field):
            raise CheckStateError(f"The '{field}' key is not found in the state.")


def map_type(
    type_str: str, registered_custom_models: Dict[str, Type[Any]] = None
) -> Type[Any]:
    type_str = type_str.strip()

    if registered_custom_models and type_str in registered_custom_models:
        return registered_custom_models[type_str]

    try:
        # Handle generic types
        if type_str.startswith("List["):
            inner_type_str = type_str[5:-1]
            inner_type = map_type(inner_type_str, registered_custom_models)
            return List[inner_type]

        elif type_str.startswith("Dict["):
            key_value_str = type_str[5:-1]
            key_type_str, value_type_str = [
                t.strip() for t in key_value_str.split(",", 1)
            ]
            key_type = map_type(key_type_str, registered_custom_models)
            value_type = map_type(value_type_str, registered_custom_models)
            return Dict[key_type, value_type]

        elif type_str.startswith("Optional["):
            inner_type_str = type_str[9:-1]
            inner_type = map_type(inner_type_str, registered_custom_models)
            return Optional[inner_type]

        elif type_str.startswith("Union["):
            types_str = type_str[6:-1]
            types = [
                map_type(t.strip(), registered_custom_models)
                for t in types_str.split(",")
            ]
            return Union[tuple(types)]

        elif type_str.startswith("Set["):
            inner_type_str = type_str[4:-1]
            inner_type = map_type(inner_type_str, registered_custom_models)
            return Set[inner_type]

        elif type_str.startswith("FrozenSet["):
            inner_type_str = type_str[10:-1]
            inner_type = map_type(inner_type_str, registered_custom_models)
            return FrozenSet[inner_type]

        elif type_str.startswith("Deque["):
            inner_type_str = type_str[6:-1]
            inner_type = map_type(inner_type_str, registered_custom_models)
            return Deque[inner_type]

        elif type_str.startswith("Tuple["):
            types_str = type_str[6:-1]
            if "..." in types_str:
                # Handle variable-length tuples
                element_type = map_type(
                    types_str.split("...")[0].strip(), registered_custom_models
                )
                return Tuple[element_type, ...]
            else:
                types = [
                    map_type(t.strip(), registered_custom_models)
                    for t in types_str.split(",")
                ]
                return Tuple[tuple(types)]

        # Map basic types
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "Any": Any,
            "Callable": Callable,
            "None": type(None),
        }

        if type_str in type_mapping:
            return type_mapping[type_str]

        raise TypeMappingError(f"Unknown type: {type_str}")

    except Exception as e:
        raise TypeMappingError(f"Error mapping type '{type_str}': {str(e)}")


def base_response_model_keys() -> Set[str]:
    return set(BaseResponseModel.__annotations__.keys())


class Models:
    def __init__(self, language: str = "ja"):
        self._language = language

    def check_state_error(self, state: BaseModel) -> BaseModel:
        if state.ERROR_MESSAGE:
            state.SUCCESS = False
        else:
            state.ERROR_MESSAGE = None
            state.SUCCESS = True
        return state

    def convert_model_data(
        self, data: Dict[str, Any], model_registry: ModelRegistry
    ) -> Dict[str, Any]:
        """
        データをカスタムモデルに変換する補助関数

        Args:
            data: 変換するデータ
            model_registry: ModelRegistryインスタンス

        Returns:
            Dict[str, Any]: 変換されたデータ
        """
        converted_data = {}

        for key, value in data.items():
            if isinstance(value, list):
                converted_list = []
                for item in value:
                    if isinstance(item, dict):
                        fields_match = set(item.keys())
                        for (
                            model_name,
                            model_fields,
                        ) in model_registry._model_fields.items():
                            if fields_match.issubset(model_fields):
                                model_class = model_registry.get(model_name)
                                if model_class:
                                    converted_list.append(model_class(**item))
                                    break
                        else:
                            converted_list.append(item)
                    else:
                        converted_list.append(item)
                converted_data[key] = converted_list
            elif isinstance(value, dict):
                # 辞書がカスタムモデルのフィールドと一致するか確認
                fields_match = set(value.keys())
                for model_name, model_fields in model_registry._model_fields.items():
                    if fields_match.issubset(model_fields):
                        model_class = model_registry.get(model_name)
                        if model_class:
                            converted_data[key] = model_class(**value)
                            break
                else:
                    converted_data[key] = value
            else:
                converted_data[key] = value

        return converted_data

    def generate_state_model(
        self,
        state_fields: List[Dict[str, Any]],
        custom_models: List[Dict[str, Any]] = None,
    ) -> Type[BaseModel]:
        """Generate the main state model and store it in the global StateModel variable."""
        try:

            fields = self.create_fields(state_fields, custom_models)
            StateModel = create_model(
                "StateModel", __base__=BaseResponseModel, **fields
            )
            ModelRegistry.register("StateModel", StateModel)
            return StateModel
        except Exception as e:
            raise GenerateStateError(f"Error generating state model: {str(e)}")

    def create_custom_models(
        self, custom_models: List[Dict[str, Any]]
    ) -> Dict[str, Type[Any]]:
        """Create custom models and store them in the registered_custom_models dictionary."""

        registered_custom_models = {}

        # First pass: Register all model names to handle forward references
        for model_def in custom_models:
            model_name = model_def["name"]
            registered_custom_models[model_name] = None  # Placeholder

        # Second pass: Create actual models
        for model_def in custom_models:
            model_name = model_def["name"]
            fields_def = model_def.get("fields", [])
            fields: Dict[str, Any] = {}

            for field in fields_def:
                field_name = field["name"]
                field_type_str = field.get("type", "Any")
                field_default = field.get("default", None)
                descriptions = field.get("description", [])
                description_text = ""

                if isinstance(descriptions, list):
                    for desc in descriptions:
                        if desc.get("language") == self._language:
                            description_text = desc.get("text", "")
                            break
                    if not description_text:
                        for desc in descriptions:
                            if desc.get("language") == "en":
                                description_text = desc.get("text", "")
                                break
                else:
                    description_text = descriptions

                field_type = map_type(field_type_str, registered_custom_models)
                fields[field_name] = (
                    Optional[field_type],
                    Field(default=field_default, description=description_text),
                )

            custom_model = create_model(model_name, **fields)
            registered_custom_models[model_name] = custom_model
            ModelRegistry.register(model_name, custom_model)
        return registered_custom_models

    def create_fields(
        self,
        state_fields: List[Dict[str, Any]],
        registered_custom_models: Dict[str, Type[Any]],
        target_fields: List[str] = None,
    ) -> Dict[str, Any]:
        """Create fields for the state model or response fields model."""
        fields: Dict[str, Any] = {}

        for field in state_fields:
            field_name = field["name"]
            if target_fields is None or field_name in target_fields:
                field_type_str = field.get("type", "Any")
                field_default = field.get("default", None)
                descriptions = field.get("description", [])
                description_text = ""

                if isinstance(descriptions, list):
                    for desc in descriptions:
                        if desc.get("language") == self._language:
                            description_text = desc.get("text", "")
                            break
                    if not description_text:
                        for desc in descriptions:
                            if desc.get("language") == "en":
                                description_text = desc.get("text", "")
                                break
                else:
                    description_text = descriptions

                field_type = map_type(field_type_str, registered_custom_models)
                fields[field_name] = (
                    Optional[field_type],
                    Field(default=field_default, description=description_text),
                )
        return fields

    def generate_response_fields_model(
        self,
        state_fields: List[Dict[str, Any]],
        response_fields: List[str],
        registered_custom_models: Dict[str, Type[Any]],
    ) -> Type[BaseModel]:
        """Generate a model for specific response fields."""
        fields = self.create_fields(
            state_fields, registered_custom_models, target_fields=response_fields
        )
        return create_model("ResponseFieldsModel", **fields)
