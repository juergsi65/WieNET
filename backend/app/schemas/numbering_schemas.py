import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.numbering import validate_pattern


class NummernschemaCreate(BaseModel):
    entity_type: str
    name: str
    pattern: str
    scope: str = "global"
    start_value: int = 1

    @field_validator("pattern")
    @classmethod
    def check_pattern(cls, v: str, info) -> str:
        entity_type = info.data.get("entity_type", "")
        validate_pattern(entity_type, v)
        return v


class NummernschemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entity_type: str
    name: str
    pattern: str
    scope: str
    start_value: int
    aktiv: bool


class NummernVorschau(BaseModel):
    nummer: Optional[str] = None
    hinweis: Optional[str] = None  # z.B. "Kein aktives Schema fuer diesen Objekttyp"
