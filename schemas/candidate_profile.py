import uuid
from sqlalchemy import Column, UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.session import Base


class CandidateProfile(Base):
    __tablename__ = 'candidate_profile'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile = Column(JSONB, nullable=False)
    files = relationship("CandidateFile", back_populates="candidate", cascade="all, delete-orphan",lazy="selectin")