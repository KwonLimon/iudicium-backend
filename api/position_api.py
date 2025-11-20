from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from schemas.position_schemas import PositionResponse, PositionCreate
from services.position_service import get_all_position, get_position_by_id, create_position

router = APIRouter(tags=["Position"])


@router.get("/get-all", response_model=List[PositionResponse])
async def get_all(session: AsyncSession = Depends(get_db)):
    return await get_all_position(session)


@router.get("/get/{id}", response_model=PositionResponse)
async def get_by_id(id: UUID, session: AsyncSession = Depends(get_db)):
    return await get_position_by_id(id, session)


@router.post("/create", response_model=PositionResponse)
async def create(position: PositionCreate, session: AsyncSession = Depends(get_db)):
    return await create_position(position, session)
