import uuid

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    id: uuid.UUID
    file_name: str
    content_type: str
    file_size: int
    candidate_id: uuid.UUID
    model_config = ConfigDict(from_attributes = True)