# pyrefly: ignore [missing-import]
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from config import settings
import logging
import secrets
import httpx
from secret_store import get_secret
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(get_secret("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, get_secret("SECRET_KEY"), algorithm=get_secret("ALGORITHM"))


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_secret("SECRET_KEY"), algorithms=[get_secret("ALGORITHM")])


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def send_otp_email(to_email: str, otp_code: str):
    try:
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": get_secret("BREVO_API_KEY"), "accept": "application/json"},
            json={
                "sender": {"name": get_secret("EMAIL_FROM_NAME"), "email": get_secret("EMAIL_FROM_ADDRESS")},
                "to": [{"email": to_email}],
                "subject": "Your SkillSwap verification code",
                "htmlContent": (
                    f"<p>Your verification code is <strong>{otp_code}</strong>. "
                    f"It expires in {int(get_secret("OTP_TTL_MINUTES"))} minutes.</p>"
                ),
            },
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        logger.exception("Failed to send OTP email to %s", to_email)