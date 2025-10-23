from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from duck_domain.crud.handdlers.query_response import QueryResponse
from duck_domain.crud.dtos.include_dto import IncludeDto
from duck_domain.crud.dtos.create_dto import CreateDto
from duck_domain.crud.dtos.update_dto import UpdateDto
from duck_domain.crud.dtos.where_dto import WhereDto
from duck_domain.types.base_dto import BaseDto


DTO = TypeVar("DTO", bound=BaseDto)
WHERE = TypeVar("WHERE", bound=WhereDto)
CREATE = TypeVar("CREATE", bound=CreateDto)
UPDATE = TypeVar("UPDATE", bound=UpdateDto)
INCLUDE = TypeVar("INCLUDE", bound=IncludeDto)
RESPONSE = TypeVar("RESPONSE", bound=BaseDto)


class IRepository(ABC, Generic[DTO, WHERE, CREATE, UPDATE, INCLUDE, RESPONSE]):
    """
    Generic repository interface for managing domain entities.

    This interface defines a strongly typed CRUD contract for data persistence,
    enabling consistent data access patterns across different storage
    implementations (e.g., Django ORM, SQLAlchemy, in-memory databases).

    The generic parameters represent the following DTOs:

        - DTO: Base data transfer object representing the entity itself.
        - WHERE: DTO used for filtering and query criteria.
        - CREATE: DTO containing attributes required to create a new entity.
        - UPDATE: DTO defining updatable fields for an existing entity.
        - INCLUDE: DTO specifying which relations or dependencies to preload.
        - RESPONSE: DTO returned from query operations, often enriched with
          relational data.

    Implementations should ensure consistent mapping between DTOs and
    persistence-layer models, while preserving data integrity and soft-delete
    semantics where applicable.
    """

    @abstractmethod
    def create(self, create: CREATE) -> DTO:
        """
        Create a new entity record.

        Args:
            create (CREATE): A DTO containing the data required to create
                a new entity.

        Returns:
            DTO: The newly created entity represented as a DTO.
        """
        ...

    @abstractmethod
    def find(self, where: WHERE, include: Optional[INCLUDE] = None) -> QueryResponse[RESPONSE, WHERE]:
        """
        Retrieve a collection of entities that match the given query criteria.

        Args:
            where (WHERE): A DTO representing the filter or query parameters.
            include (Optional[INCLUDE]): Optional DTO specifying which related
                data or associations should be eagerly loaded.

        Returns:
            QueryResponse[RESPONSE, WHERE]: A structured response containing the
            list of matching entities and metadata about the executed query.
        """
        ...

    @abstractmethod
    def update(self, uuid: str, update: UPDATE) -> DTO:
        """
        Update an existing entity record identified by its unique identifier.

        Args:
            uuid (str): The unique identifier of the entity to be updated.
            update (UPDATE): A DTO specifying which fields should be modified.

        Returns:
            DTO: The updated entity represented as a DTO.
        """
        ...

    @abstractmethod
    def delete(self, uuid: str) -> str:
        """
        Delete (or soft-delete) an entity record by its unique identifier.

        Args:
            uuid (str): The unique identifier of the entity to delete.

        Returns:
            str: The UUID of the deleted entity.
        """
        ...

