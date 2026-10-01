from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from schema.session import SessionCreate, SessionResponse
from models.session import Session, SessionStatus
from models.swap_requests import SwapRequest, RequestStatus
from models.user import User
from database import get_db
from dependencies import get_current_user

session_router = APIRouter(prefix="/sessions", tags=["sessions"])


async def _get_swap_request_or_403(swap_request_id: UUID, current_user: User, db: DBSession) -> SwapRequest:
    result = await db.execute(select(SwapRequest).where(SwapRequest.id == swap_request_id))
    swap_request = result.scalar_one_or_none()
    if not swap_request:
        raise HTTPException(status_code=404, detail="Swap request not found")
    if current_user.id not in (swap_request.sender_id, swap_request.receiver_id):
        raise HTTPException(status_code=403, detail="Not a participant in this swap request")
    if swap_request.status != RequestStatus.accepted:
        raise HTTPException(status_code=400, detail="Swap request must be accepted before scheduling a session")
    return swap_request


@session_router.post("/", status_code=201, response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    await _get_swap_request_or_403(data.swap_request_id, current_user, db)

    new_session = Session(
        swap_request_id=data.swap_request_id,
        scheduled_at=data.scheduled_at,
        duration_minutes=data.duration_minutes,
    )
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session


@session_router.get("/mine", status_code=200, response_model=List[SessionResponse])
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    result = await db.execute(
        select(Session)
        .join(SwapRequest, Session.swap_request_id == SwapRequest.id)
        .where((SwapRequest.sender_id == current_user.id) | (SwapRequest.receiver_id == current_user.id))
        .order_by(Session.scheduled_at)
    )
    return result.scalars().all()


@session_router.put("/{session_id}/complete", status_code=200, response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    swap_result = await db.execute(select(SwapRequest).where(SwapRequest.id == session.swap_request_id))
    swap_request = swap_result.scalar_one_or_none()
    if current_user.id not in (swap_request.sender_id, swap_request.receiver_id):
        raise HTTPException(status_code=403, detail="Not a participant in this session")
    if session.status != SessionStatus.scheduled:
        raise HTTPException(status_code=400, detail="Session is not in a scheduled state")

    session.status = SessionStatus.completed
    await db.commit()
    await db.refresh(session)
    return session


@session_router.put("/{session_id}/cancel", status_code=200, response_model=SessionResponse)
async def cancel_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    swap_result = await db.execute(select(SwapRequest).where(SwapRequest.id == session.swap_request_id))
    swap_request = swap_result.scalar_one_or_none()
    if current_user.id not in (swap_request.sender_id, swap_request.receiver_id):
        raise HTTPException(status_code=403, detail="Not a participant in this session")
    if session.status != SessionStatus.scheduled:
        raise HTTPException(status_code=400, detail="Session is not in a scheduled state")

    session.status = SessionStatus.cancelled
    await db.commit()
    await db.refresh(session)
    return session