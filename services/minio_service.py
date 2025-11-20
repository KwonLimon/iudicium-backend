from uuid import UUID, uuid4
from asyncio import to_thread, gather
from typing import List

from fastapi import UploadFile

from core.config import settings
from object_storage.minio_client import minio_client
from models.candidate_file import CandidateFile
from schemas.file_schemas import FileError
from services.file_service import get_file_extension


async def upload_file(file: UploadFile):
    await file.seek(0)
    id = uuid4()
    file_id = str(id)
    file_extension = await get_file_extension(file)
    await to_thread(
        minio_client.put_object, settings.MINIO_BUCKET, file_id + file_extension, file.file, file.size,
        file.content_type)
    return CandidateFile(id=id, file_name=file.filename, content_type=file.content_type, file_size=file.size)


async def upload_files(files: List[UploadFile]):
    upload_files = []
    error_files = []

    tasks = [upload_file(file) for file in files]
    results = await gather(*tasks, return_exceptions=True)

    for i,candidate_file in enumerate(results):
        if isinstance(candidate_file, Exception):
            error_file = FileError(file_name=files[i].filename, reason="Can't download file")
            error_files.append(error_file)
        else:
            upload_files.append(candidate_file)

    return upload_files, error_files