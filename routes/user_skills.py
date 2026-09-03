from models import SkillType
from schema.user_skills import DiscoverResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List
from schema.user_skills import UserSkillCreate, UserSkillResponse, UserSkillWithSkillResponse
from models.user_skills import UserSkill
from models.user import User
from database import get_db
from dependencies import get_current_user

user_skill_router = APIRouter(prefix="/user-skills", tags=["user-skills"])

#used to add skill to user
@user_skill_router.post("/", status_code=201, response_model=UserSkillResponse)
async def add_user_skill(
    skill_data: UserSkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_entry = UserSkill(
        user_id=current_user.id,
        skill_id=skill_data.skill_id,
        type=skill_data.type,
    )
    db.add(new_entry)
    try:
        await db.commit()
        await db.refresh(new_entry)
        return new_entry
    except IntegrityError as e:
        await db.rollback()
        if "uq_user_skill" in str(e.orig):
            raise HTTPException(status_code=400, detail="Skill already added for this user")
        raise HTTPException(status_code=400, detail="Invalid skill_id")


@user_skill_router.get("/user/{user_id}", status_code=200, response_model=List[UserSkillWithSkillResponse])
async def get_skills_by_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UserSkill)
        .where(UserSkill.user_id == user_id)
        .options(selectinload(UserSkill.skill))
    )
    user_skills = result.scalars().all()
    if not user_skills:
        raise HTTPException(status_code=404, detail="No skills found for this user")

    return [
        UserSkillWithSkillResponse(
            id=us.id,
            type=us.type,
            added_at=us.added_at,
            skill_id=us.skill.id,
            skill_name=us.skill.skill_name,
            skill_description=us.skill.description,
        )
        for us in user_skills
    ]

@user_skill_router.get("/discover", status_code=200, response_model=List[DiscoverResponse])
async def discover_users_by_skill(
    skill_id: UUID,
    type: SkillType,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSkill)
        .where(UserSkill.skill_id == skill_id, UserSkill.type == type)
        .options(selectinload(UserSkill.skill), selectinload(UserSkill.user))
    )
    matches = result.scalars().all()
    if not matches:
        return []

    return [
        DiscoverResponse(
            id=m.id,
            type=m.type,
            added_at=m.added_at,
            skill_id=m.skill.id,
            skill_name=m.skill.skill_name,
            skill_description=m.skill.description,
            user_id=m.user.id,
            user_name=m.user.name,
        )
        for m in matches
    ]

@user_skill_router.delete("/{user_skill_id}", status_code=204)
async def delete_user_skill(
    user_skill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSkill).where(UserSkill.id == user_skill_id, UserSkill.user_id == current_user.id)
    )
    user_skill = result.scalar_one_or_none()
    if not user_skill:
        raise HTTPException(status_code=404, detail="User skill not found")

    await db.delete(user_skill)
    await db.commit()
    return None