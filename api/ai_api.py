import os
import shutil
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.ai_schemas import RefreshRequest
from schemas.candidate_schemas import CandidateResponse
from services.ai_service import generate_answer, refresh_candidate, get_questions_for_candidate
from services.audio_service import process_audio

router = APIRouter(tags=["AI"])


@router.post("/generate", response_model=CandidateResponse)
async def generate(prompt: str | None = Form(None), position_id: UUID = Form(...), files: List[UploadFile] = File(...),
                   websearch: bool = False,
                   session: AsyncSession = Depends(get_db)):
    return await generate_answer(prompt, position_id, files, websearch, session)


@router.post("/refresh/{candidate_id}", response_model=CandidateResponse)
async def refresh(candidate_id: UUID, body: RefreshRequest | None = None, websearch: bool = False,
                  session: AsyncSession = Depends(get_db)):
    return await refresh_candidate(candidate_id, body.prompt if body else None, websearch, session)


@router.post("/refresh/voice/{candidate_id}", response_model=CandidateResponse)
async def refresh(candidate_id: UUID, record: UploadFile = File(...), websearch: bool = False,
                  session: AsyncSession = Depends(get_db)):
    temp_filename = f"temp_{record.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(record.file, buffer)

        raw_text = await process_audio(temp_filename)

        return await refresh_candidate(candidate_id, raw_text, websearch, session)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


@router.get("/questions/{candidate_id}")
async def get_questions(candidate_id: UUID, session: AsyncSession = Depends(get_db)):
    return await get_questions_for_candidate(candidate_id, session)
