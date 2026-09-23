from database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    skills = relationship("UserSkill", back_populates="user")   