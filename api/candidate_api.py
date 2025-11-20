from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.candidate_schemas import CandidateList, CandidateResponse
from services.candidate_service import get_all_candidates, get_candidate_by_id

router = APIRouter(tags=["Candidate"])


@router.get("/get-all", response_model=List[CandidateList])
async def get_all(session: AsyncSession = Depends(get_db)):
    return await get_all_candidates(session)


@router.get("/get/{id}", response_model=CandidateResponse)
async def get_by_id(id: UUID, session: AsyncSession = Depends(get_db)):
    return await get_candidate_by_id(id, session)
