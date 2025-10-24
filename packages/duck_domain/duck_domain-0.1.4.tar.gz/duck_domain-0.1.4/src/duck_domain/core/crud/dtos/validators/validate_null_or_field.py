from __future__ import annotations

from typing import Annotated, Any, ClassVar, Sequence, Tuple, Type, get_args, get_origin, get_type_hints
from duck_domain.core.types.null_or import NullOr
from duck_domain.core.types.null import Null
from pydantic.fields import FieldInfo
import sys

"""
Utility validators for DTO (Data Transfer Object) field definitions.

This module enforces strict typing and default-value conventions for Pydantic
models used as domain DTOs in the `duck_domain` ecosystem. It validates that
DTO fields follow the expected `NullOr[T]` pattern, ensuring consistency across
`WhereDto`, `UpdateDto`, and `IncludeDto` classes.

Functions
---------
validate_null_or_field(obj: type, *null_or_expected_args)
    Validates that all fields in a DTO subclass use `NullOr` types and have
    a default value of `Null`.

__validate_field_type(obj: Type, key: str, field_type: Any, null_or_expected_args: Tuple)
    Internal helper that ensures the declared type of a field is compatible
    with `NullOr[T]` and matches any expected type arguments.

__validate_default_property_on_field(obj: Type, key: str, annotations: Sequence[Any])
    Internal helper that checks whether a field’s default value is correctly
    set to `Null` when using `pydantic.Field`.
"""


def __validate_field_type(obj: Type, key: str, field_type: Any, null_or_expected_args: Tuple):
    """
    Validate that a field type conforms to the `NullOr[T]` structure.

    Parameters
    ----------
    obj : Type
        The DTO class being validated.
    key : str
        The field name.
    field_type : Any
        The declared type annotation for the field.
    null_or_expected_args : Tuple
        Optional tuple of specific inner types that are expected within `NullOr`.

    Raises
    ------
    TypeError
        If the field is not typed as `NullOr[T]` or does not match the expected
        inner types.
    """
    is_processable_null_or = get_origin(field_type) is NullOr and get_args(field_type)
    if not is_processable_null_or:
        raise TypeError(f'Field "{key}" on "{obj.__name__}" Dto should be "NullOr[T]" (T | Null)')

    is_missing_expected_args = len(null_or_expected_args) > 0 and null_or_expected_args != get_args(field_type)
    if is_missing_expected_args:
        should_args = ", ".join([arg.__name__ for arg in null_or_expected_args])
        raise TypeError(f'Field "{key}" on "{obj.__name__}" Dto should be "NullOr[{should_args}]"')


def __validate_default_property_on_field(obj: Type, key: str, annotations: Sequence[Any]):
    """
    Validate that a field’s default value is explicitly set to `Null`.

    Parameters
    ----------
    obj : Type
        The DTO class being validated.
    key : str
        The field name.
    annotations : Sequence[Any]
        The annotations or metadata attached to the field (e.g., `Annotated`,
        `Field(...)` from Pydantic).

    Raises
    ------
    TypeError
        If the field does not have a default value of `Null`.
    """
    default = None
    field = next((field_meta for field_meta in annotations if isinstance(field_meta, FieldInfo)), None)
    if field is not None:
        default = field.default
    else:
        if key in obj.__dict__:
            value = obj.__dict__[key]
            default = value.default if isinstance(value, FieldInfo) else value

    if default is not Null:
        raise TypeError(f'Field "{key}" on "{obj.__name__}" Dto should be "Field(default=Null, ...)"')


def validate_null_or_field(obj: type, *null_or_expected_args):
    """
    Validate all fields in a DTO class to ensure proper `NullOr` usage.

    This function performs two key validations:
      1. Each field must be typed as `NullOr[T]` (e.g., `NullOr[str]`).
      2. Each field must have a default value of `Null` (`Field(default=Null)`).

    It is automatically executed when DTO subclasses like `WhereDto`,
    `UpdateDto`, or `IncludeDto` are defined.

    Parameters
    ----------
    obj : type
        The DTO subclass being validated.
    *null_or_expected_args : Any
        Optional tuple specifying which type(s) are permitted inside `NullOr`.

    Raises
    ------
    TypeError
        If any field is incorrectly typed or does not have `Null` as its default
        value.
    """
    hints = get_type_hints(
        obj,
        include_extras=True,
        globalns=vars(sys.modules[obj.__module__]),
        localns=dict(obj.__dict__),
    )

    for key, field_type in hints.items():
        if key.startswith('_'):
            continue

        if get_origin(field_type) is ClassVar:
            continue
 
        annotations = ()
        if get_origin(field_type) is Annotated:
            field_type, *annotations = get_args(field_type)

        __validate_field_type(obj, key, field_type, null_or_expected_args)
        __validate_default_property_on_field(obj, key, annotations)

