from duck_domain.core.crud.dtos.validators.validate_bool_field import validate_bool_field
from duck_domain.core.types.base_dto import BaseDto

class IncludeDto(BaseDto):
    """
    Base Data Transfer Object (DTO) used to define which related entities
    should be included when fetching data from a repository or query layer.

    This class validates that all subclass fields are strictly boolean,
    ensuring that only True/False flags are defined to control which relations
    are included in a query.

    Example
    -------
        class ResearchIncludeDto(IncludeDto):
            author: bool = False
            questions: bool = False

    Notes
    -----
    - Each field must be typed as `bool` and default to `False`.
    - The validation is executed automatically at import time.
    - Attempting to define a field of another type will raise `TypeError`.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls is IncludeDto:
            return

        validate_bool_field(cls)

