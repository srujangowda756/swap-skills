from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Enum, Integer
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship
import enum

class SessionStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    swap_request_id = Column(UUID(as_uuid=True), ForeignKey("swap_requests.id"), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.scheduled)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    swap_request = relationship("SwapRequest")
    reviews = relationship("Review", back_populates="session")