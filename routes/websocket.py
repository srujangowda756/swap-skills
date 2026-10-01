from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select
from uuid import UUID
from jose import JWTError

from websocket_manager import manager
from database import SessionLocal
from models.messages import Message
from models.conversations import Conversation
from models.swap_requests import SwapRequest
from models.notifications import Notification
from models.user import User
from utility import decode_access_token

ws_router = APIRouter()

@ws_router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: UUID, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except JWTError:
        await websocket.close(code=1008)
        return

    async with SessionLocal() as db:
        conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            await websocket.close(code=1008)
            return

        swap_result = await db.execute(select(SwapRequest).where(SwapRequest.id == conversation.swap_request_id))
        swap_request = swap_result.scalar_one_or_none()
        if user_id not in (str(swap_request.sender_id), str(swap_request.receiver_id)):
            await websocket.close(code=1008)
            return

        current_user_result = await db.execute(select(User).where(User.id == user_id))
        current_user = current_user_result.scalar_one_or_none()

        await manager.connect(conversation_id, user_id, websocket)
        try:
            await websocket.send_json({
                "type": "presence_snapshot",
                "online_user_ids": [
                    connected_user_id
                    for connected_user_id in manager.connected_user_ids(conversation_id)
                    if connected_user_id != user_id
                ],
            })
            await manager.broadcast(conversation_id, {
                "type": "presence",
                "user_id": user_id,
                "online": True,
            })
            while True:
                data = await websocket.receive_json()
                new_message = Message(
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    content=data["content"],
                )
                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)

                await manager.broadcast(conversation_id, {
                    "id": str(new_message.id),
                    "conversation_id": str(conversation_id),
                    "sender_id": str(new_message.sender_id),
                    "content": new_message.content,
                    "sent_at": new_message.sent_at.isoformat(),
                })

                other_user_id = (
                    str(swap_request.receiver_id)
                    if user_id == str(swap_request.sender_id)
                    else str(swap_request.sender_id)
                )

                recipient_connected = manager.is_user_connected(conversation_id, other_user_id)

                if not recipient_connected:
                    notification = Notification(
                        user_id=other_user_id,
                        type="new_message",
                        reference_id=new_message.id,
                        message=f"New message from {current_user.name}",
                    )
                    db.add(notification)
                    await db.commit()
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(conversation_id, websocket)
            if not manager.is_user_connected(conversation_id, user_id):
                await manager.broadcast(conversation_id, {
                    "type": "presence",
                    "user_id": user_id,
                    "online": False,
                })
