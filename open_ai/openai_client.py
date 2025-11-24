import io
from openai import AsyncOpenAI
from core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def transcribe_audio(self, file_content: bytes, filename: str) -> dict:
    try:
        buffer = io.BytesIO(file_content)
        buffer.name = filename

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=buffer,
            language="uk",
            response_format="verbose_json"
        )

        return transcript.model_dump()

    except Exception as e:
        print(f"OpenAI Whisper Error: {e}")
        raise e
