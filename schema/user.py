from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class BaseCredentials(BaseModel):
    email:str 
    name:str 
    password:str

class user_credentials(BaseCredentials):
    pass

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

