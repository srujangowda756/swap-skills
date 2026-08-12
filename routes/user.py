from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schema.user import user_credentials, UserResponse
from models.user import User
from utility import hash_password, verify_password, create_access_token
from database import get_db

user_router= APIRouter(prefix="/user",tags=["user"])

@user_router.post("/register", status_code=201, response_model=UserResponse)
async def user_register(user_details:user_credentials, db: AsyncSession = Depends(get_db)):
    hashed_password=hash_password(user_details.password)
    try:
        new_user = User(name=user_details.name,email=user_details.email,password=hashed_password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@user_router.post("/login", status_code=200)
async def user_login(user_login:user_credentials, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
    
