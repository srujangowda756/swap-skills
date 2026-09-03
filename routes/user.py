from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schema.user import UserResponse, UserLogin, UserRegister
from models.user import User
from utility import hash_password, verify_password, create_access_token
from database import get_db
from sqlalchemy.exc import IntegrityError
from dependencies import get_current_user

user_router = APIRouter(prefix="/user", tags=["user"])

#new user register
@user_router.post("/register", status_code=201, response_model=UserResponse)
async def user_register(user_details: UserRegister, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).where(User.email == user_details.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    hashed_password = hash_password(user_details.password)
    try:
        new_user = User(name=user_details.name, email=user_details.email, password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

#existing user login
@user_router.post("/login", status_code=200)
async def user_login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
    
@user_router.get("/me", status_code=200, response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user