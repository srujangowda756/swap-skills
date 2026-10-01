from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class ReviewCreate(BaseModel):
    session_id: UUID
    reviewed_user_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: UUID
    session_id: UUID
    reviewer_id: UUID
    reviewed_user_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True