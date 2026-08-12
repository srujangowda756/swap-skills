from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schema.skills import SkillCreate, SkillResponse
from models.skills import Skills
from database import get_db
from utility import get_current_user

skills_router = APIRouter(prefix="/skills", tags=["skills"])

@skills_router.post("/", status_code=201, response_model=SkillResponse)
async def create_skill(skill: SkillCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = current_user.get("sub")
    new_skill = Skills(name=skill.name, type=skill.type, user_id=user_id)
    db.add(new_skill)
    await db.commit()
    await db.refresh(new_skill)
    return new_skill

@skills_router.get("/user/{user_id}", response_model=list[SkillResponse])
async def get_user_skills(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skills).where(Skills.user_id == user_id))
    skills = result.scalars().all()
    return skills
