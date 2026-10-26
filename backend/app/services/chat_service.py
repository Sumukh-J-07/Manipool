import logging
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chat_message import ChatMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # group_id -> list of WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, group_id: str, websocket: WebSocket):
        await websocket.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = []
        self.active_connections[group_id].append(websocket)
        logger.info(f"WebSocket connected for group {group_id}")

    def disconnect(self, group_id: str, websocket: WebSocket):
        if group_id in self.active_connections:
            if websocket in self.active_connections[group_id]:
                self.active_connections[group_id].remove(websocket)
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
        logger.info(f"WebSocket disconnected for group {group_id}")

    async def broadcast(self, group_id: str, message: dict):
        if group_id in self.active_connections:
            for connection in self.active_connections[group_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error broadcasting message to connection: {e}")


ws_manager = ConnectionManager()


async def save_chat_message(
    db: AsyncSession,
    group_id: str,
    sender_id: str,
    sender_name: str,
    text: str,
    is_system: bool = False,
) -> ChatMessage:
    msg = ChatMessage(
        group_id=group_id,
        sender_id=sender_id,
        sender_name=sender_name,
        text=text,
        is_system=is_system,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Broadcast via WebSockets
    payload = {
        "id": msg.id,
        "group_id": msg.group_id,
        "sender_id": msg.sender_id,
        "sender_name": msg.sender_name,
        "text": msg.text,
        "is_system": msg.is_system,
        "created_at": msg.created_at.isoformat(),
    }
    await ws_manager.broadcast(group_id, payload)
    return msg


async def get_group_messages(
    db: AsyncSession,
    group_id: str,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> List[ChatMessage]:
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.group_id == group_id)
        .order_by(ChatMessage.created_at.asc())
    )
    if since:
        stmt = stmt.where(ChatMessage.created_at > since)
    stmt = stmt.limit(limit)

    res = await db.execute(stmt)
    return res.scalars().all()
