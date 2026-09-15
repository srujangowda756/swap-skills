from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from typing import List

from schema.conversations import ConversationSummary
from models.conversations import Conversation
from models.swap_requests import SwapRequest
from models.messages import Message
from models.user import User
from database import get_db
from dependencies import get_current_user

conversation_router = APIRouter(prefix="/conversations", tags=["conversations"])


@conversation_router.get("/", status_code=200, response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .join(SwapRequest, Conversation.swap_request_id == SwapRequest.id)
        .where(or_(SwapRequest.sender_id == current_user.id, SwapRequest.receiver_id == current_user.id))
        .options(
            selectinload(Conversation.swap_request).selectinload(SwapRequest.sender),
            selectinload(Conversation.swap_request).selectinload(SwapRequest.receiver),
            selectinload(Conversation.messages),
        )
    )
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        swap_request = conv.swap_request
        other_user = swap_request.receiver if swap_request.sender_id == current_user.id else swap_request.sender

        last_message = max(conv.messages, key=lambda m: m.sent_at, default=None)

        summaries.append(ConversationSummary(
            conversation_id=conv.id,
            other_user_id=other_user.id,
            other_user_name=other_user.name,
            last_message=last_message.content if last_message else None,
            last_message_at=last_message.sent_at if last_message else None,
        ))

    return summaries