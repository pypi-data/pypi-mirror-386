from duck_domain.core.crud.dtos.validators import validate_null_or_field
from duck_domain.core.types.base_dto import BaseDto

class WhereDto(BaseDto):
    """
    Base Data Transfer Object (DTO) for defining filtering and query conditions
    used in repository or data access operations.

    This class is designed to express "where" clauses in a type-safe,
    declarative way. It ensures that all subclass fields are compatible with
    `NullOr` types, allowing flexible filtering (e.g., optional or ignored
    conditions when the value is `Null`).

    The `validate_null_or_field` validator is automatically applied during
    subclass creation, ensuring that all fields follow the expected `NullOr`
    typing convention for query parameters.

    Example
    -------
        class ResearchWhereDto(WhereDto):
            title: NullOr[str]
            author_id: NullOr[UUID]

        # Example usage:
        filters = ResearchWhereDto(title="AI Research")
        # Generates query conditions equivalent to WHERE title = 'AI Research'

    Notes
    -----
    - Fields typed as `NullOr[T]` can represent both an active condition (`T`)
      or an ignored one (`Null`), enabling dynamic query composition.
    - Validation runs at class definition time to guarantee that each field
      supports nullable semantics.
    - `WhereDto` is typically consumed by repository implementations to build
      ORM or SQL-level query filters dynamically.

    Raises
    ------
    TypeError
        If any subclass field does not use a `NullOr` type.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls is WhereDto:
            return

        validate_null_or_field(cls)

