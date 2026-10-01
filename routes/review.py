from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID
from typing import List

from schema.review import ReviewCreate, ReviewResponse
from models.review import Review
from models.session import Session, SessionStatus
from models.swap_requests import SwapRequest
from models.user import User
from database import get_db
from dependencies import get_current_user

review_router = APIRouter(prefix="/reviews", tags=["reviews"])


@review_router.post("/", status_code=201, response_model=ReviewResponse)
async def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session_result = await db.execute(select(Session).where(Session.id == data.session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.completed:
        raise HTTPException(status_code=400, detail="Can only review a completed session")

    swap_result = await db.execute(select(SwapRequest).where(SwapRequest.id == session.swap_request_id))
    swap_request = swap_result.scalar_one_or_none()
    participants = (swap_request.sender_id, swap_request.receiver_id)
    if current_user.id not in participants:
        raise HTTPException(status_code=403, detail="Not a participant in this session")
    if data.reviewed_user_id not in participants or data.reviewed_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Can only review the other participant in this session")

    new_review = Review(
        session_id=data.session_id,
        reviewer_id=current_user.id,
        reviewed_user_id=data.reviewed_user_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(new_review)
    try:
        await db.commit()
        await db.refresh(new_review)
        return new_review
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="You already reviewed this session")


@review_router.get("/user/{user_id}", status_code=200, response_model=List[ReviewResponse])
async def get_user_reviews(user_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.reviewed_user_id == user_id).order_by(Review.created_at.desc())
    )
    return result.scalars().all()