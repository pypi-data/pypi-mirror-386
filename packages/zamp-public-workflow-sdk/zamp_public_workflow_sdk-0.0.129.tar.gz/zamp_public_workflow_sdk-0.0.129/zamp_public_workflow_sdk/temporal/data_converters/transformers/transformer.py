from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import to_jsonable_python

from zamp_public_workflow_sdk.temporal.data_converters.transformers.base import BaseTransformer
from zamp_public_workflow_sdk.temporal.data_converters.transformers.collections.base import BaseCollectionsTransformer
from zamp_public_workflow_sdk.temporal.data_converters.transformers.models import GenericSerializedValue
from zamp_public_workflow_sdk.temporal.data_converters.type_utils import (
    get_fqn,
    get_individual_type_field_name,
    get_reference_from_fqn,
    get_type_field_name,
    is_dict_type,
    is_pydantic_model,
    is_type_field,
)


class Transformer:
    _transformers: list[BaseTransformer] = []
    _collection_transformers: list[BaseCollectionsTransformer] = []

    @classmethod
    def register_transformer(cls, transformer: BaseTransformer):
        cls._transformers.append(transformer)

    @classmethod
    def register_collection_transformer(cls, transformer: BaseCollectionsTransformer):
        cls._collection_transformers.append(transformer)

    @classmethod
    def serialize(cls, value) -> GenericSerializedValue:
        # Temporary hack to serialize ColumnMappingResult
        if "TableDetectionOutput" in str(type(value)):
            return GenericSerializedValue(
                serialized_value=to_jsonable_python(value),
                serialized_type_hint=get_fqn(type(value)),
            )

        if value is None:
            return GenericSerializedValue(serialized_value=None, serialized_type_hint=get_fqn(type(value)))

        for collection_transformer in cls._collection_transformers:
            serialized = collection_transformer.serialize(value)
            if serialized is not None:
                return serialized

        if cls._should_serialize(value):
            serialized_result = {}
            for item_key, item_type, item_value in cls._get_enumerator(value):
                serialized = cls.serialize(item_value)
                if type(serialized) is GenericSerializedValue:
                    serialized_result[item_key] = serialized.serialized_value
                    serialized_result[get_type_field_name(item_key)] = serialized.serialized_type_hint
                    if serialized.serialized_individual_type_hints is not None:
                        serialized_result[get_individual_type_field_name(item_key)] = (
                            serialized.serialized_individual_type_hints
                        )
                else:
                    serialized_result[item_key] = serialized

            return GenericSerializedValue(
                serialized_value=serialized_result,
                serialized_type_hint=get_fqn(type(value)),
            )

        for transformer in cls._transformers:
            serialized = transformer.serialize(value)
            if serialized is not None:
                return serialized

        return GenericSerializedValue(
            serialized_value=to_jsonable_python(value),
            serialized_type_hint=get_fqn(type(value)),
        )

    @classmethod
    def deserialize(
        cls,
        value: Any,
        type_hint: type,
        individual_type_hints: list[type] | None = None,
    ) -> Any:
        if type_hint is None or value is None:
            return value

        for collection_transformer in cls._collection_transformers:
            deserialized = collection_transformer.deserialize(value, type_hint, individual_type_hints)
            if deserialized is not None:
                return deserialized

        if cls._should_deserialize(type_hint):
            deserialized_result = cls._default_deserialized_model(value, type_hint)
            for item_key, item_type, item_value in cls._get_enumerator(deserialized_result):
                if is_type_field(item_key):
                    continue

                type_key = get_type_field_name(item_key)
                if type_key in value:
                    item_type = get_reference_from_fqn(cls._get_attribute(value, type_key))

                individual_type_hints = None
                individual_type_hints_key = get_individual_type_field_name(item_key)
                if individual_type_hints_key in value:
                    individual_type_hints = cls._get_attribute(value, individual_type_hints_key)
                    individual_type_hints = [get_reference_from_fqn(hint) for hint in individual_type_hints]

                deserialized = cls.deserialize(item_value, item_type, individual_type_hints)
                cls._set_attribute(deserialized_result, item_key, deserialized)

            deserialized_result = cls._delete_type_keys(deserialized_result)
            return deserialized_result

        for transformer in cls._transformers:
            deserialized = transformer.deserialize(value, type_hint)
            if deserialized is not None:
                return deserialized

        return value

    """
    Private methods
    """

    @classmethod
    def _delete_type_keys(cls, value: dict):
        if isinstance(value, dict):
            keys_to_delete = []
            for key in value.keys():
                if is_type_field(key):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del value[key]

        return value

    @classmethod
    def _get_enumerator(cls, value: dict | BaseModel):
        if isinstance(value, dict):
            for key, item_value in value.items():
                yield key, type(item_value), item_value
        elif isinstance(value, BaseModel):
            for name, field in value.model_fields.items():
                yield name, cls._get_property_type(field), getattr(value, name)

    @classmethod
    def _should_serialize(cls, value: Any) -> bool:
        if isinstance(value, dict) or isinstance(value, BaseModel):
            return True

        return False

    @classmethod
    def _should_deserialize(cls, type_hint: Any) -> bool:
        if is_dict_type(type_hint) or is_pydantic_model(type_hint):
            return True

        return False

    @classmethod
    def _get_property_type(cls, field: FieldInfo) -> Any:
        annotation = field._attributes_set.get("annotation", None)
        if annotation is None:
            return field.annotation

        return annotation

    @classmethod
    def _default_deserialized_model(cls, value, type_hint: Any) -> Any:
        if is_dict_type(type_hint):
            return value
        elif is_pydantic_model(type_hint):
            if type(value) == type_hint:
                return value

            return type_hint.model_construct(**value)

        return value

    @classmethod
    def _get_attribute(cls, value: Any, name: str) -> Any:
        if isinstance(value, BaseModel):
            return getattr(value, name)
        elif isinstance(value, dict):
            return value[name]
        else:
            raise ValueError(f"Invalid value type: {type(value)}")

    @classmethod
    def _set_attribute(cls, model: Any, name: str, value: Any):
        if isinstance(model, BaseModel):
            setattr(model, name, value)
        elif isinstance(model, dict):
            model[name] = value
        else:
            raise ValueError(f"Invalid model type: {type(model)}")
