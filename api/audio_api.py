from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from services.audio_service import audio_service

router = APIRouter()


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{file.filename}"

    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Отримуємо чистий рядок тексту
        raw_text = await audio_service.process_audio(temp_filename)

        # Повертаємо як JSON поле
        return {"text": raw_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)