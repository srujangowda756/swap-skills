from fastapi import APIRouter,HTTPException
from schema.user import user_credentials
from models.user import User
from utility import hash_password

user_router= APIRouter(prefix="user",tags=["user"])

@user_router.post("/register", status_code=201)
def user_register(user_details:user_credentials):
    hashed_password=hash_password(user_details.password)
    try:
        new_user = User(name=user_details.name,email=user_details.email,password=hashed_password)
    except:
        raise HTTPException(status_code=401)
    return new_user


@user_router.post("/login", status_code=200)
def user_login(user_login:user_credentials):
    pass
    
