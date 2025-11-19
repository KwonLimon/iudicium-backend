import uuid
from typing import List

from pydantic import BaseModel, ConfigDict

from schemas.file_response import FileResponse


class CandidateResponse(BaseModel):
    id: uuid.UUID
    profile: dict
    files: List[FileResponse] = []
    model_config = ConfigDict(from_attributes = True)