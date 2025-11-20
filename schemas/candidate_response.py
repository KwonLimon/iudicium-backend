from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.file_response import FileResponse


class CandidateResponse(BaseModel):
    id: UUID
    profile: dict
    files: List[FileResponse] = []
    model_config = ConfigDict(from_attributes = True)