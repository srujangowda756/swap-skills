from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: UUID
    type: str
    reference_id: Optional[UUID]
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True