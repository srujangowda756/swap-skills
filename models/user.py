from sqlalchemy.sql import true
from database import Base
from sqlalchemy import Column, String, DateTime
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import timezone
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    name = Column(String, nullable=False,unique=True)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    skills = relationship("Skills", back_populates="user")
    