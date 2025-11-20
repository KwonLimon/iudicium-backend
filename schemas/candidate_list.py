from uuid import UUID

from pydantic import BaseModel


class CandidateList(BaseModel):
    id: UUID
    full_name: str
