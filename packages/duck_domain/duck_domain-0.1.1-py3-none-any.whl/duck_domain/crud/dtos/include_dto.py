from duck_domain.crud.dtos.validators import validate_null_or_field
from duck_domain.types.base_dto import BaseDto

class IncludeDto(BaseDto):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if cls is IncludeDto:
            return

        validate_null_or_field(cls, bool)
