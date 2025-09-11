import json

from pydantic import BaseModel
from pydantic import ValidationError

class AutosRequestDto(BaseModel):
    uuid:str
    fecha:str
    radicado:str
    consecutivo:int
    

    @classmethod
    def fromRaw(cls, rawBody: str):
        try:
            data = json.loads(rawBody)
            return cls(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid scrapper request data: {e}")

