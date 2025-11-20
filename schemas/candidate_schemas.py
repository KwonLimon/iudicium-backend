from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.file_schemas import FileResponse


class CandidateBase(BaseModel):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class CandidateResponse(CandidateBase):
    profile: dict
    files: List[FileResponse] = []


class CandidateList(CandidateBase):
    full_name: str
