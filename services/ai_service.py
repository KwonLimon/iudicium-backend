import json
import httpx
from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from core.config import settings
from models.message import Message
from models.request_to_ai import RequestToAI
from models.request_to_ai_in_chat import RequestToAIInChat
from schemas.chat_schema import ChatSchema
from schemas.message_schema import MessageSchema


async def generateAnswer(prompt):
    async with httpx.AsyncClient() as client:
        request = RequestToAI(model=settings.AI_MODEL, prompt=prompt, stream=False)
        response = await client.post(
            f"{settings.OLLAMA_API}/api/generate",
            json=request.model_dump()
        )
        data = json.loads(response.text)
        answer = data["response"]
    return {"answer": answer}


async def getChat(id, message, session):
    if id is None:
        new_chat = ChatSchema(context=[message])
        session.add(new_chat)
        await session.commit()
        await session.refresh(new_chat)
        new_chat = await loadChatFromDb(new_chat.id, session)
        return new_chat

    chat = await loadChatFromDb(id, session)

    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    await addMessageToContext(chat, message, session)

    return chat


async def addMessageToContext(chat, message, session):
    chat.context.append(message)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat

async def loadChatFromDb(id, session):
    result = await session.execute(
        select(ChatSchema)
        .options(selectinload(ChatSchema.context))
        .where(ChatSchema.id == id)
    )
    chat = result.scalars().one()
    return chat

async def chatWithBot(id, prompt, session):
    user_message = MessageSchema(role="user", content=prompt)
    chat = await getChat(id, user_message, session)
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        messages = [Message(role=m.role, content=m.content) for m in chat.context]
        request = RequestToAIInChat(model=settings.AI_MODEL, messages=messages, stream=False)
        print(request)
        response = await client.post(
            f"{settings.OLLAMA_API}/api/chat",
            json=request.model_dump()
        )
        print(response.text)
        data = json.loads(response.text)
        answer = data["message"]["content"]
        ai_message = MessageSchema(role="assistant", content=answer)
        await addMessageToContext(chat, ai_message, session)
    return {"chat_id": chat.id, "answer": answer}
