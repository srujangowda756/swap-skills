import asyncio
from database import engine, Base
from models.user import User
from models.skills import Skills
from models.swapRequest import SwapRequest
from models.review import Review

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database tables created successfully!")
