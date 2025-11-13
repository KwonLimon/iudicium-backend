from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SendMessageToChat(BaseModel):
    id: Optional[UUID] = None
    prompt: str