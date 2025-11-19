import uuid

from fastapi import UploadFile

from core.config import settings
from object_storage.minio_client import minio_client
from schemas.candidate_file import CandidateFile
from services.file_service import get_file_extension


async def upload_file(file: UploadFile):
    await file.seek(0)
    id = uuid.uuid4()
    file_id = str(id)
    file_extension = await get_file_extension(file)
    minio_client.put_object(settings.MINIO_BUCKET, file_id + file_extension, file.file, file.size,
                            file.content_type)
    return CandidateFile(id=id, file_name=file.filename, content_type=file.content_type, file_size=file.size)

