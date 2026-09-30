from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy import select, func,update,delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dependencies import require_admin
from models.user import User
from models.skills import Skill
from schema.admin import UpdatedSkill
from uuid import UUID
from schema.skills import SkillCreate,SkillResponse
from sqlalchemy.exc import IntegrityError
from models.swap_requests import SwapRequest

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("/users/count",status_code=200)
async def user_count(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(User))
    return {"total_users": total}

@admin_router.get("/skills/count",status_code=200)
async def skill_count(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(Skill))
    return {"total_skills": total}

@admin_router.get("/skills/list",status_code=200)
async def get_skill_by_id(db:AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skill))
    skills = res.scalars().all()
    return skills


@admin_router.get("/skills/list/{id}",status_code=200)
async def get_skill_by_id(id:UUID,db:AsyncSession = Depends(get_db)):
    res = await db.execute(select(Skill).where(Skill.id==id))
    skill=res.scalar_one_or_none()
    if not skill:
        raise HTTPException(404, detail="user not found")
    return skill



@admin_router.put("/skills/list/{id}")
async def update_skill(id:UUID,new_skill:UpdatedSkill,db:AsyncSession = Depends(get_db)):
    result=await db.execute(update(Skill).where(Skill.id==id).values(skill_name=new_skill.name,description=new_skill.description))
    
    if result.rowcount == 0:
        return {"message": "Skill not found"}
    
    try:
        await db.commit()
        return {"status":"ok"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Skill could not be updated")
    


@admin_router.post("/skills", response_model=SkillResponse, status_code=201)
async def create_skill(skill_data: SkillCreate, db: AsyncSession = Depends(get_db)):
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


@admin_router.delete("/skills/{id}",status_code=200)
async def delete_skill_by_id(id:UUID,db:AsyncSession = Depends(get_db)):
    await db.execute(delete(Skill).where(Skill.id==id))
    try:
        await db.commit()
        return {"status":"ok"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Skill could not be delete")

@admin_router.get("/users/stats")
async def user_stats(db: AsyncSession = Depends(get_db)):
    total = await db.scalar(select(func.count()).select_from(User))
    verified = await db.scalar(select(func.count()).select_from(User).where(User.is_verified == True))
    return {"total_users": total, "verified_users": verified, "unverified_users": total - verified}


@admin_router.get("/swap-requests/stats")
async def swap_request_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SwapRequest.status, func.count()).group_by(SwapRequest.status))
    return {status.value: count for status, count in result.all()}
