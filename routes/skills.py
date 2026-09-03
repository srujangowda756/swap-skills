from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from schema.skills import SkillResponse, SkillCreate
from models.skills import Skill
from database import get_db
from typing import List

skill_router = APIRouter(prefix="/skills", tags=["skills"])

@skill_router.get("/", response_model=List[SkillResponse])
async def list_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.skill_name.asc()))
    return result.scalars().all()

@skill_router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(skill_data: SkillCreate, db: AsyncSession = Depends(get_db)):
    # Check if skill with same name exists
    existing = await db.execute(select(Skill).where(Skill.skill_name.ilike(skill_data.skill_name.strip())))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Skill with this name already exists")
    
    new_skill = Skill(
        skill_name=skill_data.skill_name.strip(),
        description=skill_data.description.strip(),
    )
    db.add(new_skill)
    try:
        await db.commit()
        await db.refresh(new_skill)
        return new_skill
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Skill could not be created")