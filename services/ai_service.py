import json

import fitz
import httpx
from docx.document import Document
from fastapi import UploadFile, File, HTTPException

from core.config import settings
from models.request_to_ai import RequestToAI
from schemas.candidate_profile import CandidateProfile

basePrompt = """Твоє завдання — проаналізувати наданий файл із резюме та створити стандартизований JSON-профіль кандидата.

Спочатку уважно прочитай документ. Якщо деякі дані відсутні або сумнівні — познач їх як "unknown" або "not specified", але не вигадуй інформацію.
Інформацію в JSON зроби украънською мовою

📌 Структура вихідних даних (JSON)

Створи JSON у такому форматі:

{
  "candidate": {
    "full_name": "",
    "date_of_birth": "",
    "contacts": {
      "phone": "",
      "email": "",
      "location": ""
    },
    "education": [
      {
        "institution": "",
        "degree": "",
        "specialization": "",
        "years": ""
      }
    ],
    "work_experience": [
      {
        "position": "",
        "company": "",
        "industry": "",
        "responsibilities": "",
        "years": "",
        "duration_years": ""
      }
    ],
    "skills": [],
    "languages": [],
    "certifications": [],
    "additional_info": ""
  },

  "evaluation": {
    "trust_score": 0,
    "integrity_score": 0,
    "leadership_maturity_score": 0,
    "overall_profile_index": 0,
    "relevance_to_position_score": 0
  },

  "risk_analysis": {
    "conflict_of_interest": false,
    "frequent_job_changes": false,
    "disciplinary_issues": false,
    "competency_mismatch": false,
    "notes": ""
  },

  "position_relevance": {
    "key_competencies_match": "",
    "experience_relevance": "",
    "responsibility_level_match": "",
    "overall_score": 0
  },

  "summary_conclusion": ""
}

📌 Логіка оцінювання

Застосуй наступні критерії:

trust_score, integrity_score, leadership_maturity_score, relevance_to_position_score оцінюй за шкалою 0–10

overall_profile_index — це середнє арифметичне попередніх показників.

Якщо знайдені червоні прапорці — відобрази їх у risk_analysis.notes.

📌 Висновок

У полі "summary_conclusion" створи короткий аналітичний висновок (4–7 речень), який має пояснити:

Наскільки кандидат відповідає вимогам.

Чи є ризики.

Чи рекомендується він до подальшого відбору та чому.


📌 Формат відповіді

👉 Відповідь повинна бути лише валідним JSON у наданому форматі без додаткових коментарів.
Не додавай кодових блоків, Markdown,коментарів чи додаткового тексту.
Вивід має починатися з { і закінчуватися }"""



async def generate_answer(prompt, file ,session):
    text = await process_file(file)
    prompt = basePrompt + f"\nДані про кандидата:{text}\n" + prompt
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        request = RequestToAI(model=settings.AI_MODEL, prompt=prompt, stream=False)
        response = await client.post(
            f"{settings.OLLAMA_API}/api/generate",
            json=request.model_dump()
        )
        data = json.loads(response.text)
        answer = data["response"]
        answer = answer.replace("```", "")
        answer = answer.replace("json", "")
        profile = CandidateProfile(profile=answer)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile

async def process_file(file: UploadFile = File(...)):
    content_type = file.content_type

    if content_type.startswith("text/"):
        text = (await file.read()).decode("utf-8")
        return text

    if content_type == "application/pdf":
        pdf_bytes = await file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        return text

    if content_type == "application/json":
        text = json.loads(await file.read())
        return text

    if "officedocument.wordprocessingml" in content_type:
        doc = Document(file.file)
        text = "\n".join(p.text for p in doc.paragraphs)
        return text


    raise HTTPException(
        status_code=415,
        detail=f"Unsupported file type: {content_type}"
    )
