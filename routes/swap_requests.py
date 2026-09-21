from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID
from typing import List
from datetime import datetime, timezone
from models.conversations import Conversation
from schema.swap_requests import SwapRequestCreate, SwapRequestResponse
from models.swap_requests import SwapRequest, RequestStatus
from models.user import User
from database import get_db
from dependencies import get_current_user
from models.notifications import Notification


swap_request_router = APIRouter(prefix="/swap-requests", tags=["swap-requests"])

@swap_request_router.post("/", status_code=201, response_model=SwapRequestResponse)
async def send_request(
    data: SwapRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send a request to yourself")

    new_request = SwapRequest(sender_id=current_user.id, receiver_id=data.receiver_id)
    db.add(new_request)
    
    notification = Notification(user_id=data.receiver_id,type="request_received",reference_id=new_request.id,message=f"{current_user.name} sent you a swap request",)
    db.add(notification)
    try:
        await db.commit()
        await db.refresh(new_request)
        return new_request
    except IntegrityError as e:
        await db.rollback()
        if "uq_pending_sender_receiver" in str(e.orig):
            raise HTTPException(status_code=400, detail="You already have a pending request to this user")
        raise HTTPException(status_code=400, detail="Invalid receiver_id")


@swap_request_router.get("/received", status_code=200, response_model=List[SwapRequestResponse])
async def list_received(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SwapRequest).where(SwapRequest.receiver_id == current_user.id)
    )
    return result.scalars().all()


@swap_request_router.get("/sent", status_code=200, response_model=List[SwapRequestResponse])
async def list_sent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SwapRequest).where(SwapRequest.sender_id == current_user.id)
    )
    return result.scalars().all()


@swap_request_router.put("/{request_id}/accept", status_code=200, response_model=SwapRequestResponse)
async def accept_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SwapRequest).where(SwapRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this request")
    if req.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already responded to")

    req.status = RequestStatus.accepted
    req.responded_at = datetime.now(timezone.utc)

    new_conversation = Conversation(swap_request_id=req.id)
    db.add(new_conversation)
    notification = Notification(user_id=req.sender_id,type="request_accepted",reference_id=req.id,message=f"{current_user.name} accepted your swap request",)
    db.add(notification)
    await db.commit()
    await db.refresh(req)
    return req


@swap_request_router.put("/{request_id}/reject", status_code=200, response_model=SwapRequestResponse)
async def reject_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SwapRequest).where(SwapRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this request")
    if req.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="Request already responded to")

    req.status = RequestStatus.rejected
    req.responded_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(req)
    return req
