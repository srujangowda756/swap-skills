from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from models.user_skills import SkillType

class UserSkillCreate(BaseModel):
    skill_id: UUID
    type: SkillType

class UserSkillResponse(BaseModel):
    id: UUID
    skill_id: UUID
    type: SkillType
    added_at: datetime

    class Config:
        from_attributes = True

class UserSkillWithSkillResponse(BaseModel):
    id: UUID
    type: SkillType
    added_at: datetime
    skill_id: UUID
    skill_name: str
    skill_description: str

    class Config:
        from_attributes = True

class DiscoverResponse(BaseModel):
    id: UUID
    type: SkillType
    added_at: datetime
    skill_id: UUID
    skill_name: str
    skill_description: str
    user_id: UUID
    user_name: str

    class Config:
        from_attributes = True