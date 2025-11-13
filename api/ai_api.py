from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from db.session import get_db
from models.prompt import Prompt
from models.send_message_to_chat import SendMessageToChat
from services.ai_service import generateAnswer, chatWithBot

router = APIRouter(tags=["AI"])

@router.post("/generate")
async def generate(request: Prompt):
   return await generateAnswer(request.prompt)


@router.post("/chat")
async def chat(request: SendMessageToChat, session: AsyncSession = Depends(get_db)):
    return await chatWithBot(request.id, request.prompt, session)


