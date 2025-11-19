from sqlalchemy import select

from models.candidate_profile import CandidateProfile
from schemas.candidate_list import CandidateList


async def get_all_candidates(session):
    query = select(CandidateProfile.id, CandidateProfile.profile["candidate"]["full_name"]
                   .as_string().label("full_name"))
    result = await session.execute(query)
    rows = result.mappings().all()
    return [CandidateList(**row) for row in rows]