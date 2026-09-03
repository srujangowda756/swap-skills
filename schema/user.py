from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True