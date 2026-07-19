from database import Base
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone

class SwapRequest(Base):
    __tablename__ = "swap_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)
    skill_offered = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    skill_requested = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
