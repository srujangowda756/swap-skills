from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from models.session import SessionStatus

class SessionCreate(BaseModel):
    swap_request_id: UUID
    scheduled_at: datetime
    duration_minutes: Optional[int] = None

class SessionResponse(BaseModel):
    id: UUID
    swap_request_id: UUID
    scheduled_at: datetime
    duration_minutes: Optional[int]
    status: SessionStatus
    created_at: datetime

    class Config:
        from_attributes = True