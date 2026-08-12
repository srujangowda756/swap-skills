from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SwapRequestCreate(BaseModel):
    receiver_id: UUID
    skill_offered: UUID
    skill_requested: UUID

class SwapRequestResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    status: str
    skill_offered: UUID
    skill_requested: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class SwapRequestUpdate(BaseModel):
    status: str  # "accepted", "rejected", "completed"
