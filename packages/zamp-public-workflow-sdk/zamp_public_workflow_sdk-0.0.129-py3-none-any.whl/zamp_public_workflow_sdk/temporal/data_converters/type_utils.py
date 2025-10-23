import io
import typing
from types import UnionType
from typing import Any

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from temporalio import workflow


def get_fqn(cls: type) -> str:
    if cls == type(None) or cls is None:
        return "None"

    if cls.__module__ == "builtins":
        cls_name = cls.__name__
    elif hasattr(cls, "__name__"):
        cls_name = f"{cls.__module__}.{cls.__name__}"
    else:
        cls_name = f"{cls.__module__}.{cls.__class__.__name__}"

    # Check args
    if hasattr(cls, "__args__"):
        args = cls.__args__
        if len(args) > 0:
            return f"{cls_name}[{', '.join([get_fqn(arg) for arg in args])}]"

    # Check bound
    if hasattr(cls, "__bound__"):
        bound = cls.__bound__
        if bound is not None:
            return f"{cls_name}[{get_fqn(bound)}]"

    return cls_name


def get_class_from_fqn(fqn: str) -> type:
    # TODO (Giri): Figure out why this is needed.
    with workflow.unsafe.imports_passed_through():
        if "." in fqn:
            module_name, class_name = fqn.rsplit(".", 1)
        else:
            module_name, class_name = "builtins", fqn

        # Import the module and get the class
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)


def get_split_args(args: str) -> list[str]:
    splits = []
    old_split_index = 0
    split = True
    for i, char in enumerate(args):
        if args[i] == "[":
            split = False
        elif args[i] == "]":
            split = True
        elif args[i] == "," and split:
            splits.append(args[old_split_index:i])
            old_split_index = i + 1

    splits.append(args[old_split_index:])
    return splits


def get_reference_from_fqn(fqn: str) -> type:
    try:
        # Check for None type
        if fqn == "None":
            return None

        # Handle basic types like int, str, etc.
        if fqn in {"int", "str", "bool", "float", "None"}:
            return eval(fqn)

        # Split the FQN by the brackets to detect generics
        if "[" in fqn and "]" in fqn:
            # Get the class from the module
            cls_name = fqn.split("[")[0].replace("[", "").replace("]`", "")
            cls = get_class_from_fqn(cls_name)

            # Do not split if it's a dict[int, int] where there is a comma between [ ]
            args = fqn[fqn.index("[") + 1 : fqn.rindex("]")]
            args_types = [get_reference_from_fqn(arg.strip()) for arg in get_split_args(args)]

            if hasattr(cls, "__origin__"):
                return cls.__origin__[tuple(args_types)]

            return typing.GenericAlias(cls, tuple(args_types))

        return get_class_from_fqn(fqn)
    except Exception as e:
        print(f"Error getting reference from FQN {fqn}: {e}")
        raise e


def get_inner_type(type_hint: type) -> type:
    if hasattr(type_hint, "__args__"):
        return type_hint.__args__[0]

    return type


def get_type_field_name(field_name: str) -> str:
    return "__" + field_name + "_type"


def get_individual_type_field_name(field_name: str) -> str:
    return "__" + field_name + "_individual_type"


def is_type_field(field_name: str) -> bool:
    return (field_name.startswith("__") and field_name.endswith("_type")) or (
        field_name.startswith("__") and field_name.endswith("_individual_type")
    )


def safe_issubclass(obj, cls):
    if isinstance(obj, type):
        return issubclass(obj, cls)
    return False


def is_dict_type(type_hint: Any) -> bool:
    return type_hint is dict or getattr(type_hint, "__origin__", None) is dict


def is_pydantic_model(type_hint: Any) -> bool:
    return safe_issubclass(type_hint, BaseModel)


def is_union_type(type_hint) -> bool:
    if getattr(type_hint, "__origin__", None) is typing.Union or getattr(type_hint, "__class__", None) is typing.Union:
        return True

    if getattr(type_hint, "__origin__", None) is UnionType or getattr(type_hint, "__class__", None) is UnionType:
        return True


def is_list_non_serializable_type(type_hint) -> bool:
    if type_hint is list or getattr(type_hint, "__origin__", None) is list:
        if not hasattr(type_hint, "__args__"):
            return True

        args = getattr(type_hint, "__args__", None)
        return not is_field_annotation_serializable(args[0])

    return False


def is_field_annotation_serializable(type_hint) -> bool:
    if type_hint is typing.Generic:
        return False

    if getattr(type_hint, "__class__", None) is typing.TypeVar:
        return False

    if type_hint is type:
        return False

    if type_hint is BaseModel:
        return False

    if type_hint is tuple:
        return False

    if is_list_non_serializable_type(type_hint):
        return False

    if is_union_type(type_hint):
        args = getattr(type_hint, "__args__")
        for arg in args:
            if not is_field_annotation_serializable(arg):
                return False

    return True


def should_serialize(value: Any) -> bool:
    if isinstance(value, dict) or isinstance(value, BaseModel):
        return True

    return False


def get_property_type(field) -> Any:
    annotation = field._attributes_set.get("annotation", None)
    if annotation is None:
        return field.annotation

    return annotation


def get_enumerator(value: dict | BaseModel):
    if isinstance(value, dict):
        for key, item_value in value.items():
            yield key, type(item_value), item_value
    elif isinstance(value, BaseModel):
        for name, field in value.model_fields.items():
            yield name, get_property_type(field), getattr(value, name)


def is_serialize_by_default_serializer(value: Any) -> bool:
    if should_serialize(value):
        for _, annotation, property_value in get_enumerator(value):
            if not is_field_annotation_serializable(annotation):
                return False

            if isinstance(property_value, io.BytesIO):
                return False

            if isinstance(property_value, ModelMetaclass):
                return False

            if not is_serialize_by_default_serializer(property_value):
                return False

    return True
