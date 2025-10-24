from pydantic import BaseModel, ConfigDict, field_serializer
from duck_domain.core.types.null import Null

class BaseDto(BaseModel):
    """
    Base class for all domain Data Transfer Objects (DTOs).

    This class extends Pydantic's `BaseModel` to provide consistent behavior
    across all DTOs within the domain layer. It introduces custom serialization
    rules and relaxed type constraints to support domain-specific abstractions
    such as `Null` and `NullOr[T]`.

    Features
    --------
    - Allows arbitrary types (`arbitrary_types_allowed=True`) to support custom
      domain classes and framework-specific objects.
    - Automatically serializes the custom `Null` sentinel to `None` when
      converting models to JSON, ensuring compatibility with API responses and
      persistence layers.
    - Acts as the shared parent for specialized DTOs such as:
        * `CreateDto` – defines creation payloads.
        * `UpdateDto` – defines partial updates.
        * `WhereDto` – defines query filters.
        * `IncludeDto` – defines inclusion of related entities.

    Example
    -------
        from duck_domain.core.types.null import Null
        from duck_domain.core.types.null_or import NullOr

        class UserDto(BaseDto):
            id: int
            name: NullOr[str] = Null

        user = UserDto(id=1)
        print(user.model_dump_json())  # {"id": 1, "name": null}

    Notes
    -----
    - The `@field_serializer` hook ensures that the internal domain sentinel
      `Null` is transparently converted to `null` (JSON-compatible) during
      serialization.
    - Subclasses should be pure data structures — no business logic should be
      embedded in DTOs.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('*', when_used='json')
    def _serialize_typenull(self, v, _):
        if v is Null:
            return None
        return v

