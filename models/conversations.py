from database import Base
from sqlalchemy import Column, DateTime, ForeignKey
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    swap_request_id = Column(UUID(as_uuid=True), ForeignKey("swap_requests.id"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    swap_request = relationship("SwapRequest")
    messages = relationship("Message", back_populates="conversation")