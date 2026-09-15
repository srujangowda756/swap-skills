from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from models.swap_requests import RequestStatus

class SwapRequestCreate(BaseModel):
    receiver_id: UUID

class SwapRequestResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    status: RequestStatus
    created_at: datetime
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True