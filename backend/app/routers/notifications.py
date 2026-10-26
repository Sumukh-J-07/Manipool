from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models.notification import DeviceToken, Notification
from backend.app.models.user import User
from backend.app.schemas.notification import (
    DeviceTokenRegisterRequest,
    NotificationResponse,
)
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationResponse])
async def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.post("/register-device")
async def register_device(
    req: DeviceTokenRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DeviceToken).where(DeviceToken.token == req.token)
    res = await db.execute(stmt)
    existing = res.scalars().first()

    if existing:
        existing.user_id = current_user.id
        existing.platform = req.platform
    else:
        new_token = DeviceToken(
            user_id=current_user.id,
            token=req.token,
            platform=req.platform,
        )
        db.add(new_token)

    await db.commit()
    return {"message": "Device token registered successfully."}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    )
    res = await db.execute(stmt)
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    notif.is_read = True
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse.model_validate(notif)
