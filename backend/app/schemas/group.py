from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CreateGroupRequest(BaseModel):
    candidate_request_ids: List[str] = Field(..., min_length=1)
    pickup_mode: str = Field("common", description="'common' or 'sequential'")
    vehicle_type: str = Field("cab", description="'cab' or 'auto'")


class GroupMemberDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    email: str
    area: str
    acceptance_status: str  # PENDING | ACCEPTED | DECLINED
    membership_status: str  # ACTIVE | LEFT | CANCELLED
    fare_share_paise: int
    joined_at: datetime
    accepted_at: Optional[datetime] = None


class GroupDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    pickup_mode: str
    meeting_point_id: str
    meeting_point_name: str
    departure_time: datetime
    destination_id: str
    destination_name: str
    vehicle_type: str
    vehicle_capacity: int
    total_fare_paise: int
    booked_by_user_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    members: List[GroupMemberDetail] = []
    created_at: datetime


class UpdatePickupModeRequest(BaseModel):
    mode: str = Field(..., description="'common' or 'sequential'")
    meeting_point_id: Optional[str] = None
    meeting_point_name: Optional[str] = None


class BookRideRequest(BaseModel):
    vehicle_type: str = Field("cab", description="'cab' or 'auto'")
    fare_paise: Optional[int] = None


class DelayDepartureRequest(BaseModel):
    minutes: int = Field(10, ge=1, le=60)


class LeaveGroupRequest(BaseModel):
    reason: Optional[str] = "Student left group"
