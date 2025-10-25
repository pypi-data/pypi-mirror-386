from typing import Type, get_type_hints, get_origin, ClassVar
from pydantic.fields import FieldInfo
import sys

def __validate_field_type(obj: Type, key: str, field_type: type):
    """Validate that a field type is strictly `bool`."""
    if field_type is not bool:
        raise TypeError(
            f'Field "{key}" on "{obj.__name__}" Dto should be of type "bool"'
        )

def __validate_default_property_on_field(obj: Type, key: str, annotations):
    """Validate the default value on Pydantic Field(...)."""
    default = None
    field = next((meta for meta in annotations if isinstance(meta, FieldInfo)), None)
    if field is not None:
        default = field.default
    elif key in obj.__dict__:
        value = obj.__dict__[key]
        default = value.default if isinstance(value, FieldInfo) else value

    if default not in (False, None):
        raise TypeError(
            f'Field "{key}" on "{obj.__name__}" Dto should have default=False'
        )

def validate_bool_field(obj: type):
    """Validate that all fields on the DTO are `bool` with default=False."""
    hints = get_type_hints(
        obj,
        include_extras=True,
        globalns=vars(sys.modules[obj.__module__]),
        localns=dict(obj.__dict__),
    )

    for key, field_type in hints.items():
        if key.startswith("_"):
            continue
        if get_origin(field_type) is ClassVar:
            continue

        annotations = ()
        if get_origin(field_type) is not None:
            from typing import Annotated, get_args
            if get_origin(field_type) is Annotated:
                field_type, *annotations = get_args(field_type)

        __validate_field_type(obj, key, field_type)
        __validate_default_property_on_field(obj, key, annotations)

