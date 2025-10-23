from typing import Dict, Generic, List, Optional, Type, TypeVar, cast

from duck_domain.crud.handdlers.query_response import QueryResponse
from duck_domain.crud.repositories.django.soft_delete.soft_delete_model import SoftDeleteModel
from duck_domain.errors.handdlers.app_error import AppError

from duck_domain.crud.dtos.include_dto import IncludeDto
from duck_domain.crud.dtos.create_dto import CreateDto
from duck_domain.crud.dtos.update_dto import UpdateDto
from duck_domain.crud.dtos.where_dto import WhereDto
from duck_domain.types.base_dto import BaseDto

from duck_domain.typing.crud.i_repository import IRepository
from duck_domain.types.null import Null
from functools import cached_property

MODEL = TypeVar("MODEL", bound=SoftDeleteModel)
DTO = TypeVar("DTO", bound=BaseDto)
WHERE = TypeVar("WHERE", bound=WhereDto)
CREATE = TypeVar("CREATE", bound=CreateDto)
UPDATE = TypeVar("UPDATE", bound=UpdateDto)
INCLUDE = TypeVar("INCLUDE", bound=IncludeDto)
RESPONSE = TypeVar("RESPONSE", bound=BaseDto)

class SoftDeleteDjangoRepository(
    IRepository,
    Generic[MODEL, DTO, WHERE, CREATE, UPDATE, INCLUDE, RESPONSE],
):
    """
    A generic Django repository implementation that supports soft-delete semantics
    and integrates with Pydantic DTOs for type-safe data mapping.

    This class provides a reusable data-access layer for Django models that inherit
    from `SoftDeleteModel`, automatically handling conversions between ORM entities
    and Pydantic-based DTOs (`BaseDto`). It supports standard CRUD operations and
    prefetch-based relation loading.

    Type Parameters:
        MODEL (SoftDeleteModel): The Django model class managed by this repository.
        DTO (BaseDto): The main data transfer object (domain-level representation).
        WHERE (WhereDto): DTO defining filtering criteria for queries.
        CREATE (CreateDto): DTO used for creating new records.
        UPDATE (UpdateDto): DTO used for updating existing records.
        INCLUDE (IncludeDto): DTO specifying related entities to prefetch.
        RESPONSE (BaseDto): DTO returned in query responses.

    Attributes:
        response (Type[RESPONSE]): Class of the DTO returned in query responses.
        include (Type[INCLUDE]): Class of the DTO specifying relations to include.
        model (Type[SoftDeleteModel]): The Django model managed by the repository.
        dto (Type[DTO]): Class of the DTO representing the entity.
        where_field_to_filter (Dict[str, str]): Mapping between field names in the
            `WHERE` DTO and Django ORM filter expressions.
        include_field_to_relation (Dict[str, str]): Mapping between fields in the
            `INCLUDE` DTO and Django ORM relation names.
    """

    response: Type[RESPONSE]
    include: Type[INCLUDE]
    model: Type[SoftDeleteModel]
    dto: Type[DTO]

    where_field_to_filter: Dict[str, str] = {}
    include_field_to_relation: Dict[str, str] = {}

    @cached_property
    def _model_fields(self) -> List[str]:
        """
        Cached list of model field names for fast access and filtering.

        Returns:
            List[str]: A list of field names defined in the Django model.
        """
        return [f.name for f in self.model._meta.fields]

    def _as_django_relation(self, relation: str) -> str:
        """
        Convert an `INCLUDE` DTO field name into its Django ORM relation name.

        Args:
            relation (str): Field name from the `INCLUDE` DTO.

        Returns:
            str: Django ORM-compatible relation name.
        """
        if relation in self.include_field_to_relation.keys():
            return self.include_field_to_relation[relation]
        return relation 

    def _as_django_filter(self, field: str) -> str:
        """
        Convert a `WHERE` DTO field name into a Django ORM filter key.

        Args:
            field (str): Field name from the `WHERE` DTO.

        Returns:
            str: Django ORM-compatible filter string.
        """
        if field in self.where_field_to_filter.keys():
            return self.where_field_to_filter[field]
        return field

    def create(self, create: CREATE) -> DTO:
        """
        Create a new record in the database from the given `CREATE` DTO.

        Args:
            create (CREATE): DTO containing field values for the new record.

        Returns:
            DTO: A Pydantic DTO representing the newly created entity.
        """
        created = self.model.objects.create(**create.model_dump())
        return cast(DTO, created.as_dto())

    def find(
        self, where: WHERE, include: Optional[INCLUDE] = None
    ) -> QueryResponse[RESPONSE, WHERE]:
        """
        Query the database for records matching the provided `WHERE` filters.
        Supports optional eager loading of related entities defined in the
        `INCLUDE` DTO.

        Args:
            where (WHERE): DTO defining filter conditions for the query.
            include (Optional[INCLUDE]): DTO specifying related entities or
                foreign keys to prefetch.

        Returns:
            QueryResponse[RESPONSE, WHERE]: A structured query result containing
            matching records and query metadata.
        """
        relations = (
            list(include.model_dump(exclude_defaults=True).keys())
            if include
            else []
        )
        relations = {self._as_django_relation(relation): relation for relation in relations}

        filters = {
            self._as_django_filter(field): value
            for field, value in where.model_dump().items()
            if value is not Null and (
                field in self._model_fields
                or field in self.where_field_to_filter.keys()
                or (field.endswith("_id") and field.replace("_id", "") in self._model_fields)
            )
        }

        prefetches = self.model.build_prefetches(list(relations.keys()))
        queryset = self.model.objects.filter(
            **filters
        ).prefetch_related(*prefetches).distinct()

        result = []
        for model in queryset:
            item = model.as_dto(True).model_dump()

            for rel in relations.values():
                related_field = getattr(model, rel)

                if hasattr(related_field, "all"):
                    related = related_field.all()
                    item[rel] = [r.as_dto() for r in related]
                elif related_field is not None:
                    item[rel] = related_field.as_dto()
                else:
                    item[rel] = None
            
            result.append(self.response(**item))
        
        return QueryResponse(result, self.model._meta.db_table, where)

    def update(self, id: str, update: UPDATE) -> DTO:
        """
        Update an existing record identified by its UUID using data from the
        provided `UPDATE` DTO. Fields set to `Null` are ignored.

        Args:
            id (str): The unique identifier (UUID) of the record to update.
            update (UPDATE): DTO specifying the new field values.

        Returns:
            DTO: A Pydantic DTO representing the updated entity.

        Raises:
            AppError: If no record is found with the provided UUID.
        """
        instance = self.model.objects.filter(id=id).first()
        if instance is None:
            self.__error(self, id)

        for field, value in update.model_dump(exclude_defaults=True).items():
            if value is Null:
                continue

            if hasattr(instance, field):
                setattr(instance, field, value)

            elif field.endswith("_id"):
                fk_field = field.removesuffix("_id")
                if hasattr(instance, fk_field):
                    setattr(instance, f"{fk_field}_id", value)

        instance.save()
        return cast(DTO, instance.as_dto())

    def delete(self, id: str) -> str:
        """
        Perform a soft-delete operation on the record identified by its UUID.
        The record remains in the database but is excluded from normal queries.

        Args:
            id (str): The unique identifier (UUID) of the record to soft-delete.

        Returns:
            str: The UUID of the deleted record.

        Raises:
            AppError: If the record does not exist.
        """
        data = self.model.objects.filter(id=id).first()

        if data is None:
            self.__error(self, id)

        data.soft_delete()
        return id

    def __error(self, cls: object, id: str):
        """
        Raise a standardized application error when a record is not found.

        Args:
            cls (object): The class or context in which the error occurred.
            id (str): The UUID of the missing record.

        Raises:
            AppError: With message "Not Found Error" and a 404 HTTP code.
        """
        raise AppError(
            cls,
            "Not Found Error",
            f"{self.model._meta.db_table} row not found",
            {"id": id},
            code=404,
        )

