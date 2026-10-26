from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.auth import UserProfile


class LocationSchema(BaseModel):
    id: str
    name: str
    area: str
    kind: str
    corridor: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class RideRequestCreate(BaseModel):
    pickup_id: str
    destination_id: str
    departure: datetime
    flexibility: int = Field(30, description="Flexibility in minutes: 0, 15, 30, or 45")


class MatchCandidateResponse(BaseModel):
    id: str
    student: UserProfile
    request_id: str
    departure: str
    flexibility: int
    destination_id: str
    corridor: str
    pickup_km: float
    detour_minutes: int
    route_overlap: float
    reliability: float
    score: float


class RideRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    pickup_id: str
    pickup_name: str
    pickup_area: str
    destination_id: str
    destination_name: str
    destination_area: str
    destination_corridor: str
    departure: datetime
    flexibility: int
    status: str
    group_id: Optional[str] = None
    matches: List[MatchCandidateResponse] = []
    created_at: datetime
    updated_at: datetime


class RideRematchRequest(BaseModel):
    flexibility: Optional[int] = None
