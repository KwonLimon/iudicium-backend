import uuid
from typing import Optional, List
from uuid import UUID

from sqlmodel import SQLModel, Field, Relationship



class ChatSchema(SQLModel, table=True):
    __tablename__ = 'chat'
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    context: Optional[List["MessageSchema"]] = Relationship(back_populates="chat")

from .message_schema import MessageSchema
ChatSchema.model_rebuild()


