from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.candidate_list import CandidateList
from services.candidate_service import get_all_candidates

router = APIRouter(tags=["Candidate"])

@router.get("/get-all", response_model=List[CandidateList])
async def get_all(session: AsyncSession = Depends(get_db)):
    return await get_all_candidates(session)