from duck_domain.core.crud.dtos.validators import validate_null_or_field
from duck_domain.core.types.base_dto import BaseDto

class IncludeDto(BaseDto):
    """
    Base Data Transfer Object (DTO) used to define which related entities
    should be included when fetching data from a repository or query layer.

    This class serves as a base for DTOs that describe `include` parameters
    (e.g., when specifying whether to include foreign-key or nested relations).
    It ensures that all subclass fields are validated as `NullOr[bool]` fields
    using the `validate_null_or_field` function.

    Subclasses must define their own boolean fields indicating which relations
    should be included in a query. For example:

        class ResearchIncludeDto(IncludeDto):
            author: NullOr[bool]
            questions: NullOr[bool]

    In this example, `author` and `questions` indicate whether related entities
    should be included when the research entity is queried.

    Notes
    -----
    - This class automatically validates subclass fields during definition,
      ensuring that every attribute is compatible with `bool` or `NullOr[bool]`.
    - The validation is executed in the `__init_subclass__` hook, so any
      subclass inheriting from `IncludeDto` is checked at import time.

    Raises
    ------
    TypeError
        If any subclass field is not compatible with `bool` or `NullOr[bool]`.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls is IncludeDto:
            return

        validate_null_or_field(cls, bool)
