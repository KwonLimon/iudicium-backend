import json
from typing import List
from uuid import UUID

import httpx
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.prompt import basePrompt, info_prompt, short_info_prompt, question_prompt
from schemas.ai_schemas import RequestToAI
from schemas.candidate_schemas import CandidateResponse, ShortCandidateInfo
from schemas.position_schemas import PositionResponse
from services.candidate_service import get_candidate_by_id, create_candidate, update_candidate_profile
from services.file_service import read_files, read_files_from_minio
from services.minio_service import upload_files
from services.position_service import get_position_by_id
from services.youcontrol_service import check_candidate


async def generate_answer(prompt: str, position_id: UUID, files: List[UploadFile], websearch: bool,
                          session: AsyncSession):
    """
        Основний пайплайн створення кандидата: обробка файлів, AI-аналіз та збереження.

        Ця функція виконує повний цикл обробки нового кандидата:
        1. Зчитує та парсить текст із завантажених файлів (PDF, DOCX, TXT).
        2. (Опціонально) Виконує OSINT-пошук (Websearch) по відкритих реєстрах.
        3. Формує промпт та відправляє запит до LLM (Ollama) для аналізу резюме.
        4. Валідує отримані дані (перевіряє наявність імені).
        5. Завантажує файли у сховище MinIO.
        6. Створює запис про кандидата в базі даних.

        Args:
            prompt (str): Додаткові вказівки від користувача для AI (наприклад, "Зверни увагу на досвід з AWS").
            position_id (UUID): ID вакансії, на яку подається кандидат (для порівняння вимог).
            files (List[UploadFile]): Список файлів резюме.
            websearch (bool): Прапорець для увімкнення перевірки по реєстрах (YouControl).
            session (AsyncSession): Сесія бази даних.

        Returns:
            CandidateResponse: Сформований об'єкт кандидата з оцінками та файлами.

        Raises:
            HTTPException(422): Якщо AI не зміг знайти ім'я кандидата або дані некоректні.
        """
    full_text, processed_files, error_files = await read_files(files)

    additional_info = ""
    if websearch:
        additional_info = do_websearch(full_text)

    profile_data = await make_request(full_text, position_id, prompt, additional_info, session)
    if profile_data["candidate"]["full_name"] == "unknown":
        raise HTTPException(status_code=422, detail="No candidate data")
    candidate_files, upload_error_files = await upload_files(processed_files)
    error_files.extend(upload_error_files)
    new_candidate = await create_candidate(profile_data, candidate_files, position_id, prompt, session)

    return CandidateResponse(id=new_candidate.id, profile=new_candidate.profile, position_id=new_candidate.position_id,
                             files=new_candidate.files, error_files=error_files)


async def refresh_candidate(candidate_id: UUID, prompt: str, websearch: bool, session: AsyncSession):
    """
        Оновлення (регенерація) профілю існуючого кандидата.

        Використовується, коли потрібно перерахувати оцінки або додати нові вказівки для AI
        без повторного завантаження файлів. Файли витягуються з MinIO.

        Args:
            candidate_id (UUID): ID існуючого кандидата.
            prompt (str): Нові або додаткові інструкції для AI.
            websearch (bool): Чи потрібно (пере)запускати пошук по реєстрах.
            session (AsyncSession): Сесія бази даних.

        Returns:
            CandidateResponse: Оновлений об'єкт кандидата.
        """
    candidate = await get_candidate_by_id(candidate_id, session)
    files = candidate.files
    full_text, processed_files, error_files = await read_files_from_minio(files)

    additional_info = ""
    if websearch:
        additional_info = do_websearch(full_text)

    profile_data = await make_request(full_text, candidate.position_id, candidate.additional_info + prompt,
                                      additional_info, session)
    updated_candidate = await update_candidate_profile(candidate_id, profile_data, prompt, session)
    return CandidateResponse(id=updated_candidate.id, profile=updated_candidate.profile,
                             position_id=updated_candidate.position_id,
                             files=updated_candidate.files, error_files=error_files)


