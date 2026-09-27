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
        
class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)

class ResendOTP(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email:EmailStr
    password:str
    confirm_password:str
    otp:str = Field(min_length=6, max_length=6)

class ForgetPassword(BaseModel):
    email:EmailStr
