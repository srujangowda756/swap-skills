from database import Base
from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship

class Skill(Base):
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    skill_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=False)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user_links = relationship("UserSkill", back_populates="skill")