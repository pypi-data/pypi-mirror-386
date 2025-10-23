from __future__ import annotations
from typing import Annotated, Any, ClassVar, Sequence, Tuple, Type, get_args, get_origin, get_type_hints
import sys
from pydantic.fields import FieldInfo

from duck_domain.types.null import Null
from duck_domain.types.null_or import NullOr

def __validate_field_type(obj: Type, key: str, field_type: Any, null_or_expected_args: Tuple):
    '''Validate all the fields types on the "Dto" pydantic \"BaseModel\"'''
        
    is_processable_null_or = get_origin(field_type) is NullOr and get_args(field_type)
    if not is_processable_null_or:
        raise TypeError(f"Field \"{key}\" on \"{obj.__name__}\" Dto should be \"NullOr[T]\" (T | TypeNull)")
        
    is_missing_expected_args = len(null_or_expected_args) > 0 and null_or_expected_args != get_args(field_type)
    if is_missing_expected_args:
        should_args = ", ".join([arg.__name__ for arg in null_or_expected_args])
        raise TypeError(f"Field \"{key}\" on \"{obj.__name__}\" Dto should be \"NullOr[{should_args}]\"")


def __validate_default_property_on_field(obj: Type, key: str, annotations: Sequence[Any]):
    '''Validate the value of the "default" atribute on pydantic \"Field(...)\"'''
    default = None
    field = next((field_meta for field_meta in annotations if isinstance(field_meta, FieldInfo)), None)
    if field is not None:
        default = field.default

    else:
        if key in obj.__dict__:
            value = obj.__dict__[key]
            default = (
                value.default 
                if isinstance(value, FieldInfo) 
                else value
            )

    if default is not Null:
        raise TypeError(f"Field \"{key}\" on \"{obj.__name__}\" Dto should be \"Field(default=TypeNull, ...)\"")

def validate_null_or_field(obj: type, *null_or_expected_args):
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



