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


@router.post("/generate", response_model=CandidateResponse, summary="📄 Аналіз резюме та створення профілю",
             description="Приймає файли резюме (PDF, DOCX, TXT, JSON, CSV) та опис вакансії. ШІ аналізує відповідність, шукає ризики та формує JSON-профіль.")
async def generate(prompt: str | None = Form(None), position_id: UUID = Form(...),
                   files: List[UploadFile] = File(..., description="Список файлів резюме"),
                   websearch: bool = False,
                   session: AsyncSession = Depends(get_db)):
    return await generate_answer(prompt, position_id, files, websearch, session)


@router.post("/refresh/{candidate_id}", response_model=CandidateResponse, summary="🔄 Уточнити аналіз (Текст)",
             description="Дозволяє попросити ШІ переробити аналіз з урахуванням нових текстових вказівок.")
async def refresh(candidate_id: UUID, body: RefreshRequest | None = None, websearch: bool = False,
                  session: AsyncSession = Depends(get_db)):
    """
        Використовується, якщо рекрутер хоче уточнити деталі.
        Наприклад: *"Перевір, чи знає він бібліотеку Pandas, я не побачив це у звіті"*.
        """
    return await refresh_candidate(candidate_id, body.prompt if body else None, websearch, session)


@router.post("/refresh/voice/{candidate_id}", response_model=CandidateResponse, summary="🎙️ Уточнити аналіз (Голос)",
             description="Приймає аудіофайл (голосову нотатку), транскрибує його в текст і використовує як промпт для оновлення аналізу."
             )
async def refresh_by_voice(candidate_id: UUID, record: UploadFile = File(..., description="Аудіофайл (mp3, wav, ogg)"),
                           websearch: bool = False,
                           session: AsyncSession = Depends(get_db)):
    """
        **Flow:**
        1. Завантаження аудіо.
        2. Транскрибація через Open_AI (Audio-to-Text).
        3. Виклик функції оновлення кандидата з отриманим текстом.
        """
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


@router.get("/questions/{candidate_id}", summary="❓ Згенерувати питання для інтерв'ю",
            description="ШІ аналізує слабкі сторони кандидата та вимоги вакансії, щоб створити список технічних та поведінкових питань.")
async def get_questions(candidate_id: UUID, session: AsyncSession = Depends(get_db)):
    return await get_questions_for_candidate(candidate_id, session)
