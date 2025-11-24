from typing import Any

from pydantic import BaseModel


class RequestToAI(BaseModel):
    model: str
    prompt: str
    stream: bool
    format: str | None = None
    options: dict[str, Any]

class RefreshRequest(BaseModel):
    prompt: str