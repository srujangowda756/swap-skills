from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SkillCreate(BaseModel):
    skill_name: str
    description: str

class SkillResponse(BaseModel):
    id: UUID
    skill_name: str
    description: str
    added_at: datetime

    class Config:
        from_attributes = True