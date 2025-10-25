from typing import Any, Callable, Generic, Iterator, List, Optional, TypeVar, Union
from duck_domain.core.errors.handdlers.app_error import AppError
from duck_domain.core.crud.dtos.where_dto import WhereDto
from duck_domain.core.handdlers.async_handler import AsyncHandler
from duck_domain.core.types.base_dto import BaseDto


RESPONSE = TypeVar("RESPONSE")
WHERE = TypeVar("WHERE", bound=WhereDto)
R = TypeVar("R")

class QueryResponse(Generic[RESPONSE, WHERE]):
    """
    A generic and iterable wrapper for repository `find` operations.

    This class encapsulates:
    - The list of DTOs returned by the repository
    - Metadata such as the originating model name and filter DTO

    It supports iteration, indexing, and safe-access helpers such as:
    - `first_or_error()` → returns the first element or an `AppError(404)`
    - `empty_or_error()` → ensures no duplicates before creation operations
    """

    def __init__(
        self,
        query_response: List[RESPONSE],
        object_name: str,
        where: WHERE,
    ) -> None:
        """
        Initialize a new QueryResponse instance.

        Parameters
        ----------
        query_response : List[RESPONSE]
            The list of DTO instances returned by the query.
        object_name : str
            The name of the domain entity related to this query.
        where : WHERE
            The DTO describing the filtering criteria used in the query.
        """
        self.query_response = query_response
        self.object_name = object_name
        self.where = where

    @property
    def all(self) -> List[RESPONSE]:
        """Return all DTOs from the query result."""
        return self.query_response

    @property
    def first(self) -> Optional[RESPONSE]:
        """Return the first DTO if available, else None."""
        return self.query_response[0] if self.query_response else None

    def first_or_error(self, class_pointer: Any = None) -> Union[RESPONSE, AppError]:
        """Return the first DTO or an AppError(404) if the result set is empty."""
        if not self.query_response:
            return self._could_not_find_error(class_pointer)
        return self.query_response[0]

    def empty_or_error(self, class_pointer: Any = None) -> Optional[AppError]:
        """Return an AppError(409) if any records exist, otherwise None."""
        if self.query_response:
            return self._already_exists_error(class_pointer)
        return None

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the query response into a dictionary.

        Returns
        -------
        dict[str, Any]
            {
                "data": [...],
                "filters": {...}
            }
        """

        return {
            "data": [dto.model_dump() if isinstance(dto, BaseDto) else format(dto) for dto in self.query_response],
            "count": len(self.query_response),
            "filters": self.where.model_dump(),
        }
    
    def parallel_map(
        self,
        func: Callable[[List[RESPONSE]], List[R]] | Any,
        divisions: int = 4,
        class_pointer: Any = None,
    ) -> "QueryResponse[R, WHERE] | AppError":
        """
        Process the query results concurrently using a thread pool.

        Parameters
        ----------
        func : Callable[[List[RESPONSE]], List[R]]
            Function to apply to each data chunk. Must return a list of results.
        divisions : int, optional
            Number of worker threads to use. Default is 4.
        class_pointer : Any, optional
            Context object for error attribution.

        Returns
        -------
        List[R] | AppError
            - A flattened list containing all processed results.
            - An `AppError` if the function is invalid or a thread fails.
        """
        response = AsyncHandler(
            self.query_response, self.object_name
        ).parallel_map(func, divisions=divisions, class_pointer=class_pointer)

        if isinstance(response, AppError):
            return response
        
        return QueryResponse(response, self.object_name, self.where)

    # -------------------------------------------------------------------------
    # Error builders
    # -------------------------------------------------------------------------

    def _could_not_find_error(self, class_pointer: Any = None) -> AppError:
        """Return a standardized 404 error."""
        return AppError(
            class_pointer=class_pointer or self,
            title=f"{self.object_name} not found",
            message=f"No {self.object_name} matched the provided filters.",
            details={
                "object_name": self.object_name,
                "filters": self.where.model_dump(),
                "results_found": len(self.query_response),
            },
            code=404,
        )

    def _already_exists_error(self, class_pointer: Any = None) -> AppError:
        """Return a standardized 409 error."""
        return AppError(
            class_pointer=class_pointer or self,
            title=f"{self.object_name} already exists",
            message=f"A {self.object_name} matching the given filters already exists.",
            details={
                "object_name": self.object_name,
                "filters": self.where.model_dump(),
                "results_found": len(self.query_response),
            },
            code=409,
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of elements in the current response."""
        return len(self.query_response)

    def __iter__(self) -> Iterator[RESPONSE]:
        """Allow iteration over the DTO list."""
        return iter(self.query_response)

    def __getitem__(self, index: int) -> RESPONSE:
        """Allow indexed access to results."""
        return self.query_response[index]

    def __bool__(self) -> bool:
        """Return True if the response contains at least one record."""
        return bool(self.query_response)

    def __repr__(self) -> str:
        """Developer-friendly representation for debugging."""
        count = len(self.query_response)
        return f"<QueryResponse {self.object_name} ({count} results)>"

