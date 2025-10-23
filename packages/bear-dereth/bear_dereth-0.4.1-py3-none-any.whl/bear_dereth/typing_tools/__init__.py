"""A set of type aliases and utility functions for type validation and inspection."""

from collections.abc import Callable
from typing import Any, Literal, NoReturn, TypeGuard

from .builtin_tools import check_for_conflicts
from .from_type import type_to_str
from .infer import infer_inner_type, infer_type, str_to_bool
from .introspection import (
    find_type_hints,
    get_function_signature,
    introspect_types,
    isinstance_in_annotation,
    not_in_bound,
    resolve_string_to_type,
    type_in_annotation,
)
from .to_type import coerce_to_type, mapping_to_type, str_to_type, value_to_type
from .type_helper import TypeHelper, all_same_type, num_type_params, type_param, validate_type
from .utils import ArrayLike, JSONLike, TypeHint, a_or_b, is_array_like, is_json_like, is_mapping, is_object

LitInt = Literal["int"]
LitFloat = Literal["float"]
LitStr = Literal["str"]
LitBool = Literal["bool"]
LitList = Literal["list"]
LitDict = Literal["dict"]
LitTuple = Literal["tuple"]
LitSet = Literal["set"]
LitPath = Literal["path"]
LitBytes = Literal["bytes"]

LitFalse = Literal[False]
LitTrue = Literal[True]

OptInt = int | None
OptFloat = float | None
OptStr = str | None
OptBool = bool | None
OptStrList = list[str] | None
OptStrDict = dict[str, str] | None
NoReturnCall = Callable[..., NoReturn]


def has_exception(e: Exception | None) -> TypeGuard[Exception]:
    """Check if an exception is present.

    Args:
        e: The exception to check
    Returns:
        True if an exception is present, False otherwise
    """
    return e is not None


def format_default_value(value: Any) -> str:
    """Format a default value for string representation in code.

    Args:
        value (Any): The value to format.

    Returns:
        str: The formatted string representation of the value.
    """
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int | float)):
        return str(value)
    return repr(value)


__all__ = [
    "ArrayLike",
    "JSONLike",
    "LitBool",
    "LitBytes",
    "LitDict",
    "LitFalse",
    "LitFloat",
    "LitInt",
    "LitList",
    "LitPath",
    "LitSet",
    "LitStr",
    "LitTrue",
    "LitTuple",
    "NoReturnCall",
    "OptBool",
    "OptFloat",
    "OptInt",
    "OptStr",
    "OptStrDict",
    "OptStrList",
    "TypeHelper",
    "TypeHint",
    "a_or_b",
    "all_same_type",
    "check_for_conflicts",
    "coerce_to_type",
    "find_type_hints",
    "format_default_value",
    "get_function_signature",
    "infer_inner_type",
    "infer_type",
    "introspect_types",
    "is_array_like",
    "is_json_like",
    "is_mapping",
    "is_object",
    "isinstance_in_annotation",
    "mapping_to_type",
    "not_in_bound",
    "num_type_params",
    "resolve_string_to_type",
    "str_to_bool",
    "str_to_type",
    "type_in_annotation",
    "type_param",
    "type_to_str",
    "validate_type",
    "value_to_type",
]
