from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schema.skills import SkillResponse
from models.skills import Skill
from database import get_db
from typing import List

skill_router = APIRouter(prefix="/skills", tags=["skills"])

@skill_router.get("/", response_model=List[SkillResponse])
async def list_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.skill_name.asc()))
    return result.scalars().all()
