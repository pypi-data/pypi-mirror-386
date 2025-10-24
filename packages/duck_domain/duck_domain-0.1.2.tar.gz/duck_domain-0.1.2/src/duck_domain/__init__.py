from duck_domain.core.crud.handdlers.query_response import QueryResponse
from duck_domain.core.errors.handdlers.app_error import AppError
from duck_domain.core.crud.i_repository import IRepository

from duck_domain.core.crud.dtos.include_dto import IncludeDto
from duck_domain.core.crud.dtos.create_dto import CreateDto
from duck_domain.core.crud.dtos.update_dto import UpdateDto
from duck_domain.core.crud.dtos.where_dto import WhereDto

from duck_domain.core.types.request_dto import RequestDto
from duck_domain.core.types.base_dto import BaseDto
from duck_domain.core.types.null_or import NullOr
from duck_domain.core.types.null import Null

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from duck_domain.django_tools import SoftDeleteDjangoRepository, SoftDeleteModel

__all__ = [
    "QueryResponse",
    "IRepository",
    "AppError",
    "IncludeDto",
    "CreateDto",
    "UpdateDto",
    "WhereDto",
    "RequestDto",
    "BaseDto",
    "NullOr",
    "Null",

    "SoftDeleteDjangoRepository",
    "SoftDeleteModel",
]

def __getattr__(name: str):
    if name in ("SoftDeleteDjangoRepository", "SoftDeleteModel"):
        from duck_domain.django_tools import (
            SoftDeleteDjangoRepository,
            SoftDeleteModel,
        )
        globals()[name] = locals()[name]
        return locals()[name]
    raise AttributeError(f"module 'duck_domain' has no attribute '{name}'")
