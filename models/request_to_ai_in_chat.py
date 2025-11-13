from pydantic import BaseModel

from models.message import Message


class RequestToAIInChat(BaseModel):
    model: str
    messages: list[Message]
    stream: bool