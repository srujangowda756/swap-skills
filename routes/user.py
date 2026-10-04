import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter,HTTPException,Depends,BackgroundTasks,Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from schema.user import UserResponse, UserLogin, UserRegister, VerifyOTP, ResendOTP,ForgetPassword,ResetPassword
from models.user import User
from models.otp import OTP
from utility import hash_password, verify_password, create_access_token, generate_otp, send_otp_email
from database import get_db
from dependencies import get_current_user
from secret_store import get_secret
from slowapi import Limiter
from slowapi.util import get_remote_address



logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

user_router = APIRouter(prefix="/user", tags=["user"])


def _hash_otp(otp: str) -> str:
    return hmac.new(get_secret("SECRET_KEY").encode(), otp.encode(), hashlib.sha256).hexdigest()


def _expiry() -> datetime:
    return (datetime.now(timezone.utc) + timedelta(minutes=int(get_secret("OTP_TTL_MINUTES"))))


# new user register
@user_router.post("/register", status_code=201, response_model=UserResponse)
@limiter.limit("5/minute")
async def user_register(
    request: Request,
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
        await db.flush()

        otp_entry = OTP(user_id=new_user.id, code_hash=_hash_otp(otp), expires_at=_expiry())

        db.add(otp_entry)

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


@user_router.post("/forget-password", status_code=200)
@limiter.limit("5/minute")
async def forget_password(request:Request,forget_password: ForgetPassword, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user= await db.execute(select(User).where(User.email == forget_password.email))
    user = user.scalar_one_or_none()
    if user:
        otp = generate_otp()
        await db.execute(delete(OTP).where(OTP.user_id == user.id))
        otp_entry = OTP(user_id=user.id, code_hash=_hash_otp(otp), expires_at=_expiry())
        db.add(otp_entry)

        await db.commit()
        background_tasks.add_task(send_otp_email, user.email, otp)
    return {"message": "If the account exists and is verified, a password reset code was sent"}


@user_router.put("/set-new-password",status_code=200)
@limiter.limit("5/minute")
async def set_new_password(
    request: Request,
    reset_password: ResetPassword,
    db: AsyncSession = Depends(get_db),
):

    if reset_password.password != reset_password.confirm_password:
        raise HTTPException(status_code=400, detail="password and confirm password dont match")
    
    user = await db.execute(select(User).where(User.email == reset_password.email))
    user = user.scalar_one_or_none()

    if not user or not user.is_verified:
        raise HTTPException(status_code=403, detail="Invalid input")

    claimed = await db.execute(
        update(OTP)
        .where(
            OTP.user_id == user.id,
            OTP.attempts < int(get_secret("MAX_OTP_ATTEMPTS")),
            OTP.expires_at > datetime.now(timezone.utc),
        )
        .values(attempts=OTP.attempts + 1)
        .returning(OTP.code_hash)
    )

    row = claimed.first()

    await db.commit()
    
    if row is None or not hmac.compare_digest(row.code_hash, _hash_otp(reset_password.otp)):
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    await db.execute(update(User).where(User.id == user.id).values(password=hash_password(reset_password.password)))
    await db.execute(delete(OTP).where(OTP.user_id == user.id))
    await db.commit()

# verify the emailed code
@user_router.post("/verify-otp", status_code=200)
@limiter.limit("5/minute")
async def verify_otp(
    request: Request,
    data: VerifyOTP,
    db: AsyncSession = Depends(get_db),
):
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
@limiter.limit("5/minute")
async def resend_otp(
    request: Request,
    data: ResendOTP,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.is_verified:
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
        otp_entry = OTP(user_id=user_id, code_hash=_hash_otp(otp), expires_at=_expiry())
        db.add(otp_entry)

        await db.commit()
        background_tasks.add_task(send_otp_email, email, otp)

    return {"message": "If the account exists and is unverified, a new code was sent"}


# existing user login
@user_router.post("/login", status_code=200)
@limiter.limit("5/minute")
async def user_login(
    request: Request,
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user or not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.get("/me", status_code=200, response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user