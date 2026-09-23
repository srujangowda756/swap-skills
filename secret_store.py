from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.secret_key import SecretKey

_cache: dict[str, str] = {}


async def load_secrets(db: AsyncSession) -> None:
    rows = (await db.execute(select(SecretKey))).scalars().all()
    _cache.update({row.name: row.value for row in rows})


def get_secret(name: str) -> str:
    return _cache[name]