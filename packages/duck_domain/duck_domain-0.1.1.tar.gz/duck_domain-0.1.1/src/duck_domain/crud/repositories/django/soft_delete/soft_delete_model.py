from duck_django_soft_delete.table.soft_delete_table import SoftDeleteTable
from duck_domain.types.base_dto import BaseDto
from abc import abstractmethod
from django.db import models
from uuid import uuid4


class SoftDeleteModel(SoftDeleteTable):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    @abstractmethod
    def as_dto(
        self, include_fks: bool = False, show_deleted: bool = False
    ) -> BaseDto:
        """
        Serialize Django database model into Pydantic BaseModel
        """
        raise NotImplementedError(
            "Subclasses must implement `as_dto` returning a BaseModel"
        )
