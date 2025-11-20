from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.position import Position
from schemas.position_schemas import PositionCreate


async def get_all_position(session: AsyncSession):
    result = await session.execute(select(Position))
    return result.scalars().all()


async def get_position_by_id(id: UUID, session: AsyncSession):
    return await session.get(Position, id)


async def create_position(position_create: PositionCreate, session: AsyncSession):
    position = Position(name=position_create.name, parameters=position_create.parameters)
    session.add(position)
    await session.commit()
    await session.refresh(position)
    return position
