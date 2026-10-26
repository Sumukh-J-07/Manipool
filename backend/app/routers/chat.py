from datetime import datetime
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import AsyncSessionLocal, get_db
from backend.app.models.chat_message import ChatMessage
from backend.app.models.group_member import GroupMember
from backend.app.models.user import User
from backend.app.schemas.chat import ChatMessageCreate, ChatMessageResponse
from backend.app.services.auth_service import (
    decode_access_token,
    get_current_user,
)
from backend.app.services.chat_service import (
    get_group_messages,
    save_chat_message,
    ws_manager,
)

router = APIRouter(tags=["Group Chat"])


@router.get(
    "/groups/{group_id}/messages",
    response_model=List[ChatMessageResponse],
)
async def list_messages(
    group_id: str,
    since: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify user is a group member or reviewer
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
    )
    mem_res = await db.execute(mem_stmt)
    is_member = mem_res.scalars().first()

    if not is_member and current_user.role not in ("reviewer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view messages in this group.",
        )

    messages = await get_group_messages(db, group_id, since=since, limit=limit)
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.post(
    "/groups/{group_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    group_id: str,
    req: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    mem_stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == current_user.id,
        GroupMember.membership_status == "ACTIVE",
    )
    mem_res = await db.execute(mem_stmt)
    member = mem_res.scalars().first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only active members of this group can send messages.",
        )

    msg = await save_chat_message(
        db=db,
        group_id=group_id,
        sender_id=current_user.id,
        sender_name=current_user.name,
        text=req.text.strip(),
        is_system=False,
    )
    return ChatMessageResponse.model_validate(msg)


@router.websocket("/ws/chat/{group_id}")
async def websocket_chat_endpoint(websocket: WebSocket, group_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = payload["sub"]

    async with AsyncSessionLocal() as db:
        u_res = await db.execute(select(User).where(User.id == user_id))
        user = u_res.scalars().first()
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        m_res = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
        member = m_res.scalars().first()
        if not member and user.role not in ("reviewer", "admin"):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws_manager.connect(group_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "").strip()
            if text:
                async with AsyncSessionLocal() as db:
                    await save_chat_message(
                        db=db,
                        group_id=group_id,
                        sender_id=user.id,
                        sender_name=user.name,
                        text=text,
                        is_system=False,
                    )
    except WebSocketDisconnect:
        ws_manager.disconnect(group_id, websocket)
    except Exception:
        ws_manager.disconnect(group_id, websocket)
