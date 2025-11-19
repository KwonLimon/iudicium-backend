import uuid

from pydantic import BaseModel


class CandidateList(BaseModel):
    id: uuid.UUID
    full_name: str