async def make_request(full_text: str, position_id: UUID, prompt: str, additional_info, session: AsyncSession):
    """
        Формування промпту та виконання запиту до LLM (Ollama).

        Функція збирає всі дані (текст резюме, опис вакансії, дані з реєстрів, вказівки користувача)
        в один великий промпт і відправляє його моделі.

        Args:
            full_text (str): Повний текст резюме.
            position_id (UUID): ID вакансії для отримання вимог.
            prompt (str): Вказівки користувача.
            additional_info (str): Результати пошуку OSINT (JSON-строка).
            session (AsyncSession): Сесія БД.

        Returns:
            dict: Розпарсений JSON-відповідь від AI з аналізом кандидата.
        """
    position_orm = await get_position_by_id(position_id, session)
    position = PositionResponse.model_validate(position_orm).model_dump_json()
    final_prompt = basePrompt + info_prompt.format(full_text=full_text, position=position, prompt=prompt,
                                                   additional_info=additional_info)

    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        request = RequestToAI(model=settings.AI_MODEL, prompt=final_prompt, stream=False,
                              format="json",
                              options={"temperature": 0.0, "seed": 137})
        response = await client.post(
            f"{settings.OLLAMA_API}/api/generate",
            json=request.model_dump()
        )

        data = json.loads(response.text)
        answer = data["response"]
        return json.loads(answer)


async def get_short_candidate_info(full_text: str):
    """
        Екстракція короткої інформації (ПІБ, дата народження) для пошуку.

        Використовує окремий, короткий промпт для AI, щоб швидко витягнути
        дані, необхідні для запитів у зовнішні реєстри.

        Args:
            full_text (str): Текст резюме.

        Returns:
            ShortCandidateInfo: Pydantic-модель з ім'ям та датою народження.

        Raises:
            HTTPException(422): Якщо прізвище не знайдено.
        """
    final_prompt = short_info_prompt + full_text
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        request = RequestToAI(model=settings.AI_MODEL, prompt=final_prompt, stream=False, format="json",
                              options={"temperature": 0.0, "seed": 137})
        response = await client.post(
            f"{settings.OLLAMA_API}/api/generate",
            json=request.model_dump()
        )
        data = json.loads(response.text)
        answer = data["response"]
        answer = json.loads(answer)
        print(answer)
        candidate_info = ShortCandidateInfo(**answer)

        if not candidate_info.LastName:
            raise HTTPException(status_code=422, detail="No candidate data")

        return candidate_info


async def do_websearch(full_text: str):
    """
        Оркестратор OSINT-пошуку (YouControl).

        1. Витягує ПІБ та дату народження з тексту резюме (через AI).
        2. Робить запити до реєстрів YouControl.
        3. Повертає результат у вигляді JSON-строки для додавання в контекст AI.

        Args:
            full_text (str): Текст резюме.

        Returns:
            str: JSON-строка зі знайденими ризиками або інформацією про відсутність даних.
        """
    candidate_info = await get_short_candidate_info(full_text)
    youcontrol_info = await check_candidate(candidate_info.LastName, candidate_info.FirstName,
                                            candidate_info.MiddleName, candidate_info.BirthDate)
    return json.dumps(youcontrol_info)


async def get_questions_for_candidate(candidate_id: UUID, session: AsyncSession):
    """
        Генерація персоналізованих питань для співбесіди.

        Аналізує профіль кандидата (навички, досвід) і створює список питань
        для перевірки його компетенцій.

        Args:
            candidate_id (UUID): ID кандидата.
            session (AsyncSession): Сесія БД.

        Returns:
            str: Текстовий список питань (або JSON, залежно від промпту).
        """
    candidate = await get_candidate_by_id(candidate_id, session)
    profile = json.dumps(candidate.profile, ensure_ascii=False, indent=2)
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        request = RequestToAI(model=settings.AI_MODEL, prompt=question_prompt.format(profile=profile),
                              stream=False,
                              options={"temperature": 0.7})
        response = await client.post(f"{settings.OLLAMA_API}/api/generate",
                                     json=request.model_dump()
                                     )
        data = json.loads(response.text)
        answer = data["response"]
        return answer
