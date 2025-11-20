from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.candidate_schemas import CandidateResponse
from services.ai_service import generate_answer

router = APIRouter(tags=["AI"])


@router.post("/generate", response_model=CandidateResponse)
async def generate(prompt: str = Form(...), file: UploadFile = File(...), session: AsyncSession = Depends(get_db)):
    return await generate_answer(prompt, file, session)
