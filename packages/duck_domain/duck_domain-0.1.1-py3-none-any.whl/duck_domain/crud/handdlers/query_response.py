from typing import Any, Generic, List, Optional, TypeVar, Union
from duck_domain.errors.handdlers.app_error import AppError
from duck_domain.crud.dtos.where_dto import WhereDto
from pydantic import BaseModel


RESPONSE = TypeVar("RESPONSE", bound=BaseModel)
WHERE = TypeVar("WHERE", bound=WhereDto)

class QueryResponse(Generic[RESPONSE, WHERE]):
    """
    A generic response wrapper for query operations, encapsulating a list of
    result objects along with query metadata such as the originating model
    name and the applied filtering criteria.

    This class provides convenience methods for accessing results, retrieving
    the first element safely, and generating domain-friendly errors when
    no matching records are found.

    Type Parameters:
        RESPONSE: A Pydantic model representing the DTO returned by the query.
        WHERE: A Pydantic DTO subclass (derived from `WhereDto`) that defines
               the filters used in the query.
    """

    def __init__(
        self,
        query_response: List[RESPONSE],
        object_name: str,
        where: WHERE
    ) -> None:
        """
        Initialize a new `QueryResponse` instance.

        Args:
            query_response (List[RESPONSE]):
                The list of DTO instances returned by the query operation.
            object_name (str):
                The name of the domain object or model associated with this response.
            where (WHERE):
                The filtering DTO used to generate the query.
        """
        self.query_response = query_response
        self.object_name = object_name
        self.where = where

    @property
    def all(self) -> List[RESPONSE]:
        """
        Retrieve all elements from the query response.

        Returns:
            List[RESPONSE]: A list of all DTO instances retrieved by the query.
        """
        return self.query_response

    @property
    def first(self) -> Optional[RESPONSE]:
        """
        Retrieve the first element of the query response, if available.

        Returns:
            Optional[RESPONSE]: The first DTO in the result list, or `None`
            if the response is empty.
        """
        if len(self) == 0:
            return None
        return self.query_response[0]

    def first_or_error(self, class_pointer: Any = None) -> Union[RESPONSE, AppError]:
        """
        Retrieve the first element of the query response, or return an error
        if no records were found.

        Args:
            class_pointer (Any, optional):
                The class or context from which this method is called, used for
                error attribution. Defaults to `None`.

        Returns:
            Union[RESPONSE, AppError]:
                - The first DTO from the query result, if available.
                - An `AppError` instance describing the "not found" condition
                  if the query returned no results.
        """
        if len(self) == 0:
            return self.could_not_find_error(class_pointer)
        return self.query_response[0]

    def could_not_find_error(self, class_pointer: Any = None) -> AppError:
        """
        Construct a standardized `AppError` indicating that no matching records
        were found for the given query filters.

        Args:
            class_pointer (Any, optional):
                The class or component responsible for the query, used to
                annotate the error context. Defaults to `self`.

        Returns:
            AppError: A structured error object containing details about
            the missing entity, applied filters, and result count.
        """
        return AppError(
            class_pointer=class_pointer if class_pointer is not None else self,
            title="Not Found",
            message=f"Could not find any {self.object_name} matching the given filters.",
            details={
                "object_name": self.object_name,
                "where": self.where.model_dump_json(),
                "query_response_count": len(self.query_response),
            },
            code=404,
        )

    def __len__(self) -> int:
        """
        Return the total number of elements in the query response.

        Returns:
            int: The count of DTOs in the current query result.
        """
        return len(self.query_response)

