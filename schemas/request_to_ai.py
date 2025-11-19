from pydantic import BaseModel


class RequestToAI(BaseModel):
    model: str
    prompt: str
    stream: bool
