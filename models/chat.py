from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.message import Message


class Chat(BaseModel):
    id: UUID
    context: list[Message]

