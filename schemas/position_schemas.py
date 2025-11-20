from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PositionCreate(BaseModel):
    name: str
    parameters: List[dict]


class PositionResponse(PositionCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
