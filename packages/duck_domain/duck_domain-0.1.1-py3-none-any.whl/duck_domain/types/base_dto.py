from pydantic import BaseModel, ConfigDict, field_serializer
from duck_domain.types.null import Null

class BaseDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('*', when_used='json')
    def _serialize_typenull(self, v, _):
        if v is Null:
            return None
        return v
