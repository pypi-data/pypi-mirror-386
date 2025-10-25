"""
Type alias that represents a union between a value of type `T` and the custom
domain sentinel `Null`.

`NullOr[T]` is used throughout the domain to express optional or nullable fields
that can explicitly carry the `Null` marker instead of Python’s `None`. This
distinction allows domain objects and DTOs to represent three states:
    1. **Value present** — the field has a concrete value (`T`);
    2. **Explicitly null** — the field was intentionally set to `Null`;
    3. **Missing** — the field was not provided at all (absent from data).

This pattern improves clarity in domain models, especially for update and query
DTOs where `None` cannot reliably express “no change”.

Example
-------
    from duck_domain.core.types.null import Null
    from duck_domain.core.types.null_or import NullOr
    from duck_domain.core.types.base_dto import BaseDto

    class UserDto(BaseDto):
        name: NullOr[str]
        age: NullOr[int]

    user = UserDto(name=Null)
    assert user.name is Null  # Explicitly null, not None

Notes
-----
- `NullOr` is evaluated at runtime using Python’s union syntax (`|`).
- The `Null` sentinel is automatically serialized as `None` when DTOs are
  converted to JSON.
- This alias works seamlessly with Pydantic’s type system for validation
  and model generation.
"""

from __future__ import annotations

from duck_domain.core.types.null import _TypeNull
from typing import TypeVar

T = TypeVar("T")

type NullOr[T] = T | _TypeNull

