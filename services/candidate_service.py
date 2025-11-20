from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.candidate_profile import CandidateProfile
from schemas.candidate_schemas import CandidateList


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
