from database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Enum, Index
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy.orm import relationship
import enum

class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class SwapRequest(Base):
    __tablename__ = "swap_requests"
    __table_args__ = (
        Index(
            "uq_pending_sender_receiver",
            "sender_id", "receiver_id",
            unique=True,
            postgresql_where=(Column("status") == "pending"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.pending)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    responded_at = Column(DateTime(timezone=True), nullable=True)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])