from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import require_admin
from models.user import User
from models.skills import Skill

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("/users/count")
async def user_count(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(User))
    return {"total_users": total}

@admin_router.get("/skills/count")
async def skill_count(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(Skill))
    return {"total_skills": total}



