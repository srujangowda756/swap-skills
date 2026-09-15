from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    conversation_id: UUID
    content: str

class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    content: str
    sent_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True