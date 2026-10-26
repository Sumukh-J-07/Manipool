from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceTokenRegisterRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=255)
    platform: str = Field("android", description="'android' or 'ios'")


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    message: str
    event_type: str
    payload_json: Optional[str] = None
    is_read: bool
    created_at: datetime
