from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime,timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    swap_request_id = Column(UUID(as_uuid=True), ForeignKey("swap_requests.id"))
    given_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    given_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rating = Column(Integer,nullable=False)
    comment = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    swap_request = relationship("SwapRequest", back_populates="reviews")
