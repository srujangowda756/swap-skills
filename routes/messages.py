from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from schema.messages import MessageCreate, MessageResponse
from models.messages import Message
from models.conversations import Conversation
from models.swap_requests import SwapRequest
from models.user import User
from database import get_db
from dependencies import get_current_user

message_router = APIRouter(prefix="/messages", tags=["messages"])


async def _get_conversation_or_403(conversation_id: UUID, current_user: User, db: AsyncSession) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .join(SwapRequest, Conversation.swap_request_id == SwapRequest.id)
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    swap_result = await db.execute(select(SwapRequest).where(SwapRequest.id == conversation.swap_request_id))
    swap_request = swap_result.scalar_one_or_none()
    if current_user.id not in (swap_request.sender_id, swap_request.receiver_id):
        raise HTTPException(status_code=403, detail="Not a participant in this conversation")

    return conversation


@message_router.post("/", status_code=201, response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_conversation_or_403(data.conversation_id, current_user, db)

    new_message = Message(
        conversation_id=data.conversation_id,
        sender_id=current_user.id,
        content=data.content,
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message


@message_router.get("/{conversation_id}", status_code=200, response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_conversation_or_403(conversation_id, current_user, db)

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at)
    )
    return result.scalars().all()