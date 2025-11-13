from uuid import UUID

from sqlmodel import SQLModel, Field, Relationship

class MessageSchema(SQLModel, table=True):
    __tablename__ = 'message'

    id: int = Field(primary_key=True, unique=True)
    role: str = Field(nullable=False)
    content: str | None
    chat_id: UUID = Field(foreign_key="chat.id")
    chat: "ChatSchema" = Relationship(back_populates="context")

from .chat_schema import ChatSchema
MessageSchema.model_rebuild()