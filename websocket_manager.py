from fastapi import WebSocket
from typing import Dict, List, Tuple
from uuid import UUID

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[UUID, List[Tuple[str, WebSocket]]] = {}

    async def connect(self, conversation_id: UUID, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(conversation_id, []).append((user_id, websocket))

    def disconnect(self, conversation_id: UUID, websocket: WebSocket):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id] = [
                (uid, ws) for uid, ws in self.active_connections[conversation_id] if ws != websocket
            ]
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    def is_user_connected(self, conversation_id: UUID, user_id: str) -> bool:
        return any(uid == user_id for uid, _ in self.active_connections.get(conversation_id, []))

    def connected_user_ids(self, conversation_id: UUID) -> List[str]:
        return list(dict.fromkeys(uid for uid, _ in self.active_connections.get(conversation_id, [])))

    async def broadcast(self, conversation_id: UUID, message: dict):
        for _, connection in self.active_connections.get(conversation_id, []):
            await connection.send_json(message)

manager = ConnectionManager()
