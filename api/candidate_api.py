from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.session import get_db
from schemas.candidate_schemas import CandidateList, CandidateResponse
from services.candidate_service import get_all_candidates, get_candidate_by_id, delete_candidate_by_id

router = APIRouter(tags=["Candidate"])


@router.get("/get-all", response_model=List[CandidateList])
async def get_all(session: AsyncSession = Depends(get_db)):
    return await get_all_candidates(session)


@router.get("/get/{candidate_id}", response_model=CandidateResponse)
async def get_by_id(candidate_id: UUID, session: AsyncSession = Depends(get_db)):
    return await get_candidate_by_id(candidate_id, session)


@router.delete("/delete/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_by_id(candidate_id: UUID, session: AsyncSession = Depends(get_db)):
    await delete_candidate_by_id(candidate_id, session)
    return None
