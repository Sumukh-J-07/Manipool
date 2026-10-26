import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.group_member import GroupMember
from backend.app.models.notification import DeviceToken, Notification

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    message: str,
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Notification:
    payload_str = json.dumps(payload) if payload else None
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        event_type=event_type,
        payload_json=payload_str,
        is_read=False,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Deliver to registered push tokens if present
    stmt = select(DeviceToken).where(DeviceToken.user_id == user_id)
    res = await db.execute(stmt)
    tokens = res.scalars().all()
    for tok in tokens:
        logger.info(
            f"[PUSH DISPATCH] To User {user_id} ({tok.platform}): {title} - {message}"
        )

    return notif


async def notify_group_members(
    db: AsyncSession,
    group_id: str,
    title: str,
    message: str,
    event_type: str,
    exclude_user_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> List[Notification]:
    stmt = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.membership_status == "ACTIVE",
    )
    if exclude_user_id:
        stmt = stmt.where(GroupMember.user_id != exclude_user_id)

    res = await db.execute(stmt)
    members = res.scalars().all()

    notifications: List[Notification] = []
    for member in members:
        n = await create_notification(
            db=db,
            user_id=member.user_id,
            title=title,
            message=message,
            event_type=event_type,
            payload=payload,
        )
        notifications.append(n)

    return notifications
