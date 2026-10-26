from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChatMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    group_id: str
    sender_id: str
    sender_name: str
    text: str
    is_system: bool
    created_at: datetime
