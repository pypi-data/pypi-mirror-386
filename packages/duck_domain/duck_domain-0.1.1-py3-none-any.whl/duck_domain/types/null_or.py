from __future__ import annotations
from typing import TypeVar
from duck_domain.types.null import _TypeNull

T = TypeVar("T")

type NullOr[T] = T | _TypeNull
