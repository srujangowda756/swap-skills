import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from schema.user import UserResponse, UserLogin, UserRegister, VerifyOTP, ResendOTP
from models.user import User
from models.otp import OTP
from utility import hash_password, verify_password, create_access_token, generate_otp, send_otp_email
from database import get_db
from dependencies import get_current_user
from config import settings
from secret_store import get_secret

logger = logging.getLogger(__name__)

user_router = APIRouter(prefix="/user", tags=["user"])


def _hash_otp(otp: str) -> str:
    return hmac.new(get_secret("SECRET_KEY").encode(), otp.encode(), hashlib.sha256).hexdigest()


def _expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=int(get_secret("OTP_TTL_MINUTES")))


# new user register
@user_router.post("/register", status_code=201, response_model=UserResponse)
async def user_register(
    user_details: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await db.execute(select(User).where(User.email == user_details.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A user with this email already exists")

    hashed_password = hash_password(user_details.password)
    otp = generate_otp()
    try:
        new_user = User(
            name=user_details.name,
            email=user_details.email,
            password=hashed_password,
            is_verified=False,
        )
        db.add(new_user)
        await db.flush()  # assigns new_user.id
        db.add(OTP(user_id=new_user.id, code_hash=_hash_otp(otp), expires_at=_expiry()))
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Database integrity error")
    except Exception:
        await db.rollback()
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")

    background_tasks.add_task(send_otp_email, new_user.email, otp)
    return new_user


# verify the emailed code
@user_router.post("/verify-otp", status_code=200)
async def verify_otp(data: VerifyOTP, db: AsyncSession = Depends(get_db)):
    invalid = HTTPException(status_code=400, detail="Invalid or expired code")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or user.is_verified:
        raise invalid
    user_id = user.id

    # claim an attempt atomically so parallel requests can't bypass the cap
    claimed = await db.execute(
        update(OTP)
        .where(
            OTP.user_id == user_id,
            OTP.attempts < int(get_secret("MAX_OTP_ATTEMPTS")),
            OTP.expires_at > datetime.now(timezone.utc),
        )
        .values(attempts=OTP.attempts + 1)
        .returning(OTP.code_hash)
    )
    row = claimed.first()
    await db.commit()
    if row is None:
        raise invalid

    if not hmac.compare_digest(row.code_hash, _hash_otp(data.otp)):
        raise invalid

    await db.execute(delete(OTP).where(OTP.user_id == user_id))
    await db.execute(update(User).where(User.id == user_id).values(is_verified=True))
    await db.commit()
    return {"message": "Email verified"}


# issue a fresh code
@user_router.post("/resend-otp", status_code=200)
async def resend_otp(
    data: ResendOTP,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user and not user.is_verified:
        user_id, email = user.id, user.email
        existing = (
            await db.execute(select(OTP).where(OTP.user_id == user_id))
        ).scalar_one_or_none()
        if existing and datetime.now(timezone.utc) - existing.created_at < timedelta(
            seconds=int(get_secret("RESEND_COOLDOWN_SECONDS"))
        ):
            raise HTTPException(status_code=429, detail="Wait a minute before requesting another code")

        otp = generate_otp()
        await db.execute(delete(OTP).where(OTP.user_id == user_id))
        db.add(OTP(user_id=user_id, code_hash=_hash_otp(otp), expires_at=_expiry()))
        await db.commit()
        background_tasks.add_task(send_otp_email, email, otp)

    return {"message": "If the account exists and is unverified, a new code was sent"}


# existing user login
@user_router.post("/login", status_code=200)
async def user_login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.get("/me", status_code=200, response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user