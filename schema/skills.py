from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class SkillCreate(BaseModel):
    name: str
    type: str

class SkillResponse(BaseModel):
    id: UUID
    name: str
    type: str
    user_id: UUID
    
    class Config:
        from_attributes = True
