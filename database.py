# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession,async_sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base
from config import settings
import ssl

DATABASE_URL = settings.DATABASE_URL

#fix URL for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

if "sslmode" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.split("?")[0]
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args = {"ssl": ssl_context}
else:
    connect_args = {}


engine = create_async_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)
SessionLocal = async_sessionmaker(engine, 
autocommit=False,
expire_on_commit=False, 
class_=AsyncSession,
autoflush=False)


Base = declarative_base()

async def get_db():
    async with SessionLocal() as db:
        yield db
