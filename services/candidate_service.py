import os
from asyncio import to_thread, gather
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.candidate_profile import CandidateProfile
from object_storage.minio_client import minio_client
from schemas.candidate_schemas import CandidateList
from services.file_service import get_file_extension, ALLOWED_BINARY_TYPES


async def get_all_candidates(session: AsyncSession):
    query = select(CandidateProfile.id, CandidateProfile.profile["candidate"]["full_name"]
                   .as_string().label("full_name"))
    result = await session.execute(query)
    rows = result.mappings().all()
    return [CandidateList(**row) for row in rows]


async def get_candidate_by_id(id: UUID, session: AsyncSession):
    candidate = await session.get(CandidateProfile, id)

    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return candidate

async def delete_candidate_by_id(id: UUID, session: AsyncSession):
    candidate = await session.get(CandidateProfile, id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    minio_tasks = []

    for file in candidate.files:
        if file.content_type.startswith("text/"):
            filename = file.file_name
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
        else:
            ext = ALLOWED_BINARY_TYPES[file.content_type]
        task = to_thread(minio_client.remove_object, settings.MINIO_BUCKET, str(file.id) + ext)
        minio_tasks.append(task)

    if minio_tasks:
        await gather(*minio_tasks, return_exceptions=True)

    await session.delete(candidate)
    await session.commit()
